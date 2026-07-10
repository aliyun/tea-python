import base64
import hashlib
import os
import ssl
import threading
import time
from datetime import datetime
from enum import IntEnum
from typing import Any, Callable, Dict, List, Optional, Union
from urllib.parse import parse_qs, urlencode, urlparse

import websocket
from websocket._abnf import ABNF

from darabonba.request import DaraRequest
from darabonba.response import DaraResponse
from darabonba.runtime import RuntimeOptions


class WebSocketMessageType(IntEnum):
    Text = 0
    Binary = 1
    Ping = 2
    Pong = 3
    Close = 4


class WebSocketMessage:
    def __init__(
        self,
        type: WebSocketMessageType,
        payload: bytes,
        headers: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.type = type
        self.payload = payload
        self.headers = headers or {}
        self.timestamp = timestamp or datetime.now()


class WebSocketSessionInfo:
    def __init__(
        self,
        session_id: str,
        request_id: str = '',
        connected_at: Optional[datetime] = None,
        remote_addr: str = '',
        local_addr: str = '',
        attributes: Optional[Dict[str, Any]] = None,
    ):
        self.session_id = session_id
        self.request_id = request_id
        self.connected_at = connected_at or datetime.now()
        self.remote_addr = remote_addr
        self.local_addr = local_addr
        self.attributes = attributes or {}


STATE_DISCONNECTED = 0
STATE_CONNECTING = 1
STATE_CONNECTED = 2
STATE_DISCONNECTING = 3


def _get_runtime_value(runtime: Any, camel_key: str, snake_key: str = None):
    if runtime is None:
        return None
    if isinstance(runtime, dict):
        return runtime.get(camel_key)
    key = snake_key or camel_key
    return getattr(runtime, key, None)


def get_web_socket_ping_interval(runtime: Any) -> Optional[int]:
    return _get_runtime_value(runtime, 'webSocketPingInterval', 'web_socket_ping_interval')


def get_web_socket_pong_timeout(runtime: Any) -> Optional[int]:
    return _get_runtime_value(runtime, 'webSocketPongTimeout', 'web_socket_pong_timeout')


def get_web_socket_enable_reconnect(runtime: Any) -> Optional[bool]:
    return _get_runtime_value(runtime, 'webSocketEnableReconnect', 'web_socket_enable_reconnect')


def get_web_socket_reconnect_interval(runtime: Any) -> Optional[int]:
    return _get_runtime_value(runtime, 'webSocketReconnectInterval', 'web_socket_reconnect_interval')


def get_web_socket_max_reconnect_times(runtime: Any) -> Optional[int]:
    return _get_runtime_value(runtime, 'webSocketMaxReconnectTimes', 'web_socket_max_reconnect_times')


def get_web_socket_write_timeout(runtime: Any) -> Optional[int]:
    return _get_runtime_value(runtime, 'webSocketWriteTimeout', 'web_socket_write_timeout')


def get_web_socket_handshake_timeout(runtime: Any) -> Optional[int]:
    return _get_runtime_value(runtime, 'webSocketHandshakeTimeout', 'web_socket_handshake_timeout')


def get_web_socket_handler(runtime: Any):
    return _get_runtime_value(runtime, 'webSocketHandler', 'web_socket_handler')


def new_websocket_response(
    status_code: int,
    status_message: str,
    headers: Optional[Dict[str, Any]] = None,
) -> DaraResponse:
    res = DaraResponse()
    res.status_code = status_code
    res.status_message = status_message
    normalized_headers: Dict[str, str] = {}
    for key, val in (headers or {}).items():
        if val is not None:
            if isinstance(val, list):
                normalized_headers[key.lower()] = str(val[0])
            else:
                normalized_headers[key.lower()] = str(val)
    res.headers = normalized_headers
    return res


class WebSocketHandler:
    def after_connection_established(self, session: WebSocketSessionInfo) -> None:
        return None

    def handle_raw_message(self, session: WebSocketSessionInfo, message: WebSocketMessage) -> None:
        return None

    def handle_error(self, session: WebSocketSessionInfo, err: Exception) -> None:
        return None

    def after_connection_closed(self, session: WebSocketSessionInfo, code: int, reason: str) -> None:
        return None


class AbstractWebSocketHandler(WebSocketHandler):
    pass


class DefaultWebSocketClient:
    def __init__(self, handler: WebSocketHandler):
        if handler is None:
            raise ValueError('handler cannot be nil')
        self.handler = handler
        self.stopped = False
        self.pong_received = False
        self.state = STATE_DISCONNECTED
        self.ws_app: Optional[websocket.WebSocketApp] = None
        self.session: Optional[WebSocketSessionInfo] = None
        self.request: Optional[DaraRequest] = None
        self.runtime_object: Any = None
        self.reconnect_count = 0
        self._ping_timer: Optional[threading.Timer] = None
        self.ping_interval = 30000
        self.reconnect_interval = 5000
        self.write_timeout = 30000
        self.read_timeout = 0
        self.pong_timeout = 5000
        self.max_reconnect_times = 5
        self._reconnect_lock = threading.Lock()
        self._abort_event = threading.Event()
        self._ws_thread: Optional[threading.Thread] = None
        self._message_handlers_started = False
        self._connect_error: Optional[Exception] = None
        self._handshake_response: Dict[str, Any] = {}

    def connect(self, request: DaraRequest, runtime_object: Any) -> DaraResponse:
        if request is None:
            raise ValueError('request cannot be nil')
        if runtime_object is None:
            raise ValueError('runtimeObject cannot be nil')

        self.request = request
        self.runtime_object = runtime_object
        self._update_timeout_config(runtime_object)
        self.state = STATE_CONNECTING
        self.stopped = False
        self.pong_received = False
        self._connect_error = None
        self._handshake_response = {}
        self._abort_event.clear()

        request_url = build_websocket_url(request)
        parsed = urlparse(request_url)
        if not parsed.scheme or not parsed.netloc:
            self.state = STATE_DISCONNECTED
            raise ValueError(f'invalid websocket url: {request_url}')

        handshake_timeout = get_web_socket_handshake_timeout(runtime_object)
        if not handshake_timeout or handshake_timeout <= 0:
            handshake_timeout = 30000

        connect_timeout = _get_connect_timeout(runtime_object)

        headers: Dict[str, str] = {}
        if request.headers:
            for key, value in request.headers.items():
                if value and key.lower() not in ('host', 'content-length'):
                    headers[key] = value

        sslopt = self._configure_tls(runtime_object, parsed.scheme)
        proxy_kwargs = self._configure_proxy(parsed, runtime_object, request)

        connected_event = threading.Event()

        def on_open(ws_app):
            self.ws_app = ws_app
            self.state = STATE_CONNECTED
            self._setup_pong_handler()
            self._start_message_handlers(ws_app)
            if self.ping_interval > 0:
                self._start_ping_pong()

            resp_headers: Dict[str, Any] = {}
            status_code = 101
            status_message = 'Switching Protocols'
            if ws_app.sock is not None:
                if hasattr(ws_app.sock, 'headers') and ws_app.sock.headers:
                    resp_headers = dict(ws_app.sock.headers)
                if hasattr(ws_app.sock, 'status') and ws_app.sock.status:
                    status_code = ws_app.sock.status
                if hasattr(ws_app.sock, 'status_message') and ws_app.sock.status_message:
                    status_message = ws_app.sock.status_message

            session_id = (
                resp_headers.get('x-acs-ws-session-id')
                or resp_headers.get('X-Acs-Ws-Session-Id')
                or _generate_session_id()
            )
            request_id = (
                resp_headers.get('x-acs-request-id')
                or resp_headers.get('X-Acs-Request-Id')
                or ''
            )
            if isinstance(session_id, list):
                session_id = session_id[0]
            if isinstance(request_id, list):
                request_id = request_id[0]

            self.session = WebSocketSessionInfo(
                session_id=str(session_id),
                request_id=str(request_id),
                connected_at=datetime.now(),
                remote_addr=request_url,
                local_addr='',
                attributes={},
            )

            try:
                self.handler.after_connection_established(self.session)
            except Exception as err:
                self._connect_error = err
                self.state = STATE_DISCONNECTED
                self.stopped = True
                try:
                    ws_app.close()
                except Exception:
                    pass
                connected_event.set()
                return

            self._handshake_response = {
                'status_code': status_code,
                'status_message': status_message,
                'headers': resp_headers,
            }
            connected_event.set()

        def on_error(ws_app, error):
            if self.state == STATE_CONNECTING:
                self._connect_error = error if isinstance(error, Exception) else Exception(str(error))
                connected_event.set()

        self.ws_app = websocket.WebSocketApp(
            request_url,
            header=headers,
            on_open=on_open,
            on_message=self._on_message,
            on_error=on_error,
            on_close=self._on_close,
            on_pong=self._on_pong,
        )

        run_kwargs = {
            'sslopt': sslopt,
            'ping_interval': 0,
            'ping_timeout': None,
        }
        run_kwargs.update(proxy_kwargs)

        self._ws_thread = threading.Thread(
            target=self.ws_app.run_forever,
            kwargs=run_kwargs,
            daemon=True,
        )
        self._ws_thread.start()

        timeout_seconds = max(connect_timeout, handshake_timeout) / 1000
        if not connected_event.wait(timeout=timeout_seconds):
            self.state = STATE_DISCONNECTED
            self._cleanup_connection()
            raise TimeoutError('WebSocket connection timeout')

        if self._connect_error is not None:
            self._cleanup_connection()
            raise self._connect_error

        return new_websocket_response(
            self._handshake_response.get('status_code', 101),
            self._handshake_response.get('status_message', 'Switching Protocols'),
            self._handshake_response.get('headers', {}),
        )

    def disconnect(self) -> None:
        self._disconnect_internal(1000, 'Normal closure')

    def _disconnect_internal(self, code: int, reason: str) -> None:
        if self.state == STATE_DISCONNECTED and not self._ws_thread:
            return

        self.state = STATE_DISCONNECTING
        self._stop_ping_pong()
        self.stopped = True

        ws_app = self.ws_app
        self.ws_app = None
        if ws_app is not None:
            try:
                ws_app.close(status=code, reason=reason)
            except Exception:
                pass

        self._wait_for_close()

        if self.session:
            try:
                self.handler.after_connection_closed(self.session, code, reason)
            except Exception:
                pass

        self.state = STATE_DISCONNECTED
        self._abort_event.set()

    def reconnect(self) -> DaraResponse:
        return self._reconnect_internal(False)

    def reconnect_gracefully(self) -> DaraResponse:
        return self._reconnect_internal(True)

    def _reconnect_internal(self, graceful: bool) -> DaraResponse:
        if not graceful and self.is_connected():
            raise Exception('already connected')

        if self._abort_event.is_set():
            raise Exception('connection aborted')

        if not self._reconnect_lock.acquire(blocking=False):
            raise Exception('reconnect already in progress')

        try:
            if not get_web_socket_enable_reconnect(self.runtime_object):
                raise Exception('reconnect is disabled')

            if self.reconnect_count >= self.max_reconnect_times:
                raise Exception(f'max reconnect times reached: {self.max_reconnect_times}')

            previous_session_id = ''
            if graceful:
                if self.session and self.session.session_id:
                    previous_session_id = self.session.session_id
                else:
                    raise Exception('graceful reconnection requires existing session ID')

            self._cleanup_resources()

            self.stopped = False
            self.reconnect_count += 1

            if self.request is None:
                raise Exception('request is nil, cannot reconnect')

            if graceful and previous_session_id:
                if self.request.headers is None:
                    self.request.headers = {}
                self.request.headers['X-Acs-Ws-Session-Id'] = previous_session_id
            elif self.request.headers:
                self.request.headers.pop('X-Acs-Ws-Session-Id', None)

            self._sleep_interruptible(self.reconnect_interval)

            if self._abort_event.is_set():
                raise Exception('connection aborted')

            result = self.connect(self.request, self.runtime_object)
            self.reconnect_count = 0
            return result
        finally:
            self._reconnect_lock.release()

    def _cleanup_resources(self) -> None:
        self.state = STATE_DISCONNECTING
        self._stop_ping_pong()
        self.stopped = True

        ws_app = self.ws_app
        self.ws_app = None
        if ws_app is not None:
            try:
                ws_app.close(status=1001, reason='Reconnecting')
            except Exception:
                pass
            self._wait_for_close()

        self.session = None
        self._message_handlers_started = False
        self.state = STATE_DISCONNECTED

    def is_connected(self) -> bool:
        return self.state == STATE_CONNECTED

    def send_text(self, text: str) -> None:
        if not self.is_connected():
            raise Exception('not connected')
        ws_app = self.ws_app
        if ws_app is None:
            raise Exception('connection is nil')
        self._send_with_timeout(lambda: ws_app.send(text))

    def send_binary(self, data: bytes) -> None:
        if not self.is_connected():
            raise Exception('not connected')
        ws_app = self.ws_app
        if ws_app is None:
            raise Exception('connection is nil')
        self._send_with_timeout(lambda: ws_app.send(data, opcode=ABNF.OPCODE_BINARY))

    def get_session_info(self) -> Optional[WebSocketSessionInfo]:
        return self.session

    def close(self) -> None:
        self._disconnect_internal(1000, 'Client closed')

    def configure_tls(self, runtime_object: Any, scheme: str = 'wss') -> Dict[str, Any]:
        return self._configure_tls(runtime_object, scheme)

    def configure_proxy(
        self,
        parsed: Any,
        runtime_object: Any,
        request: DaraRequest,
    ) -> Dict[str, Any]:
        return self._configure_proxy(parsed, runtime_object, request)

    def configure_socks5_proxy(self, runtime_object: Any) -> Dict[str, Any]:
        proxy_kwargs: Dict[str, Any] = {}
        socks5_proxy = _get_runtime_value(runtime_object, 'socks5Proxy', 'socks_5proxy')
        if socks5_proxy:
            proxy_kwargs['proxy_type'] = 'socks5'
            proxy_kwargs['http_proxy_host'] = socks5_proxy
        return proxy_kwargs

    def configure_http_proxy(
        self,
        parsed: Any,
        runtime_object: Any,
        request: DaraRequest,
    ) -> Dict[str, Any]:
        return self._configure_proxy(parsed, runtime_object, request)

    def _configure_tls(self, runtime_object: Any, scheme: str) -> Dict[str, Any]:
        if scheme not in ('wss', 'https'):
            return {}

        ignore_ssl = _get_runtime_value(runtime_object, 'ignoreSSL', 'ignore_ssl')
        sslopt: Dict[str, Any] = {}
        if ignore_ssl:
            sslopt['cert_reqs'] = ssl.CERT_NONE
            sslopt['check_hostname'] = False
        else:
            sslopt['cert_reqs'] = ssl.CERT_REQUIRED

        cert = _get_runtime_value(runtime_object, 'cert', 'cert')
        key = _get_runtime_value(runtime_object, 'key', 'key')
        ca = _get_runtime_value(runtime_object, 'ca', 'ca')
        if cert and key:
            sslopt['certfile'] = cert
            sslopt['keyfile'] = key
        if ca:
            sslopt['ca_certs'] = ca
        return sslopt

    def _configure_proxy(
        self,
        parsed: Any,
        runtime_object: Any,
        request: DaraRequest,
    ) -> Dict[str, Any]:
        proxy_kwargs: Dict[str, Any] = {}
        socks5_proxy = _get_runtime_value(runtime_object, 'socks5Proxy', 'socks_5proxy')
        if socks5_proxy:
            proxy_kwargs['proxy_type'] = 'socks5'
            proxy_kwargs['http_proxy_host'] = socks5_proxy
            return proxy_kwargs

        if parsed is None:
            return proxy_kwargs

        protocol = parsed.scheme.replace(':', '')
        host = parsed.hostname
        no_proxy_list = _get_no_proxy(protocol, runtime_object)
        for no_proxy_host in no_proxy_list:
            if no_proxy_host.strip() == host:
                return proxy_kwargs

        proxy_url = _get_http_proxy_url(protocol, host, runtime_object)
        if not proxy_url:
            return proxy_kwargs

        proxy_parsed = urlparse(proxy_url)
        proxy_kwargs['http_proxy_host'] = proxy_parsed.hostname
        proxy_kwargs['http_proxy_port'] = proxy_parsed.port or (
            443 if protocol in ('wss', 'https') else 80
        )
        if proxy_parsed.username and proxy_parsed.password:
            if request.headers is None:
                request.headers = {}
            auth = f'{proxy_parsed.username}:{proxy_parsed.password}'
            request.headers['Proxy-Authorization'] = (
                'Basic ' + base64.b64encode(auth.encode()).decode()
            )
        return proxy_kwargs

    def _update_timeout_config(self, runtime_object: Any) -> None:
        ping_interval = get_web_socket_ping_interval(runtime_object)
        self.ping_interval = ping_interval if ping_interval and ping_interval > 0 else 30000

        reconnect_interval = get_web_socket_reconnect_interval(runtime_object)
        self.reconnect_interval = reconnect_interval if reconnect_interval and reconnect_interval > 0 else 5000

        write_timeout = get_web_socket_write_timeout(runtime_object)
        self.write_timeout = write_timeout if write_timeout and write_timeout > 0 else 30000

        read_timeout = _get_runtime_value(runtime_object, 'readTimeout', 'read_timeout')
        self.read_timeout = read_timeout if read_timeout and read_timeout > 0 else 0

        pong_timeout = get_web_socket_pong_timeout(runtime_object)
        self.pong_timeout = pong_timeout if pong_timeout and pong_timeout > 0 else 5000

        max_reconnect_times = get_web_socket_max_reconnect_times(runtime_object)
        self.max_reconnect_times = max_reconnect_times if max_reconnect_times and max_reconnect_times > 0 else 5

    def _setup_pong_handler(self) -> None:
        self.pong_received = False

    def _on_pong(self, ws_app, _data) -> None:
        self.pong_received = True

    def _start_message_handlers(self, ws_app) -> None:
        if self._message_handlers_started:
            return
        self._message_handlers_started = True
        self.ws_app = ws_app

    def _on_message(self, ws_app, message) -> None:
        if self.stopped:
            return

        if isinstance(message, bytes):
            msg_type = WebSocketMessageType.Binary
            payload = message
        else:
            msg_type = WebSocketMessageType.Text
            payload = message.encode('utf-8') if isinstance(message, str) else bytes(message)

        msg = WebSocketMessage(type=msg_type, payload=payload, headers={}, timestamp=datetime.now())
        if not self.session:
            return

        try:
            self.handler.handle_raw_message(self.session, msg)
        except Exception as err:
            try:
                self.handler.handle_error(self.session, err)
            except Exception:
                pass

    def _on_error(self, ws_app, error) -> None:
        if self.stopped or not self.session:
            return
        err = error if isinstance(error, Exception) else Exception(str(error))
        try:
            self.handler.handle_error(self.session, err)
        except Exception:
            pass

    def _on_close(self, ws_app, close_status_code, close_msg) -> None:
        if self.stopped:
            return

        reason = close_msg or ''
        if self.session and close_status_code not in (1000, 1001):
            try:
                self.handler.handle_error(
                    self.session,
                    Exception(f'WebSocket closed: {close_status_code} {reason}'),
                )
            except Exception:
                pass

        if get_web_socket_enable_reconnect(self.runtime_object) and self.request and not self.stopped:
            try:
                self.reconnect()
            except Exception:
                pass

    def _start_ping_pong(self) -> None:
        if self.ping_interval <= 0:
            return
        self._stop_ping_pong()
        self._schedule_ping()

    def _schedule_ping(self) -> None:
        if self.stopped or not self.is_connected():
            return

        self.pong_received = False
        try:
            if self.ws_app and self.ws_app.sock:
                self.ws_app.sock.ping()
        except Exception as err:
            if self.session:
                try:
                    self.handler.handle_error(self.session, err)
                except Exception:
                    pass
            return

        def check_pong():
            if self.stopped:
                return
            if not self.pong_received and get_web_socket_enable_reconnect(self.runtime_object):
                try:
                    self.reconnect()
                except Exception:
                    pass
            if not self.stopped and self.is_connected():
                self._schedule_ping()

        self._ping_timer = threading.Timer(self.pong_timeout / 1000, check_pong)
        self._ping_timer.daemon = True
        self._ping_timer.start()

    def _stop_ping_pong(self) -> None:
        if self._ping_timer is not None:
            self._ping_timer.cancel()
            self._ping_timer = None

    def _cleanup_connection(self) -> None:
        self._stop_ping_pong()
        self.stopped = True
        ws_app = self.ws_app
        self.ws_app = None
        if ws_app is not None:
            try:
                ws_app.close()
            except Exception:
                pass
            self._wait_for_close()

    def _send_with_timeout(self, send_fn: Callable[[], None]) -> None:
        if self.write_timeout <= 0:
            send_fn()
            return

        error: List[Optional[Exception]] = [None]

        def do_send():
            try:
                send_fn()
            except Exception as err:
                error[0] = err

        thread = threading.Thread(target=do_send, daemon=True)
        thread.start()
        thread.join(timeout=self.write_timeout / 1000)
        if thread.is_alive():
            raise TimeoutError('write timeout')
        if error[0] is not None:
            raise error[0]

    def _wait_for_close(self, timeout: float = 5.0) -> None:
        thread = self._ws_thread
        if thread is None:
            return
        if thread is threading.current_thread():
            return
        thread.join(timeout=timeout)

    def _sleep_interruptible(self, ms: int) -> bool:
        return self._abort_event.wait(timeout=ms / 1000)


def new_default_websocket_client(handler: WebSocketHandler) -> DefaultWebSocketClient:
    return DefaultWebSocketClient(handler)


def new_websocket_client_and_connect(
    request: DaraRequest,
    runtime_object: Any,
):
    if runtime_object is None:
        raise ValueError('runtimeObject cannot be nil')

    handler = get_web_socket_handler(runtime_object)
    if handler is None:
        raise ValueError(
            'WebSocketHandler is required: please set it in runtimeObject.webSocketHandler'
        )

    client = DefaultWebSocketClient(handler)
    response = client.connect(request, runtime_object)
    return client, response


def build_websocket_url(request: DaraRequest) -> str:
    if request is None:
        raise ValueError('request cannot be nil')

    protocol = request.protocol or 'ws'
    protocol = protocol.lower()
    if protocol == 'http':
        protocol = 'ws'
    elif protocol == 'https':
        protocol = 'wss'

    domain = getattr(request, 'domain', None)
    if not domain and request.headers:
        domain = request.headers.get('host')
    if not domain:
        raise ValueError('domain is required (set in request.headers["host"] or request.domain)')

    request_url = f'{protocol}://{domain}'
    request_url += request.pathname or '/'

    if request.query:
        qs = urlencode(request.query, doseq=True)
        if qs:
            request_url += '&' + qs if '?' in request_url else '?' + qs

    return request_url


def convert_to_websocket_message_type(message_type: int) -> WebSocketMessageType:
    mapping = {
        1: WebSocketMessageType.Text,
        2: WebSocketMessageType.Binary,
        9: WebSocketMessageType.Ping,
        10: WebSocketMessageType.Pong,
        8: WebSocketMessageType.Close,
    }
    return mapping.get(message_type, WebSocketMessageType.Binary)


def _generate_session_id() -> str:
    return f'ws-session-{int(time.time() * 1000)}{os.urandom(4).hex()}'


def _get_connect_timeout(runtime_object: Any) -> int:
    connect_timeout = _get_runtime_value(runtime_object, 'connectTimeout', 'connect_timeout')
    if connect_timeout and connect_timeout > 0:
        return connect_timeout
    return 10000


def _get_no_proxy(protocol: str, runtime: Any) -> List[str]:
    no_proxy = _get_runtime_value(runtime, 'noProxy', 'no_proxy')
    if no_proxy:
        return no_proxy.split(',')
    env_no_proxy = os.environ.get('NO_PROXY') or os.environ.get('no_proxy')
    if env_no_proxy:
        return env_no_proxy.split(',')
    return []


def _get_http_proxy_url(protocol: str, host: str, runtime: Any) -> Optional[str]:
    no_proxy_list = _get_no_proxy(protocol, runtime)
    for no_proxy_host in no_proxy_list:
        if no_proxy_host.strip() == host:
            return None

    proxy_protocol = protocol
    if protocol == 'wss':
        proxy_protocol = 'https'
    elif protocol == 'ws':
        proxy_protocol = 'http'

    if proxy_protocol == 'https':
        proxy_url = _get_runtime_value(runtime, 'httpsProxy', 'https_proxy')
        if proxy_url:
            return proxy_url
        return os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    proxy_url = _get_runtime_value(runtime, 'httpProxy', 'http_proxy')
    if proxy_url:
        return proxy_url
    return os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')

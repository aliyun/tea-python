import hashlib
import socket
import ssl
import struct
import threading
import unittest
from base64 import b64encode
from datetime import datetime
from unittest import mock
from urllib.parse import urlparse

import websocket as ws_client

from darabonba.request import DaraRequest
from darabonba.runtime import RuntimeOptions
from darabonba.websocket import (
    AbstractWebSocketHandler,
    DefaultWebSocketClient,
    STATE_CONNECTED,
    WebSocketMessage,
    WebSocketMessageType,
    WebSocketSessionInfo,
    build_websocket_url,
    convert_to_websocket_message_type,
    new_default_websocket_client,
    new_websocket_client_and_connect,
)


WEBSOCKET_GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'


class MockWebSocketHandler(AbstractWebSocketHandler):
    def __init__(self):
        self.connected_called = False
        self.message_received_count = 0
        self.error_count = 0
        self.closed_called = False
        self.last_message = None

    def after_connection_established(self, session):
        self.connected_called = True

    def handle_raw_message(self, session, message):
        self.message_received_count += 1
        self.last_message = message

    def handle_error(self, session, err):
        self.error_count += 1

    def after_connection_closed(self, session, code, reason):
        self.closed_called = True


class ErrorOnConnectHandler(MockWebSocketHandler):
    def after_connection_established(self, session):
        raise Exception('test error on connection')


class SimpleEchoWebSocketServer:
    def __init__(self):
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(('127.0.0.1', 0))
        self.port = self._server.getsockname()[1]
        self._server.listen(5)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self):
        self._server.settimeout(0.5)
        while not self._stop.is_set():
            try:
                conn, _addr = self._server.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()

    def _handle_client(self, conn):
        try:
            request = conn.recv(4096).decode('utf-8', errors='ignore')
            key = None
            for line in request.split('\r\n'):
                if line.lower().startswith('sec-websocket-key:'):
                    key = line.split(':', 1)[1].strip()
            if not key:
                conn.close()
                return
            accept = b64encode(hashlib.sha1((key + WEBSOCKET_GUID).encode()).digest()).decode()
            response = (
                'HTTP/1.1 101 Switching Protocols\r\n'
                'Upgrade: websocket\r\n'
                'Connection: Upgrade\r\n'
                f'Sec-WebSocket-Accept: {accept}\r\n'
                'X-Acs-Ws-Session-Id: test-session-id\r\n'
                '\r\n'
            )
            conn.sendall(response.encode())

            while not self._stop.is_set():
                try:
                    header = conn.recv(2)
                    if len(header) < 2:
                        break
                    length = header[1] & 127
                    if length == 126:
                        length = struct.unpack('>H', conn.recv(2))[0]
                    elif length == 127:
                        length = struct.unpack('>Q', conn.recv(8))[0]
                    masked = header[1] & 128
                    mask = conn.recv(4) if masked else b''
                    payload = conn.recv(length)
                    if masked:
                        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
                    frame = self._encode_text_frame(payload)
                    conn.sendall(frame)
                except OSError:
                    break
        finally:
            conn.close()

    @staticmethod
    def _encode_text_frame(payload):
        length = len(payload)
        if length <= 125:
            header = struct.pack('>BB', 0x81, length)
        elif length <= 65535:
            header = struct.pack('>BBH', 0x81, 126, length)
        else:
            header = struct.pack('>BBQ', 0x81, 127, length)
        return header + payload

    def close(self):
        self._stop.set()
        try:
            self._server.close()
        except OSError:
            pass
        self._thread.join(timeout=2)


class TestWebSocket(unittest.TestCase):
    def test_create_default_websocket_client(self):
        handler = MockWebSocketHandler()
        client = new_default_websocket_client(handler)
        self.assertIsNotNone(client)
        self.assertFalse(client.is_connected())
        with self.assertRaisesRegex(ValueError, 'handler cannot be nil'):
            new_default_websocket_client(None)

    def test_websocket_message_type_values(self):
        self.assertEqual(WebSocketMessageType.Text, 0)
        self.assertEqual(WebSocketMessageType.Binary, 1)

    def test_convert_websocket_message_type(self):
        self.assertEqual(convert_to_websocket_message_type(1), WebSocketMessageType.Text)
        self.assertEqual(convert_to_websocket_message_type(2), WebSocketMessageType.Binary)
        self.assertEqual(convert_to_websocket_message_type(9), WebSocketMessageType.Ping)
        self.assertEqual(convert_to_websocket_message_type(10), WebSocketMessageType.Pong)
        self.assertEqual(convert_to_websocket_message_type(8), WebSocketMessageType.Close)
        self.assertEqual(convert_to_websocket_message_type(999), WebSocketMessageType.Binary)

    def test_mock_handler_callbacks(self):
        handler = MockWebSocketHandler()
        session = WebSocketSessionInfo(session_id='test')
        handler.after_connection_established(session)
        self.assertTrue(handler.connected_called)

        msg = WebSocketMessage(
            type=WebSocketMessageType.Text,
            payload=b'test message',
            headers={},
            timestamp=datetime.now(),
        )
        handler.handle_raw_message(session, msg)
        handler.handle_raw_message(session, msg)
        self.assertEqual(2, handler.message_received_count)
        self.assertEqual(b'test message', handler.last_message.payload)

        handler.handle_error(session, Exception('test'))
        self.assertEqual(1, handler.error_count)

        handler.after_connection_closed(session, 1000, 'Normal')
        self.assertTrue(handler.closed_called)

    def test_build_websocket_url(self):
        request = DaraRequest()
        request.protocol = 'ws'
        request.headers = {'host': 'example.com'}
        request.pathname = '/path'
        request.query = {'foo': 'bar'}
        url = build_websocket_url(request)
        self.assertEqual('ws://example.com/path?foo=bar', url)

    def test_connect_success(self):
        server = SimpleEchoWebSocketServer()
        try:
            request = DaraRequest()
            request.protocol = 'ws'
            request.domain = f'127.0.0.1:{server.port}'
            request.pathname = '/'
            request.headers = {'host': f'127.0.0.1:{server.port}'}

            runtime = RuntimeOptions(
                connect_timeout=5000,
                read_timeout=30000,
                web_socket_ping_interval=0,
                web_socket_enable_reconnect=False,
            )
            handler = MockWebSocketHandler()
            client = new_default_websocket_client(handler)
            response = client.connect(request, runtime)

            self.assertIsNotNone(response)
            self.assertTrue(client.is_connected())
            self.assertTrue(handler.connected_called)
            self.assertEqual('test-session-id', client.session.session_id)
            client.disconnect()
        finally:
            server.close()

    def test_connect_missing_domain(self):
        request = DaraRequest()
        request.protocol = 'ws'
        request.headers = {}
        runtime = RuntimeOptions(connect_timeout=5000)
        client = new_default_websocket_client(MockWebSocketHandler())
        with self.assertRaisesRegex(ValueError, 'domain is required'):
            client.connect(request, runtime)

    def test_connect_timeout(self):
        request = DaraRequest()
        request.protocol = 'ws'
        request.domain = '127.0.0.1:59999'
        request.pathname = '/'
        request.headers = {'host': '127.0.0.1:59999'}
        runtime = RuntimeOptions(
            connect_timeout=100,
            web_socket_handshake_timeout=100,
        )
        handler = MockWebSocketHandler()
        client = new_default_websocket_client(handler)
        with self.assertRaises(Exception):
            client.connect(request, runtime)
        self.assertFalse(client.is_connected())
        self.assertFalse(handler.connected_called)

    def test_handler_error_on_connect(self):
        server = SimpleEchoWebSocketServer()
        try:
            request = DaraRequest()
            request.protocol = 'ws'
            request.domain = f'127.0.0.1:{server.port}'
            request.pathname = '/'
            request.headers = {'host': f'127.0.0.1:{server.port}'}
            runtime = RuntimeOptions(
                connect_timeout=5000,
                web_socket_ping_interval=0,
            )
            client = new_default_websocket_client(ErrorOnConnectHandler())
            with self.assertRaisesRegex(Exception, 'test error on connection'):
                client.connect(request, runtime)
            client.disconnect()
        finally:
            server.close()

    def test_send_text_echo(self):
        server = SimpleEchoWebSocketServer()
        try:
            request = DaraRequest()
            request.protocol = 'ws'
            request.domain = f'127.0.0.1:{server.port}'
            request.pathname = '/'
            request.headers = {'host': f'127.0.0.1:{server.port}'}
            handler = MockWebSocketHandler()
            runtime = RuntimeOptions(
                connect_timeout=5000,
                web_socket_ping_interval=0,
                web_socket_enable_reconnect=False,
                web_socket_handler=handler,
            )
            client, _response = new_websocket_client_and_connect(request, runtime)
            client.send_text('hello')
            import time
            time.sleep(0.2)
            self.assertGreaterEqual(handler.message_received_count, 1)
            client.close()
        finally:
            server.close()

    def test_reconnect_when_already_connected(self):
        server = SimpleEchoWebSocketServer()
        try:
            request = DaraRequest()
            request.protocol = 'ws'
            request.domain = f'127.0.0.1:{server.port}'
            request.pathname = '/'
            request.headers = {'host': f'127.0.0.1:{server.port}'}
            handler = MockWebSocketHandler()
            runtime = RuntimeOptions(
                web_socket_enable_reconnect=True,
                web_socket_max_reconnect_times=3,
                web_socket_reconnect_interval=100,
                web_socket_handshake_timeout=5000,
                web_socket_ping_interval=0,
                web_socket_handler=handler,
            )
            client, _response = new_websocket_client_and_connect(request, runtime)
            self.assertTrue(client.is_connected())
            with self.assertRaisesRegex(Exception, 'already connected'):
                client.reconnect()
            client.close()
        finally:
            server.close()

    def test_connect_passes_through_websocket_protocol_header(self):
        captured = {}

        class CapturingWebSocketApp:
            def __init__(self, url, header=None, **kwargs):
                captured['header'] = header or {}
                self.sock = None

            def run_forever(self, **kwargs):
                return True

            def close(self, **kwargs):
                return None

        original = ws_client.WebSocketApp
        ws_client.WebSocketApp = CapturingWebSocketApp
        try:
            request = DaraRequest()
            request.protocol = 'ws'
            request.domain = '127.0.0.1:59999'
            request.pathname = '/'
            request.headers = {
                'host': '127.0.0.1:59999',
                'sec-websocket-protocol': 'awap',
            }
            runtime = RuntimeOptions(
                connect_timeout=50,
                web_socket_handshake_timeout=50,
                web_socket_ping_interval=0,
            )
            client = new_default_websocket_client(MockWebSocketHandler())
            with self.assertRaises(Exception):
                client.connect(request, runtime)
            self.assertEqual('awap', captured['header'].get('sec-websocket-protocol'))
            self.assertNotIn('Sec-WebSocket-Protocol', captured['header'])
        finally:
            ws_client.WebSocketApp = original

    def test_configure_tls(self):
        client = DefaultWebSocketClient(MockWebSocketHandler())
        ignore_ssl = client.configure_tls(RuntimeOptions(ignore_ssl=True), 'wss')
        self.assertEqual(ssl.CERT_NONE, ignore_ssl['cert_reqs'])
        verify_ssl = client.configure_tls(RuntimeOptions(ignore_ssl=False), 'wss')
        self.assertEqual(ssl.CERT_REQUIRED, verify_ssl['cert_reqs'])

    def test_configure_http_proxy(self):
        client = DefaultWebSocketClient(MockWebSocketHandler())
        parsed = urlparse('wss://example.com/ws')
        request = DaraRequest()
        request.headers = {}
        proxy_kwargs = client.configure_http_proxy(
            parsed,
            RuntimeOptions(https_proxy='http://proxy.example.com:8080'),
            request,
        )
        self.assertEqual('proxy.example.com', proxy_kwargs['http_proxy_host'])

        no_proxy_kwargs = client.configure_http_proxy(
            parsed,
            RuntimeOptions(https_proxy='http://proxy.example.com:8080', no_proxy='example.com'),
            request,
        )
        self.assertEqual({}, no_proxy_kwargs)

        auth_request = DaraRequest()
        auth_request.headers = {}
        auth_kwargs = client.configure_http_proxy(
            parsed,
            RuntimeOptions(https_proxy='http://user:pass@proxy.example.com:8080'),
            auth_request,
        )
        self.assertIn('Proxy-Authorization', auth_request.headers)

    def test_no_duplicate_sec_websocket_protocol_header(self):
        # Intercept WebSocketApp to capture what headers and subprotocols are passed.
        captured = {}
        original_init = __import__('websocket').WebSocketApp.__init__

        def patched_init(self_app, url, header=None, on_open=None,
                         on_message=None, on_error=None, on_close=None,
                         subprotocols=None, **kwargs):
            captured['header'] = header
            captured['subprotocols'] = subprotocols
            raise ConnectionRefusedError('captured')

        import websocket as ws_lib
        ws_lib.WebSocketApp.__init__ = patched_init
        try:
            # Simulate the real call path: openapi client pre-sets
            # 'sec-websocket-protocol' in request.headers for ACS3 signature.
            request = DaraRequest()
            request.protocol = 'ws'
            request.domain = '127.0.0.1:19999'
            request.pathname = '/'
            request.headers = {
                'host': '127.0.0.1:19999',
                'sec-websocket-protocol': 'awap',
            }

            runtime = RuntimeOptions(
                connect_timeout=5000,
                read_timeout=5000,
                web_socket_ping_interval=0,
                web_socket_enable_reconnect=False,
            )
            handler = MockWebSocketHandler()
            client = new_default_websocket_client(handler)
            try:
                client.connect(request, runtime)
            except (ConnectionRefusedError, Exception):
                pass

            header = captured.get('header', {})

            # Must have exactly 1 key matching 'sec-websocket-protocol' (case-insensitive).
            # Before fix: Python dict had both 'sec-websocket-protocol' and
            # 'Sec-WebSocket-Protocol' because dict keys are case-sensitive.
            protocol_keys = [k for k in header if k.lower() == 'sec-websocket-protocol']
            self.assertEqual(1, len(protocol_keys),
                             f'Expected 1 protocol header key, got: {protocol_keys}')

            # subprotocols must be None. If set to ['awap'], websocket-client
            # library merges it with the header into 'awap,awap' on the wire.
            self.assertIsNone(captured.get('subprotocols'))
        finally:
            ws_lib.WebSocketApp.__init__ = original_init

    def test_subprotocols_not_passed_even_without_preset_header(self):
        # Even when request.headers does NOT contain sec-websocket-protocol,
        # subprotocols param must still be None to avoid duplication.
        captured = {}
        original_init = __import__('websocket').WebSocketApp.__init__

        def patched_init(self_app, url, header=None, on_open=None,
                         on_message=None, on_error=None, on_close=None,
                         subprotocols=None, **kwargs):
            captured['header'] = header
            captured['subprotocols'] = subprotocols
            raise ConnectionRefusedError('captured')

        import websocket as ws_lib
        ws_lib.WebSocketApp.__init__ = patched_init
        try:
            request = DaraRequest()
            request.protocol = 'ws'
            request.domain = '127.0.0.1:19999'
            request.pathname = '/'
            request.headers = {'host': '127.0.0.1:19999'}

            runtime = RuntimeOptions(
                connect_timeout=5000,
                read_timeout=5000,
                web_socket_ping_interval=0,
                web_socket_enable_reconnect=False,
            )
            handler = MockWebSocketHandler()
            client = new_default_websocket_client(handler)
            try:
                client.connect(request, runtime)
            except (ConnectionRefusedError, Exception):
                pass

            # subprotocols must always be None regardless of input.
            self.assertIsNone(captured.get('subprotocols'))
        finally:
            ws_lib.WebSocketApp.__init__ = original_init

    def test_protocol_header_value_preserved_from_request(self):
        # The header value from request.headers must pass through unchanged.
        captured = {}
        original_init = __import__('websocket').WebSocketApp.__init__

        def patched_init(self_app, url, header=None, on_open=None,
                         on_message=None, on_error=None, on_close=None,
                         subprotocols=None, **kwargs):
            captured['header'] = header
            raise ConnectionRefusedError('captured')

        import websocket as ws_lib
        ws_lib.WebSocketApp.__init__ = patched_init
        try:
            request = DaraRequest()
            request.protocol = 'ws'
            request.domain = '127.0.0.1:19999'
            request.pathname = '/'
            request.headers = {
                'host': '127.0.0.1:19999',
                'sec-websocket-protocol': 'general',
            }

            runtime = RuntimeOptions(
                connect_timeout=5000,
                read_timeout=5000,
                web_socket_ping_interval=0,
                web_socket_enable_reconnect=False,
            )
            handler = MockWebSocketHandler()
            client = new_default_websocket_client(handler)
            try:
                client.connect(request, runtime)
            except (ConnectionRefusedError, Exception):
                pass

            header = captured.get('header', {})
            # Value must be exactly 'general', not 'general,general'
            self.assertEqual('general', header.get('sec-websocket-protocol'))
        finally:
            ws_lib.WebSocketApp.__init__ = original_init

    def _make_client_for_unit(self, enable_reconnect=True, max_times=5):
        handler = MockWebSocketHandler()
        client = new_default_websocket_client(handler)
        request = DaraRequest()
        request.protocol = 'ws'
        request.domain = '127.0.0.1:19999'
        request.pathname = '/'
        request.headers = {'host': '127.0.0.1:19999'}
        client.request = request
        client.runtime_object = RuntimeOptions(
            web_socket_enable_reconnect=enable_reconnect,
            web_socket_max_reconnect_times=max_times,
            web_socket_reconnect_interval=1,
            web_socket_write_timeout=50,
        )
        client.reconnect_interval = 1
        client.max_reconnect_times = max_times
        client.write_timeout = 50
        client._sleep_interruptible = lambda _ms: True
        client._cleanup_resources = mock.MagicMock()
        return client, handler

    def test_reconnect_disabled_and_limits(self):
        client, _handler = self._make_client_for_unit(enable_reconnect=False)
        with self.assertRaisesRegex(Exception, 'reconnect is disabled'):
            client.reconnect()

        client, _handler = self._make_client_for_unit(enable_reconnect=True, max_times=1)
        client.reconnect_count = 1
        with self.assertRaisesRegex(Exception, 'max reconnect times reached'):
            client.reconnect()

        client, _handler = self._make_client_for_unit()
        client.state = STATE_CONNECTED
        with self.assertRaisesRegex(Exception, 'already connected'):
            client.reconnect()

        client, _handler = self._make_client_for_unit()
        client._abort_event.set()
        with self.assertRaisesRegex(Exception, 'connection aborted'):
            client.reconnect()

    def test_reconnect_already_in_progress(self):
        client, _handler = self._make_client_for_unit()
        self.assertTrue(client._reconnect_lock.acquire(blocking=False))
        try:
            with self.assertRaisesRegex(Exception, 'reconnect already in progress'):
                client.reconnect()
        finally:
            client._reconnect_lock.release()

    def test_reconnect_success_and_graceful(self):
        client, _handler = self._make_client_for_unit()
        client.connect = mock.MagicMock(return_value=mock.MagicMock())
        result = client.reconnect()
        self.assertIsNotNone(result)
        self.assertEqual(0, client.reconnect_count)
        client.connect.assert_called_once()

        client, _handler = self._make_client_for_unit()
        client.session = WebSocketSessionInfo(session_id='sid-1')
        client.connect = mock.MagicMock(return_value=mock.MagicMock())
        client.reconnect_gracefully()
        self.assertEqual('sid-1', client.request.headers.get('X-Acs-Ws-Session-Id'))

        client, _handler = self._make_client_for_unit()
        client.session = None
        with self.assertRaisesRegex(Exception, 'graceful reconnection requires existing session ID'):
            client.reconnect_gracefully()

    def test_send_binary_and_on_message_close(self):
        client, handler = self._make_client_for_unit()
        with self.assertRaisesRegex(Exception, 'not connected'):
            client.send_binary(b'x')

        client.state = STATE_CONNECTED
        client.ws_app = mock.MagicMock()
        client.send_binary(b'bin-data')
        client.ws_app.send.assert_called()

        client.session = WebSocketSessionInfo(session_id='sid')
        client.stopped = False
        client._on_message(None, 'hello-text')
        client._on_message(None, b'hello-bin')
        self.assertEqual(2, handler.message_received_count)

        def boom(_session, _msg):
            raise RuntimeError('handler failed')

        handler.handle_raw_message = boom
        client._on_message(None, 'fail')
        self.assertEqual(1, handler.error_count)

        client.reconnect = mock.MagicMock(side_effect=Exception('skip'))
        client._on_close(None, 1006, 'abnormal')
        client.reconnect.assert_called_once()

    def test_configure_socks5_and_tls_cert(self):
        client, _handler = self._make_client_for_unit()
        runtime = RuntimeOptions(socks_5proxy='127.0.0.1:1080')
        socks = client.configure_socks5_proxy(runtime)
        self.assertEqual('socks5', socks.get('proxy_type'))
        self.assertEqual('127.0.0.1:1080', socks.get('http_proxy_host'))

        parsed = urlparse('wss://example.com/')
        request = DaraRequest()
        request.headers = {}
        proxy = client._configure_proxy(parsed, runtime, request)
        self.assertEqual('socks5', proxy.get('proxy_type'))

        tls = client._configure_tls(
            RuntimeOptions(cert='/c.pem', key='/k.pem', ca='/ca.pem', ignore_ssl=False),
            'wss',
        )
        self.assertEqual('/c.pem', tls.get('certfile'))
        self.assertEqual('/k.pem', tls.get('keyfile'))
        self.assertEqual('/ca.pem', tls.get('ca_certs'))

    def test_send_with_timeout_paths(self):
        client, _handler = self._make_client_for_unit()
        client.write_timeout = 1000
        client._send_with_timeout(lambda: None)

        client.write_timeout = 10

        def blockers():
            raise TimeoutError('timeout')

        with self.assertRaises(Exception):
            client._send_with_timeout(blockers)


if __name__ == '__main__':
    unittest.main()

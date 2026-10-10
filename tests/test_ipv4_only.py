import asyncio
import hashlib
import os
import socket
import threading
import unittest
from base64 import b64encode
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from urllib.parse import urlparse

import urllib3.util.connection
from urllib3.exceptions import ConnectTimeoutError, NewConnectionError

from darabonba.core import (
    DaraCore, _is_ipv4_only, create_ipv4_connection, _IPv4AdapterMixin,
    _IPv4HTTPConnection, _IPv4HTTPConnectionPool, _IPv4HTTPSConnectionPool,
    _IPv4TLSAdapter, _IPv4HTTPAdapter, _TLSAdapter,
)
from darabonba.exceptions import RetryError
from darabonba.request import DaraRequest
from darabonba.runtime import RuntimeOptions
from darabonba.websocket import (
    AbstractWebSocketHandler, DefaultWebSocketClient, _open_ipv4_socket, get_ipv4_only,
)

WEBSOCKET_GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
PROXY_ENV_KEYS = ('HTTP_PROXY', 'http_proxy', 'HTTPS_PROXY', 'https_proxy', 'NO_PROXY', 'no_proxy')


def _localhost_is_dual_stack():
    try:
        infos = socket.getaddrinfo('localhost', 80, 0, socket.SOCK_STREAM)
    except socket.gaierror:
        return False
    addrs = {info[4][0] for info in infos}
    if '127.0.0.1' not in addrs or '::1' not in addrs:
        return False
    try:
        probe = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        try:
            probe.bind(('::1', 0))
        finally:
            probe.close()
    except OSError:
        return False
    return True


DUAL_STACK = _localhost_is_dual_stack()
SKIP_REASON = 'localhost does not resolve to both 127.0.0.1 and ::1, or IPv6 loopback is unavailable'


class _TagHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def do_GET(self):
        body = self.server.tag
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def _start_http_server(family, host, tag):
    class _Server(ThreadingHTTPServer):
        address_family = family
        daemon_threads = True

    server = _Server((host, 0), _TagHandler)
    server.tag = tag
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _stop_http_server(server):
    server.shutdown()
    server.server_close()


def _request(port, protocol='http'):
    request = DaraRequest()
    request.protocol = protocol
    request.port = port
    request.headers['host'] = 'localhost'
    request.pathname = '/'
    return request


def _runtime(ipv4_only=None, **kwargs):
    kwargs.setdefault('connect_timeout', 2000)
    kwargs.setdefault('read_timeout', 2000)
    runtime = RuntimeOptions(**kwargs).to_map()
    if ipv4_only is not None:
        runtime['ipv4Only'] = ipv4_only
    return runtime


class _NoProxyEnvMixin:
    def setUp(self):
        env = {k: v for k, v in os.environ.items() if k not in PROXY_ENV_KEYS}
        self._env_patch = patch.dict(os.environ, env, clear=True)
        self._env_patch.start()

    def tearDown(self):
        self._env_patch.stop()


class TestIPv4OnlyHelpers(unittest.TestCase):
    def test_is_ipv4_only(self):
        self.assertFalse(_is_ipv4_only(None))
        self.assertFalse(_is_ipv4_only({}))
        self.assertFalse(_is_ipv4_only({'ipv4Only': None}))
        self.assertFalse(_is_ipv4_only({'ipv4Only': False}))
        self.assertFalse(_is_ipv4_only({'ipv4Only': 'false'}))
        self.assertTrue(_is_ipv4_only({'ipv4Only': True}))
        self.assertTrue(_is_ipv4_only({'ipv4Only': ' True '}))

    def test_websocket_get_ipv4_only(self):
        self.assertFalse(get_ipv4_only(None))
        self.assertFalse(get_ipv4_only(RuntimeOptions()))
        self.assertTrue(get_ipv4_only({'ipv4Only': True}))
        self.assertTrue(get_ipv4_only({'ipv4Only': 'true'}))
        self.assertFalse(get_ipv4_only({'ipv4Only': 'false'}))

    def test_create_ipv4_connection_only_asks_for_af_inet(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('127.0.0.1', 0))
        server.listen(1)
        try:
            with patch('darabonba.core.socket.getaddrinfo', wraps=socket.getaddrinfo) as gai:
                sock = create_ipv4_connection(
                    ('[127.0.0.1]', server.getsockname()[1]), 2,
                    source_address=('127.0.0.1', 0),
                    socket_options=[(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)],
                )
            try:
                self.assertEqual(socket.AF_INET, sock.family)
                self.assertEqual(2, sock.gettimeout())
            finally:
                sock.close()
            self.assertEqual(socket.AF_INET, gai.call_args[0][2])
        finally:
            server.close()

    def test_create_ipv4_connection_rejects_ipv6_literal(self):
        with self.assertRaises(socket.gaierror):
            create_ipv4_connection(('::1', 80), 1)

    def test_create_ipv4_connection_empty_and_failed(self):
        with patch('darabonba.core.socket.getaddrinfo', return_value=[]):
            with self.assertRaisesRegex(OSError, 'no IPv4 address'):
                create_ipv4_connection(('example.com', 80))
        # Default-timeout sentinel objects must leave the socket timeout untouched.
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.bind(('127.0.0.1', 0))
        closed_port = probe.getsockname()[1]
        probe.close()
        with self.assertRaises(OSError):
            create_ipv4_connection(('127.0.0.1', closed_port), object())

    def test_connection_error_mapping(self):
        conn = _IPv4HTTPConnection('localhost', 80, timeout=1)
        with patch('darabonba.core.create_ipv4_connection', side_effect=socket.timeout('t')):
            with self.assertRaises(ConnectTimeoutError):
                conn._new_conn()
        with patch('darabonba.core.create_ipv4_connection', side_effect=OSError('boom')):
            with self.assertRaises(NewConnectionError):
                conn._new_conn()

    def test_adapters(self):
        default = DaraCore.get_adapter('https', 'TLSv1.2')
        self.assertIs(_TLSAdapter, type(default))
        self.assertNotIsInstance(default, _IPv4AdapterMixin)

        adapter = DaraCore.get_adapter('https', 'TLSv1.2', pool_size=7, ipv4_only=True)
        self.assertIsInstance(adapter, _IPv4TLSAdapter)
        self.assertEqual(7, adapter._pool_maxsize)
        self.assertIs(_IPv4HTTPConnectionPool, adapter.poolmanager.pool_classes_by_scheme['http'])
        self.assertIs(_IPv4HTTPSConnectionPool, adapter.poolmanager.pool_classes_by_scheme['https'])
        # Process-wide defaults must stay untouched.
        self.assertIsNot(_IPv4HTTPConnectionPool, default.poolmanager.pool_classes_by_scheme['http'])

        proxy_manager = adapter.proxy_manager_for('http://127.0.0.1:3128')
        self.assertIs(_IPv4HTTPConnectionPool, proxy_manager.pool_classes_by_scheme['http'])
        self.assertIs(_IPv4HTTPSConnectionPool, proxy_manager.pool_classes_by_scheme['https'])

    def test_get_session_ipv4_only_mounts_both_schemes(self):
        for protocol, verify in (('https', True), ('https', False), ('http', True)):
            key = f'{protocol}://ipv4-session-test:{protocol}:{verify}:ipv4Only=True'
            DaraCore._sessions.pop(key, None)
            session = DaraCore._get_session(key, protocol, 'TLSv1.2', verify=verify,
                                            pool_size=3, ipv4_only=True)
            try:
                for prefix in ('http://x/', 'https://x/'):
                    self.assertIsInstance(session.get_adapter(prefix), _IPv4AdapterMixin)
            finally:
                DaraCore._sessions.pop(key, None)
        self.assertIsInstance(
            DaraCore._get_session('https://ipv4-insecure:1:ipv4Only=True', 'https', verify=False,
                                  ipv4_only=True).get_adapter('https://x/'),
            _IPv4HTTPAdapter,
        )
        DaraCore._sessions.pop('https://ipv4-insecure:1:ipv4Only=True', None)

    def test_session_key_includes_ipv4_only(self):
        request = DaraRequest()
        request.headers['host'] = 'example.com'
        with patch('darabonba.core.DaraCore._get_session') as get_session:
            get_session.return_value.send.side_effect = IOError('stop')
            for option, expected in ((None, False), ({'ipv4Only': True}, True)):
                with self.assertRaises(RetryError):
                    DaraCore.do_action(request, option)
                kwargs = get_session.call_args[1]
                self.assertTrue(kwargs['session_key'].endswith(f':ipv4Only={expected}'))
                self.assertEqual(expected, kwargs['ipv4_only'])
                with self.assertRaises(RetryError):
                    DaraCore.do_sse_action(request, option)
                kwargs = get_session.call_args[1]
                self.assertTrue(kwargs['session_key'].endswith(f':ipv4Only={expected}'))

    def test_async_connector_family(self):
        request = DaraRequest()
        request.headers['host'] = 'example.com'
        request.protocol = 'https'
        cases = (
            ({}, None),
            ({'ipv4Only': True}, socket.AF_INET),
            ({'ipv4Only': True, 'ignoreSSL': True}, socket.AF_INET),
            ({'ipv4Only': True, 'ca': __file__}, socket.AF_INET),
        )
        for func in (DaraCore.async_do_action, DaraCore.async_do_sse_action):
            for option, family in cases:
                with patch('darabonba.core.aiohttp.TCPConnector', side_effect=RuntimeError('stop')) as tcp, \
                        patch('darabonba.core.ssl.SSLContext.load_verify_locations'):
                    with self.assertRaises(RuntimeError):
                        asyncio.run(func(request, option))
                self.assertEqual(family, tcp.call_args[1].get('family'))


@unittest.skipUnless(DUAL_STACK, SKIP_REASON)
class TestIPv4OnlySync(_NoProxyEnvMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.v6_server = _start_http_server(socket.AF_INET6, '::1', b'v6')
        self.v4_server = _start_http_server(socket.AF_INET, '127.0.0.1', b'v4')
        self.v6_port = self.v6_server.server_address[1]
        self.v4_port = self.v4_server.server_address[1]

    def tearDown(self):
        _stop_http_server(self.v6_server)
        _stop_http_server(self.v4_server)
        super().tearDown()

    def test_default_dual_stack_reaches_ipv6_only_server(self):
        resp = DaraCore.do_action(_request(self.v6_port), _runtime())
        self.assertEqual(200, resp.status_code)
        self.assertEqual(b'v6', resp.body)

    def test_ipv4_only_fails_against_ipv6_only_server(self):
        with self.assertRaises(RetryError):
            DaraCore.do_action(_request(self.v6_port), _runtime(ipv4_only=True))

    def test_ipv4_only_succeeds_against_ipv4_server(self):
        resp = DaraCore.do_action(_request(self.v4_port), _runtime(ipv4_only=True))
        self.assertEqual(b'v4', resp.body)

    def test_ipv4_only_has_no_global_side_effect(self):
        gai_family_before = urllib3.util.connection.allowed_gai_family()
        getaddrinfo_before = socket.getaddrinfo
        with self.assertRaises(RetryError):
            DaraCore.do_action(_request(self.v6_port), _runtime(ipv4_only=True))
        self.assertEqual(b'v4', DaraCore.do_action(_request(self.v4_port), _runtime(ipv4_only=True)).body)

        resp = DaraCore.do_action(_request(self.v6_port), _runtime())
        self.assertEqual(b'v6', resp.body)
        resp = DaraCore.do_action(_request(self.v6_port), _runtime(ipv4_only=False))
        self.assertEqual(b'v6', resp.body)
        self.assertEqual(gai_family_before, urllib3.util.connection.allowed_gai_family())
        self.assertIs(getaddrinfo_before, socket.getaddrinfo)

    def test_pool_not_shared_between_dual_stack_and_ipv4_only(self):
        # The dual-stack request leaves a keep-alive connection to ::1 in its pool.
        self.assertEqual(b'v6', DaraCore.do_action(_request(self.v6_port), _runtime()).body)
        with self.assertRaises(RetryError):
            DaraCore.do_action(_request(self.v6_port), _runtime(ipv4_only=True))
        self.assertEqual(b'v6', DaraCore.do_action(_request(self.v6_port), _runtime()).body)

    def test_sse_ipv4_only(self):
        with self.assertRaises(RetryError):
            DaraCore.do_sse_action(_request(self.v6_port), _runtime(ipv4_only=True))
        resp = DaraCore.do_sse_action(_request(self.v4_port), _runtime(ipv4_only=True))
        self.assertEqual(200, resp.status_code)
        resp.body.response.close()

    def test_proxy_connection_is_ipv4_only(self):
        # The tag servers answer absolute-form proxy requests, so they double as forward proxies.
        target = _request(80)
        target.headers['host'] = 'ipv4-only-target.invalid'
        with self.assertRaises(RetryError):
            DaraCore.do_action(target, _runtime(ipv4_only=True, http_proxy=f'http://localhost:{self.v6_port}'))
        resp = DaraCore.do_action(target, _runtime(ipv4_only=True, http_proxy=f'http://localhost:{self.v4_port}'))
        self.assertEqual(b'v4', resp.body)
        resp = DaraCore.do_action(target, _runtime(http_proxy=f'http://localhost:{self.v6_port}'))
        self.assertEqual(b'v6', resp.body)


@unittest.skipUnless(DUAL_STACK, SKIP_REASON)
class TestIPv4OnlyAsync(_NoProxyEnvMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.v6_server = _start_http_server(socket.AF_INET6, '::1', b'v6')
        self.v4_server = _start_http_server(socket.AF_INET, '127.0.0.1', b'v4')
        self.v6_port = self.v6_server.server_address[1]
        self.v4_port = self.v4_server.server_address[1]

    def tearDown(self):
        _stop_http_server(self.v6_server)
        _stop_http_server(self.v4_server)
        super().tearDown()

    @staticmethod
    def _do(port, runtime, host='localhost'):
        request = _request(port)
        request.headers['host'] = host
        return asyncio.run(DaraCore.async_do_action(request, runtime))

    def test_default_dual_stack_reaches_ipv6_only_server(self):
        self.assertEqual(b'v6', self._do(self.v6_port, _runtime()).body)

    def test_ipv4_only_fails_against_ipv6_only_server(self):
        with self.assertRaises(RetryError):
            self._do(self.v6_port, _runtime(ipv4_only=True))

    def test_ipv4_only_succeeds_against_ipv4_server(self):
        self.assertEqual(b'v4', self._do(self.v4_port, _runtime(ipv4_only=True)).body)

    def test_ipv4_only_has_no_global_side_effect(self):
        with self.assertRaises(RetryError):
            self._do(self.v6_port, _runtime(ipv4_only=True))
        self.assertEqual(b'v6', self._do(self.v6_port, _runtime()).body)
        self.assertEqual(b'v6', self._do(self.v6_port, _runtime(ipv4_only=False)).body)
        # The sync path in the same process is not affected either.
        self.assertEqual(b'v6', DaraCore.do_action(_request(self.v6_port), _runtime()).body)

    def test_pool_not_shared_between_dual_stack_and_ipv4_only(self):
        self.assertEqual(b'v6', self._do(self.v6_port, _runtime()).body)
        with self.assertRaises(RetryError):
            self._do(self.v6_port, _runtime(ipv4_only=True))
        self.assertEqual(b'v6', self._do(self.v6_port, _runtime()).body)

    def test_sse_ipv4_only(self):
        async def run(port, runtime):
            resp = await DaraCore.async_do_sse_action(_request(port), runtime)
            await resp.body.session.close()
            return resp

        with self.assertRaises(RetryError):
            asyncio.run(run(self.v6_port, _runtime(ipv4_only=True)))
        self.assertEqual(200, asyncio.run(run(self.v4_port, _runtime(ipv4_only=True))).status_code)
        self.assertEqual(200, asyncio.run(run(self.v6_port, _runtime())).status_code)

    def test_proxy_connection_is_ipv4_only(self):
        host = 'ipv4-only-target.invalid'
        with self.assertRaises(RetryError):
            self._do(80, _runtime(ipv4_only=True, http_proxy=f'http://localhost:{self.v6_port}'), host)
        resp = self._do(80, _runtime(ipv4_only=True, http_proxy=f'http://localhost:{self.v4_port}'), host)
        self.assertEqual(b'v4', resp.body)
        resp = self._do(80, _runtime(http_proxy=f'http://localhost:{self.v6_port}'), host)
        self.assertEqual(b'v6', resp.body)


class _Handler(AbstractWebSocketHandler):
    def handle_raw_message(self, session, message):
        pass


class _HandshakeServer:
    """Minimal websocket server; with tunnel=True it first accepts an HTTP CONNECT like a proxy."""

    def __init__(self, family, host, tunnel=False):
        self._server = socket.socket(family, socket.SOCK_STREAM)
        self._server.bind((host, 0))
        self._server.listen(5)
        self._server.settimeout(0.2)
        self.port = self._server.getsockname()[1]
        self.tunnel = tunnel
        self.connect_lines = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self):
        while not self._stop.is_set():
            try:
                conn, _ = self._server.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    @staticmethod
    def _read_head(conn):
        data = b''
        while b'\r\n\r\n' not in data:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
        return data.decode('utf-8', errors='ignore')

    def _handle(self, conn):
        try:
            if self.tunnel:
                self.connect_lines.append(self._read_head(conn).split('\r\n')[0])
                conn.sendall(b'HTTP/1.1 200 Connection established\r\n\r\n')
            head = self._read_head(conn)
            key = ''
            for line in head.split('\r\n'):
                if line.lower().startswith('sec-websocket-key:'):
                    key = line.split(':', 1)[1].strip()
            accept = b64encode(hashlib.sha1((key + WEBSOCKET_GUID).encode()).digest()).decode()
            conn.sendall((
                'HTTP/1.1 101 Switching Protocols\r\n'
                'Upgrade: websocket\r\n'
                'Connection: Upgrade\r\n'
                f'Sec-WebSocket-Accept: {accept}\r\n\r\n'
            ).encode())
            while conn.recv(4096):
                pass
        except OSError:
            pass
        finally:
            conn.close()

    def close(self):
        self._stop.set()
        self._server.close()
        self._thread.join(timeout=2)


def _ws_request(port):
    request = DaraRequest()
    request.protocol = 'ws'
    request.pathname = '/'
    request.headers = {'host': f'localhost:{port}'}
    return request


def _ws_runtime(ipv4_only=None, **kwargs):
    runtime = RuntimeOptions(
        connect_timeout=2000,
        web_socket_handshake_timeout=3000,
        web_socket_ping_interval=0,
        web_socket_enable_reconnect=False,
        **kwargs
    ).to_map()
    if ipv4_only is not None:
        runtime['ipv4Only'] = ipv4_only
    return runtime


@unittest.skipUnless(DUAL_STACK, SKIP_REASON)
class TestIPv4OnlyWebSocket(_NoProxyEnvMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.v6_server = _HandshakeServer(socket.AF_INET6, '::1')
        self.v4_server = _HandshakeServer(socket.AF_INET, '127.0.0.1')

    def tearDown(self):
        self.v6_server.close()
        self.v4_server.close()
        super().tearDown()

    def _connect(self, port, runtime):
        client = DefaultWebSocketClient(_Handler())
        client.connect(_ws_request(port), runtime)
        return client

    def test_dual_stack_and_ipv4_only(self):
        client = self._connect(self.v6_server.port, _ws_runtime())
        self.assertTrue(client.is_connected())
        client.disconnect()

        client = DefaultWebSocketClient(_Handler())
        with self.assertRaises(OSError):
            client.connect(_ws_request(self.v6_server.port), _ws_runtime(ipv4_only=True))
        self.assertFalse(client.is_connected())

        client = self._connect(self.v4_server.port, _ws_runtime(ipv4_only=True))
        self.assertTrue(client.is_connected())
        self.assertEqual(socket.AF_INET, client.ws_app.sock.sock.family)
        client.disconnect()

        client = self._connect(self.v6_server.port, _ws_runtime())
        self.assertTrue(client.is_connected())
        client.disconnect()

    def test_http_proxy_is_dialed_over_ipv4(self):
        v4_proxy = _HandshakeServer(socket.AF_INET, '127.0.0.1', tunnel=True)
        v6_proxy = _HandshakeServer(socket.AF_INET6, '::1', tunnel=True)
        try:
            request = _ws_request(8080)
            request.headers['host'] = 'ipv4-only-target.invalid:8080'
            client = DefaultWebSocketClient(_Handler())
            with self.assertRaises(OSError):
                client.connect(request, _ws_runtime(ipv4_only=True, http_proxy=f'http://localhost:{v6_proxy.port}'))

            client = DefaultWebSocketClient(_Handler())
            client.connect(request, _ws_runtime(ipv4_only=True, http_proxy=f'http://localhost:{v4_proxy.port}'))
            self.assertTrue(client.is_connected())
            self.assertEqual(['CONNECT ipv4-only-target.invalid:8080 HTTP/1.1'], v4_proxy.connect_lines)
            client.disconnect()
        finally:
            v4_proxy.close()
            v6_proxy.close()


class TestIPv4OnlyWebSocketSocket(unittest.TestCase):
    def test_socks5_rejected(self):
        with self.assertRaisesRegex(ValueError, 'socks5Proxy'):
            _open_ipv4_socket(urlparse('ws://example.com/'), {}, {'proxy_type': 'socks5'}, 1000)

    def test_wss_wraps_tls_and_closes_on_failure(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('127.0.0.1', 0))
        server.listen(2)
        port = server.getsockname()[1]
        try:
            parsed = urlparse(f'wss://127.0.0.1:{port}/')
            with patch('darabonba.websocket._ws_http._ssl_socket', side_effect=lambda s, opt, host: s) as wrap:
                sock = _open_ipv4_socket(parsed, {'cert_reqs': 0}, {}, 1000)
                sock.close()
            wrap.assert_called_once()
            self.assertEqual('127.0.0.1', wrap.call_args[0][2])

            with patch('darabonba.websocket._ws_http._ssl_socket', side_effect=OSError('tls failed')):
                with self.assertRaisesRegex(OSError, 'tls failed'):
                    _open_ipv4_socket(parsed, {}, {}, 1000)
        finally:
            server.close()


if __name__ == '__main__':
    unittest.main()

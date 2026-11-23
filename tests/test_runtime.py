import unittest
from darabonba.runtime import RuntimeOptions, ExtendsParameters

class TestRuntime(unittest.TestCase):
    def test_oss_private_url_round_trip(self):
        self.assertNotIn('ossPrivateUrl', RuntimeOptions().to_map())
        for endpoint in ('', 'http://localhost:8080/prefix', 'https://oss.example.test'):
            model = RuntimeOptions(oss_private_url=endpoint)
            self.assertEqual(endpoint, model.oss_private_url)
            self.assertEqual(endpoint, model.to_map()['ossPrivateUrl'])
            self.assertEqual(endpoint, RuntimeOptions().from_map(model.to_map()).oss_private_url)

    def test_oss_private_url_with_ipv4_only(self):
        for ipv4_only in (None, False, True):
            for endpoint in (None, '', 'http://localhost:8080/prefix', 'https://oss.example.test'):
                with self.subTest(ipv4_only=ipv4_only, endpoint=endpoint):
                    model = RuntimeOptions(
                        ipv4_only=ipv4_only,
                        oss_private_url=endpoint,
                        read_timeout=123,
                        keep_alive=False,
                        extends_parameters=ExtendsParameters(headers={'X-Test': 'value'}),
                    )
                    expected = {
                        'readTimeout': 123,
                        'keepAlive': False,
                        'extendsParameters': {'headers': {'X-Test': 'value'}},
                    }
                    if ipv4_only is not None:
                        expected['ipv4Only'] = ipv4_only
                    if endpoint is not None:
                        expected['ossPrivateUrl'] = endpoint
                    self.assertEqual(expected, model.to_map())
                    restored = RuntimeOptions().from_map(expected)
                    self.assertEqual(ipv4_only, restored.ipv4_only)
                    self.assertEqual(endpoint, restored.oss_private_url)
                    self.assertEqual(expected, restored.to_map())

    def test_oss_private_url_preserves_positional_arguments(self):
        # 按已发布上游的参数顺序传入哨兵，防止新字段挤占已有位置。
        names = (
            'retry_options', 'autoretry', 'ignore_ssl', 'max_attempts',
            'backoff_policy', 'backoff_period', 'read_timeout', 'connect_timeout',
            'http_proxy', 'https_proxy', 'no_proxy', 'max_idle_conns', 'local_addr',
            'socks_5proxy', 'socks_5net_work', 'keep_alive', 'key', 'cert', 'ca',
            'extends_parameters', 'web_socket_ping_interval', 'web_socket_pong_timeout',
            'web_socket_enable_reconnect', 'web_socket_reconnect_interval',
            'web_socket_max_reconnect_times', 'web_socket_write_timeout',
            'web_socket_handshake_timeout', 'web_socket_handler', 'ipv4_only',
        )
        values = [object() for _ in names]
        for endpoint in (None, '', 'https://oss.example.test'):
            model = RuntimeOptions(*values, oss_private_url=endpoint)
            for name, value in zip(names, values):
                self.assertIs(value, getattr(model, name))
            self.assertEqual(endpoint, model.oss_private_url)

    def test_init(self):
        option = RuntimeOptions()
        option.validate()
        self.assertEqual(None, option.autoretry)

        extends_parameters = ExtendsParameters(
            headers={'key': 'value'},
            queries={'key': 'value'},
        )
        extends_parameters.validate()
        self.assertIsNotNone(extends_parameters.headers)

        option = RuntimeOptions(
            autoretry=True,
            ignore_ssl=True,
            key="key",
            cert="cert",
            ca="ca",
            max_attempts=1,
            backoff_policy="test",
            backoff_period=1,
            read_timeout=1,
            connect_timeout=1,
            http_proxy="test",
            https_proxy="test",
            no_proxy="test",
            max_idle_conns=1,
            local_addr="test",
            socks_5proxy="test",
            socks_5net_work="test",
            keep_alive=False,
            extends_parameters=extends_parameters
        )
        option.validate()
        self.assertEqual(True, option.autoretry)
        self.assertEqual(True, option.ignore_ssl)
        self.assertEqual('key', option.key)
        self.assertEqual('cert', option.cert)
        self.assertEqual('ca', option.ca)
        self.assertEqual(1, option.max_attempts)
        self.assertEqual('test', option.backoff_policy)
        self.assertEqual(1, option.backoff_period)
        self.assertEqual(1, option.read_timeout)
        self.assertEqual(1, option.connect_timeout)
        self.assertEqual('test', option.http_proxy)
        self.assertEqual('test', option.https_proxy)
        self.assertEqual('test', option.no_proxy)
        self.assertEqual(1, option.max_idle_conns)
        self.assertEqual('test', option.local_addr)
        self.assertEqual('test', option.socks_5proxy)
        self.assertEqual('test', option.socks_5net_work)
        self.assertEqual(False, option.keep_alive)
        self.assertEqual('value', option.extends_parameters.headers['key'])
        self.assertEqual('value', option.extends_parameters.queries['key'])

    def test_to_map(self):
        option = RuntimeOptions(
            autoretry=True,
            ignore_ssl=True,
            key="key",
            cert="cert",
            ca="ca",
            max_attempts=1,
            backoff_policy="test",
            backoff_period=1,
            read_timeout=1,
            connect_timeout=1,
            http_proxy="test",
            https_proxy="test",
            no_proxy="test",
            max_idle_conns=1,
            local_addr="test",
            socks_5proxy="test",
            socks_5net_work="test",
            keep_alive=False,
            extends_parameters=ExtendsParameters(
                headers={'key': 'value'},
                queries={'key': 'value'},
            ),
        )
        result = option.to_map()
        self.assertEqual(True, result.get('autoretry'))
        self.assertEqual(True, result.get('ignoreSSL'))
        self.assertEqual('key', result.get('key'))
        self.assertEqual('cert', result.get('cert'))
        self.assertEqual('ca', result.get('ca'))
        self.assertEqual(1, result.get('max_attempts'))
        self.assertEqual('test', result.get('backoff_policy'))
        self.assertEqual(1, result.get('backoff_period'))
        self.assertEqual(1, result.get('readTimeout'))
        self.assertEqual(1, result.get('connectTimeout'))
        self.assertEqual('test', result.get('httpProxy'))
        self.assertEqual('test', result.get('httpsProxy'))
        self.assertEqual('test', result.get('noProxy'))
        self.assertEqual(1, result.get('maxIdleConns'))
        self.assertEqual('test', result.get('localAddr'))
        self.assertEqual('test', result.get('socks5Proxy'))
        self.assertEqual('test', result.get('socks5NetWork'))
        self.assertEqual(False, result.get('keepAlive'))
        self.assertEqual('value', result.get('extendsParameters').get('headers').get('key'))
        self.assertEqual('value', result.get('extendsParameters').get('queries').get('key'))
        option.extends_parameters._map = {'test': 'test'}
        result = option.extends_parameters.to_map()
        self.assertEqual('test', result.get('test'))
        option._map = {'test': 'test'}
        result = option.to_map()
        self.assertEqual('test', result.get('test'))

    def test_from_map(self):
        option = RuntimeOptions()
        dic = {
            'autoretry': True,
            'ignoreSSL': True,
            'key': 'key',
            'cert': 'cert',
            'ca': 'ca',
            'max_attempts': 1,
            'backoff_policy': 'test',
            'backoff_period': 1,
            'readTimeout': 1,
            'connectTimeout': 1,
            'httpProxy': 'test',
            'httpsProxy': 'test',
            'noProxy': 'test',
            'maxIdleConns': 1,
            'localAddr': 'test',
            'socks5Proxy': 'test',
            'socks5NetWork': 'test',
            'keepAlive': False,
            'extendsParameters': {
                'headers': {
                    'key': 'value',
                },
                'queries': {
                    'key': 'value',
                },
            },
        }
        option.from_map(dic)
        self.assertEqual(True, option.autoretry)
        self.assertEqual(True, option.ignore_ssl)
        self.assertEqual('key', option.key)
        self.assertEqual('cert', option.cert)
        self.assertEqual('ca', option.ca)
        self.assertEqual(1, option.max_attempts)
        self.assertEqual('test', option.backoff_policy)
        self.assertEqual(1, option.backoff_period)
        self.assertEqual(1, option.read_timeout)
        self.assertEqual(1, option.connect_timeout)
        self.assertEqual('test', option.http_proxy)
        self.assertEqual('test', option.https_proxy)
        self.assertEqual('test', option.no_proxy)
        self.assertEqual(1, option.max_idle_conns)
        self.assertEqual('test', option.local_addr)
        self.assertEqual('test', option.socks_5proxy)
        self.assertEqual('test', option.socks_5net_work)
        self.assertEqual(False, option.keep_alive)
        self.assertEqual('value', option.extends_parameters.headers['key'])
        self.assertEqual('value', option.extends_parameters.queries['key'])

    def test_ipv4_only(self):
        option = RuntimeOptions()
        self.assertIsNone(option.ipv4_only)
        self.assertNotIn('ipv4Only', option.to_map())
        self.assertIsNone(RuntimeOptions().from_map({}).ipv4_only)

        self.assertEqual(True, RuntimeOptions(ipv4_only=True).to_map().get('ipv4Only'))
        self.assertEqual(False, RuntimeOptions(ipv4_only=False).to_map().get('ipv4Only'))

        self.assertEqual(True, RuntimeOptions().from_map({'ipv4Only': True}).ipv4_only)
        self.assertEqual(False, RuntimeOptions().from_map({'ipv4Only': False}).ipv4_only)
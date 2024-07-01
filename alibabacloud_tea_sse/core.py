import logging
import os
import re
import time
import aiohttp
import ssl
import certifi
from urllib.parse import urlencode, urlparse
import json

from requests import status_codes, adapters, PreparedRequest, Response

from .event import Event
from .exceptions import TeaException, RequiredArgumentException, RetryError
from .model import TeaModel
from .request import TeaRequest
from .response import TeaResponse
from .stream import BaseStream

from typing import Dict, Any, Optional

DEFAULT_CONNECT_TIMEOUT = 5000
DEFAULT_READ_TIMEOUT = 10000
DEFAULT_POOL_SIZE = 128

logger = logging.getLogger('alibabacloud-tea')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
logger.addHandler(ch)

sse_line_pattern = re.compile('(?P<name>[^:]*):?( ?(?P<value>.*))?')
end_of_field = re.compile(b'\r\n\r\n|\r\r|\n\n')


class TeaCore:
    http_adapter = adapters.HTTPAdapter(DEFAULT_POOL_SIZE, DEFAULT_POOL_SIZE)
    https_adapter = adapters.HTTPAdapter(DEFAULT_POOL_SIZE, DEFAULT_POOL_SIZE)
    connectors = {};

    @staticmethod
    def get_adapter(prefix):
        if prefix.upper() == 'HTTP':
            return TeaCore.http_adapter
        else:
            return TeaCore.https_adapter

    @staticmethod
    def get_connector(prefix, verify):
        if prefix.upper() == 'HTTP' or not verify:
            if TeaCore.connectors.get('no_ssl') is None:
                http_connector = aiohttp.TCPConnector(limit=DEFAULT_POOL_SIZE, limit_per_host=DEFAULT_POOL_SIZE)
                TeaCore.connectors.update({'no_ssl': http_connector})
            return TeaCore.connectors.get('no_ssl')
        else:
            if TeaCore.connectors.get('ssl') is None:
                ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                ssl_context.load_verify_locations(certifi.where())
                https_connector = aiohttp.TCPConnector(ssl=ssl_context, limit=DEFAULT_POOL_SIZE, limit_per_host=DEFAULT_POOL_SIZE)
                TeaCore.connectors.update({'ssl': https_connector})
            return TeaCore.connectors.get('ssl')

    @staticmethod
    def _prepare_http_debug(request, symbol):
        base = ''
        for key, value in request.headers.items():
            base += f'\n{symbol} {key} : {value}'
        return base

    @staticmethod
    def _do_http_debug(request, response):
        # logger the request
        url = urlparse(request.url)
        request_base = f'\n> {request.method.upper()} {url.path + url.query} HTTP/1.1'
        logger.debug(request_base + TeaCore._prepare_http_debug(request, '>'))

        # logger the response
        response_base = f'\n< HTTP/1.1 {response.status_code}' \
                        f' {status_codes._codes.get(response.status_code)[0].upper()}'
        logger.debug(response_base + TeaCore._prepare_http_debug(response, '<'))

    @staticmethod
    def compose_url(request):
        host = request.headers.get('host')
        if not host:
            raise RequiredArgumentException('endpoint')
        else:
            host = host.rstrip('/')
        protocol = f'{request.protocol.lower()}://'
        pathname = request.pathname

        if host.startswith(('http://', 'https://')):
            protocol = ''

        if request.port == 80:
            port = ''
        else:
            port = f':{request.port}'

        url = protocol + host + port + pathname

        if request.query:
            if "?" in url:
                if not url.endswith("&"):
                    url += "&"
            else:
                url += "?"

            encode_query = {}
            for key in request.query:
                value = request.query[key]
                if value is not None:
                    encode_query[key] = str(value)
            url += urlencode(encode_query)
        return url.rstrip("?&")

    @staticmethod
    async def async_do_sse_action(
            request: TeaRequest,
            runtime_option=None
    ):
        runtime_option = runtime_option or {}
        url = TeaCore.compose_url(request)
        verify = not runtime_option.get('ignoreSSL', False)
        connect_timeout = runtime_option.get('connectTimeout')
        connect_timeout = connect_timeout if connect_timeout else DEFAULT_CONNECT_TIMEOUT
        read_timeout = runtime_option.get('readTimeout')
        read_timeout = read_timeout if read_timeout else DEFAULT_READ_TIMEOUT
        connect_timeout, read_timeout = (int(connect_timeout) / 1000, int(read_timeout) / 1000)
        proxy = None
        if request.protocol.upper() == 'HTTP':
            proxy = runtime_option.get('httpProxy')
            if not proxy:
                proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
        connector = TeaCore.get_connector(request.protocol, verify)
        if request.protocol.upper() == 'HTTP':
            verify = False
        timeout = aiohttp.ClientTimeout(
            sock_read=read_timeout,
            sock_connect=connect_timeout
        )
        async with aiohttp.ClientSession(
                connector=connector
        ) as s:
            body = b''
            if isinstance(request.body, BaseStream):
                for content in request.body:
                    body += content
            elif isinstance(request.body, str):
                body = request.body.encode('utf-8')
            else:
                body = request.body
            try:
                async with s.request(request.method, url,
                                     data=body,
                                     headers=request.headers,
                                     ssl=verify,
                                     proxy=proxy,
                                     timeout=timeout) as response:
                    tea_resp = TeaResponse()

                    # tea_resp.body = await response.read() if not stream else response.content
                    tea_resp.headers = {k.lower(): v for k, v in response.headers.items()}
                    tea_resp.status_code = response.status
                    tea_resp.status_message = response.reason
                    tea_resp.response = response
                    data = b''
                    async for chunk in response.content.iter_any():
                        match = re.search(end_of_field, chunk)
                        if match:
                            items = re.split(end_of_field, chunk)
                            for index, item in enumerate(items):
                                data += item
                                if index != len(items) - 1:
                                    yield {'response': tea_resp, 'stream': data}
                                    data = b''
                        else:
                            data += chunk
                    if data:
                        yield {'response': tea_resp, 'stream': data}
            except IOError as e:
                raise RetryError(str(e))

    @staticmethod
    def do_sse_action(
            request: TeaRequest,
            runtime_option=None
    ):
        url = TeaCore.compose_url(request)

        runtime_option = runtime_option or {}

        verify = not runtime_option.get('ignoreSSL', False)
        if verify:
            verify = runtime_option.get('ca', True) if runtime_option.get('ca', True) is not None else True
        cert = runtime_option.get('cert', None)

        connect_timeout = runtime_option.get('connectTimeout')
        connect_timeout = connect_timeout if connect_timeout else DEFAULT_CONNECT_TIMEOUT

        read_timeout = runtime_option.get('readTimeout')
        read_timeout = read_timeout if read_timeout else DEFAULT_READ_TIMEOUT

        timeout = (int(connect_timeout) / 1000, int(read_timeout) / 1000)

        if isinstance(request.body, str):
            request.body = request.body.encode('utf-8')

        p = PreparedRequest()
        p.prepare(
            method=request.method.upper(),
            url=url,
            data=request.body,
            headers=request.headers,
        )

        proxies = {}
        http_proxy = runtime_option.get('httpProxy')
        https_proxy = runtime_option.get('httpsProxy')
        no_proxy = runtime_option.get('noProxy')

        if not http_proxy:
            http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
        if not https_proxy:
            https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')

        if http_proxy:
            proxies['http'] = http_proxy
        if https_proxy:
            proxies['https'] = https_proxy
        if no_proxy:
            proxies['no_proxy'] = no_proxy

        adapter = TeaCore.get_adapter(request.protocol)
        try:
            resp = adapter.send(
                p,
                proxies=proxies,
                timeout=timeout,
                verify=verify,
                cert=cert,
                stream=True
            )
        except IOError as e:
            raise RetryError(str(e))

        debug = runtime_option.get('debug') or os.getenv('DEBUG')
        if debug and debug.lower() == 'sdk':
            TeaCore._do_http_debug(p, resp)

        response = TeaResponse()
        response.status_message = resp.reason
        response.status_code = resp.status_code
        response.headers = {k.lower(): v for k, v in resp.headers.items()}
        response.response = resp
        data = b''
        for chunk in resp.iter_content():
            match = re.search(end_of_field, chunk)
            if match:
                items = re.split(end_of_field, chunk)
                for index, item in enumerate(items):
                    data += item
                    if index != len(items) - 1:
                        yield {'response': response, 'stream': data}
                        data = b''
            else:
                data += chunk
        if data:
            yield {'response': response, 'stream': data}

    @staticmethod
    async def async_read_as_sse(
            stream
    ):
        async for chunk in stream:
            event = Event()
            status_code = chunk.get('response').status_code
            headers = chunk.get('response').headers
            if 400 <= status_code:
                decoded_line = chunk.get('stream').decode('utf-8')
                err = json.loads(decoded_line)
                err['statusCode'] = status_code
                raise TeaException({
                    'code': f"{err.get('Code')}",
                    'message': f"code: {status_code}, {err.get('Message')} request id: {err.get('RequestId')}",
                    'data': err,
                    'description': f"{err.get('Description')}",
                    'accessDeniedDetail': err.get('AccessDeniedDetail')
                })
            for line in chunk.get('stream').splitlines():
                decoded_line = line.decode('utf-8')
                if not decoded_line.strip() or decoded_line.startswith(':'):
                    continue
                match = sse_line_pattern.match(decoded_line)
                if match is not None:
                    name = match.group('name')
                    value = match.group('value')
                    if name == 'data':
                        if event.data:
                            event.data = '%s\n%s' % (event.data, value)
                        else:
                            event.data = value
                    elif name == 'event':
                        event.event = value
                    elif name == 'id':
                        event.id = value
                    elif name == 'retry':
                        event.retry = int(value)
            yield {'status_code': status_code, 'headers': headers, 'event': event}

    @staticmethod
    def read_as_sse(
            stream: Response
    ):
        for chunk in stream:
            event = Event()
            status_code = chunk.get('response').status_code
            headers = chunk.get('response').headers
            if 400 <= status_code:
                decoded_line = chunk.get('stream').decode('utf-8')
                err = json.loads(decoded_line)
                err['statusCode'] = status_code
                raise TeaException({
                    'code': f"{err.get('Code')}",
                    'message': f"code: {status_code}, {err.get('Message')} request id: {err.get('RequestId')}",
                    'data': err,
                    'description': f"{err.get('Description')}",
                    'accessDeniedDetail': err.get('AccessDeniedDetail')
                })
            for line in chunk.get('stream').splitlines():
                decoded_line = line.decode('utf-8')
                if not decoded_line.strip() or decoded_line.startswith(':'):
                    continue
                match = sse_line_pattern.match(decoded_line)
                if match is not None:
                    name = match.group('name')
                    value = match.group('value')
                    if name == 'data':
                        if event.data:
                            event.data = '%s\n%s' % (event.data, value)
                        else:
                            event.data = value
                    elif name == 'event':
                        event.event = value
                    elif name == 'id':
                        event.id = value
                    elif name == 'retry':
                        event.retry = int(value)
            yield {'status_code': status_code, 'headers': headers, 'event': event}

    @staticmethod
    async def async_do_action(
            request: TeaRequest,
            runtime_option=None
    ) -> TeaResponse:
        runtime_option = runtime_option or {}

        url = TeaCore.compose_url(request)
        verify = not runtime_option.get('ignoreSSL', False)
        connect_timeout = runtime_option.get('connectTimeout')
        connect_timeout = connect_timeout if connect_timeout else DEFAULT_CONNECT_TIMEOUT

        read_timeout = runtime_option.get('readTimeout')
        read_timeout = read_timeout if read_timeout else DEFAULT_READ_TIMEOUT

        connect_timeout, read_timeout = (int(connect_timeout) / 1000, int(read_timeout) / 1000)

        proxy = None
        if request.protocol.upper() == 'HTTP':
            proxy = runtime_option.get('httpProxy')
            if not proxy:
                proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')

        connector = TeaCore.get_connector(request.protocol, verify)
        ca_cert = certifi.where()
        if request.protocol.upper() == 'HTTP':
            verify = False

        timeout = aiohttp.ClientTimeout(
            sock_read=read_timeout,
            sock_connect=connect_timeout
        )
        async with aiohttp.ClientSession(
                connector=connector
        ) as s:
            body = b''
            if isinstance(request.body, BaseStream):
                for content in request.body:
                    body += content
            elif isinstance(request.body, str):
                body = request.body.encode('utf-8')
            else:
                body = request.body
            try:
                async with s.request(request.method, url,
                                     data=body,
                                     headers=request.headers,
                                     ssl=verify,
                                     proxy=proxy,
                                     timeout=timeout) as response:
                    tea_resp = TeaResponse()
                    tea_resp.body = await response.read()
                    tea_resp.headers = {k.lower(): v for k, v in response.headers.items()}
                    tea_resp.status_code = response.status
                    tea_resp.status_message = response.reason
                    tea_resp.response = response
            except IOError as e:
                raise RetryError(str(e))
        return tea_resp

    @staticmethod
    def do_action(
            request: TeaRequest,
            runtime_option=None
    ) -> TeaResponse:
        url = TeaCore.compose_url(request)

        runtime_option = runtime_option or {}

        verify = not runtime_option.get('ignoreSSL', False)
        if verify:
            verify = runtime_option.get('ca', True) if runtime_option.get('ca', True) is not None else True
        cert = runtime_option.get('cert', None)

        connect_timeout = runtime_option.get('connectTimeout')
        connect_timeout = connect_timeout if connect_timeout else DEFAULT_CONNECT_TIMEOUT

        read_timeout = runtime_option.get('readTimeout')
        read_timeout = read_timeout if read_timeout else DEFAULT_READ_TIMEOUT

        timeout = (int(connect_timeout) / 1000, int(read_timeout) / 1000)

        if isinstance(request.body, str):
            request.body = request.body.encode('utf-8')

        p = PreparedRequest()
        p.prepare(
            method=request.method.upper(),
            url=url,
            data=request.body,
            headers=request.headers,
        )

        proxies = {}
        http_proxy = runtime_option.get('httpProxy')
        https_proxy = runtime_option.get('httpsProxy')
        no_proxy = runtime_option.get('noProxy')

        if not http_proxy:
            http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
        if not https_proxy:
            https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')

        if http_proxy:
            proxies['http'] = http_proxy
        if https_proxy:
            proxies['https'] = https_proxy
        if no_proxy:
            proxies['no_proxy'] = no_proxy

        adapter = TeaCore.get_adapter(request.protocol)
        try:
            resp = adapter.send(
                p,
                proxies=proxies,
                timeout=timeout,
                verify=verify,
                cert=cert,
            )
        except IOError as e:
            raise RetryError(str(e))

        debug = runtime_option.get('debug') or os.getenv('DEBUG')
        if debug and debug.lower() == 'sdk':
            TeaCore._do_http_debug(p, resp)

        response = TeaResponse()
        response.status_message = resp.reason
        response.status_code = resp.status_code
        response.headers = {k.lower(): v for k, v in resp.headers.items()}
        response.body = resp.content
        response.response = resp
        return response

    @staticmethod
    def get_response_body(resp) -> str:
        return resp.content.decode("utf-8")

    @staticmethod
    def allow_retry(dic, retry_times, now=None) -> bool:
        if retry_times == 0:
            return True
        if dic is None or not dic.__contains__("maxAttempts") or \
                dic.get('retryable') is not True and retry_times >= 1:
            return False
        else:
            retry = 0 if dic.get("maxAttempts") is None else int(
                dic.get("maxAttempts"))
        return retry >= retry_times

    @staticmethod
    def get_backoff_time(dic, retry_times) -> int:
        default_back_off_time = 0
        if dic is None or not dic.get("policy") or dic.get("policy") == "no":
            return default_back_off_time

        back_off_time = dic.get('period', default_back_off_time)
        if not isinstance(back_off_time, int) and \
                not (isinstance(back_off_time, str) and back_off_time.isdigit()):
            return default_back_off_time

        back_off_time = int(back_off_time)
        if back_off_time < 0:
            return retry_times

        return back_off_time

    @staticmethod
    def sleep(t):
        time.sleep(t)

    @staticmethod
    def is_retryable(ex) -> bool:
        return isinstance(ex, RetryError)

    @staticmethod
    def bytes_readable(body):
        return body

    @staticmethod
    def merge(*dic_list) -> dict:
        dic_result = {}
        for item in dic_list:
            if isinstance(item, dict):
                dic_result.update(item)
            elif isinstance(item, TeaModel):
                dic_result.update(item.to_map())
        return dic_result

    @staticmethod
    def to_map(model: Optional[TeaModel]) -> Dict[str, Any]:
        if isinstance(model, TeaModel):
            return model.to_map()
        else:
            return dict()

    @staticmethod
    def from_map(
            model: TeaModel,
            dic: Dict[str, Any]
    ) -> TeaModel:
        if isinstance(model, TeaModel):
            try:
                return model.from_map(dic)
            except Exception:
                model._map = dic
                return model
        else:
            return model

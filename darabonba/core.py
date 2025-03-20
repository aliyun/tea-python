import asyncio
import aiohttp
import logging
import io
import os
import ssl
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode, urlparse
import re
import certifi
from requests import status_codes, adapters, PreparedRequest

from darabonba.exceptions import RequiredArgumentException, RetryError
from darabonba.model import DaraModel
from darabonba.request import DaraRequest
from darabonba.response import DaraResponse
from darabonba.utils.stream import BaseStream
from requests import status_codes, adapters, PreparedRequest, Response
from darabonba.event import Event
import json
from darabonba.exceptions import DaraException

sse_line_pattern = re.compile('(?P<name>[^:]*):?( ?(?P<value>.*))?')

DEFAULT_CONNECT_TIMEOUT = 5000
DEFAULT_READ_TIMEOUT = 10000
DEFAULT_POOL_SIZE = 10

logger = logging.getLogger('darabonba-tea')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
logger.addHandler(ch)


class DaraCore:
    http_adapter = adapters.HTTPAdapter(pool_connections=DEFAULT_POOL_SIZE, pool_maxsize=DEFAULT_POOL_SIZE * 4)
    https_adapter = adapters.HTTPAdapter(pool_connections=DEFAULT_POOL_SIZE, pool_maxsize=DEFAULT_POOL_SIZE * 4)

    @staticmethod
    def get_adapter(prefix):
        if prefix.upper() == 'HTTP':
            return DaraCore.http_adapter
        else:
            return DaraCore.https_adapter

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
        logger.debug(request_base + DaraCore._prepare_http_debug(request, '>'))

        # logger the response
        response_base = f'\n< HTTP/1.1 {response.status_code}' \
                        f' {status_codes._codes.get(response.status_code)[0].upper()}'
        logger.debug(response_base + DaraCore._prepare_http_debug(response, '<'))

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
    async def async_do_action(
            request: DaraRequest,
            runtime_option=None
    ) -> DaraResponse:
        runtime_option = runtime_option or {}

        url = DaraCore.compose_url(request)
        verify = not runtime_option.get('ignoreSSL', False)

        timeout = runtime_option.get('timeout')
        connect_timeout = runtime_option.get('connectTimeout') or timeout or DEFAULT_CONNECT_TIMEOUT
        read_timeout = runtime_option.get('readTimeout') or timeout or DEFAULT_READ_TIMEOUT

        connect_timeout, read_timeout = (int(connect_timeout) / 1000, int(read_timeout) / 1000)

        proxy = None
        if request.protocol.upper() == 'HTTP':
            proxy = runtime_option.get('httpProxy')
            if not proxy:
                proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
        elif request.protocol.upper() == 'HTTPS':
            proxy = runtime_option.get('httpsProxy')
            if not proxy:
                proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')

        connector = None
        ca_cert = certifi.where()
        if ca_cert and request.protocol.upper() == 'HTTPS':
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ssl_context.load_verify_locations(ca_cert)
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
            )
        else:
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
                    tea_resp = DaraResponse()
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
            request: DaraRequest,
            runtime_option=None
    ) -> DaraResponse:
        url = DaraCore.compose_url(request)

        runtime_option = runtime_option or {}

        verify = not runtime_option.get('ignoreSSL', False)
        if verify:
            verify = runtime_option.get('ca', True) if runtime_option.get('ca', True) is not None else True
        cert = runtime_option.get('cert', None)

        timeout = runtime_option.get('timeout')
        connect_timeout = runtime_option.get('connectTimeout') or timeout or DEFAULT_CONNECT_TIMEOUT
        read_timeout = runtime_option.get('readTimeout') or timeout or DEFAULT_READ_TIMEOUT

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

        adapter = DaraCore.get_adapter(request.protocol)
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
            DaraCore._do_http_debug(p, resp)

        response = DaraResponse()
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
    async def sleep_async(millisecond: int):
        await asyncio.sleep(millisecond / 1000)

    @staticmethod
    def sleep(millisecond: int):
        time.sleep(millisecond / 1000)

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
            elif isinstance(item, DaraModel):
                dic_result.update(item.to_map())
        return dic_result

    @staticmethod
    def to_map(model: Optional[DaraModel]) -> Dict[str, Any]:
        if isinstance(model, DaraModel):
            return model.to_map()
        else:
            return dict()

    @staticmethod
    def from_map(
            model: DaraModel,
            dic: Dict[str, Any]
    ) -> DaraModel:
        if isinstance(model, DaraModel):
            try:
                return model.from_map(dic)
            except Exception:
                model._map = dic
                return model
        else:
            return model

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
                raise DaraException({
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
    def is_null(value) -> bool:
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == '':
            return True
        if isinstance(value, (list, tuple, dict, set)) and len(value) == 0:
            return True
        return False
    
    @staticmethod
    def to_readable_stream(data):
        if isinstance(data, str):
            # 如果输入是字符串，使用 io.StringIO
            return io.StringIO(data)
        elif isinstance(data, bytes):
            # 如果输入是字节数据，使用 io.BytesIO
            return io.BytesIO(data)
        else:
            raise TypeError("Input data must be of type str or bytes")

    @staticmethod
    def to_map(model: Optional[DaraModel]) -> Dict[str, Any]:
        if isinstance(model, DaraModel):
            return model.to_map()
        else:
            return dict()

    @staticmethod
    def from_map(
            model: DaraModel,
            dic: Dict[str, Any]
    ) -> DaraModel:
        if isinstance(model, DaraModel):
            try:
                return model.from_map(dic)
            except Exception:
                model._map = dic
                return model
        else:
            return model

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
                raise DaraException({
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
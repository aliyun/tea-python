import os
import time

from requests import Request, Session
from Tea.exceptions import TeaException, RequiredArgumentException
from urllib.parse import urlencode
from Tea.response import TeaResponse
from Tea.model import TeaModel

DEFAULT_CONNECT_TIMEOUT = 5000
DEFAULT_READ_TIMEOUT = 10000


class TeaCore:
    @staticmethod
    def compose_url(request):
        host = request.headers.get('host')
        if not host:
            raise RequiredArgumentException('endpoint')
        else:
            host = host.rstrip('/')
        protocol = '%s://' % request.protocol.lower()
        pathname = request.pathname

        if host.startswith(('http://', 'https://')):
            protocol = ''

        if request.port == 80:
            port = ''
        else:
            port = ':%s' % request.port

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
    def do_action(request, runtime_option=None):
        url = TeaCore.compose_url(request)

        runtime_option = runtime_option or {}

        verify = not runtime_option.get('ignoreSSL', False)

        connect_timeout = runtime_option.get('connectTimeout')
        connect_timeout = connect_timeout if connect_timeout else DEFAULT_CONNECT_TIMEOUT

        read_timeout = runtime_option.get('readTimeout')
        read_timeout = read_timeout if read_timeout else DEFAULT_READ_TIMEOUT

        timeout = (int(connect_timeout) / 1000, int(read_timeout) / 1000)
        with Session() as s:
            req = Request(method=request.method, url=url,
                          data=request.body, headers=request.headers)
            prepped = s.prepare_request(req)

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

            resp = s.send(
                prepped,
                proxies=proxies,
                timeout=timeout,
                verify=verify,
            )
            return TeaResponse(resp)

    @staticmethod
    def get_response_body(resp):
        return resp.content.decode("utf-8")

    @staticmethod
    def allow_retry(dic, retry_times, now=None):
        if dic is None or not dic.__contains__("maxAttempts"):
            return False
        else:
            retry = 0 if dic.get("maxAttempts") is None else int(
                dic.get("maxAttempts"))
        return retry >= retry_times

    @staticmethod
    def get_backoff_time(dic, retry_times):
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
    def is_retryable(ex):
        return isinstance(ex, TeaException)

    @staticmethod
    def bytes_readable(body):
        return body

    @staticmethod
    def merge(*dic_list):
        dic_result = {}
        for item in dic_list:
            if isinstance(item, dict):
                if item is not None:
                    dic_result.update(item)
            elif isinstance(item, TeaModel):
                dic_result.update(item.to_map())
        return dic_result

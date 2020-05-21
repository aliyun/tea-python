import os
import time

from requests import Request, Session
from Tea.exceptions import TeaException
from urllib.parse import urlencode
from Tea.response import TeaResponse
from Tea.model import TeaModel


class TeaCore:
    @staticmethod
    def compose_url(request):
        url = str(request.protocol).lower() + "://"
        url += request.headers.get('host') or ""
        if request.port != 80:
            url += ":" + str(request.port)
        url += request.pathname or ""
        if (request.query is not None) and len(request.query) > 0:
            if "?" in url:
                if not url.endswith("&"):
                    url += "&"
            else:
                url += "?"
            encode_query = {}
            for key in request.query:
                value = request.query[key]
                if value is not None and value != "":
                    encode_query[key] = str(value)
            url += urlencode(encode_query)
        return url.strip("?").strip('&')

    @staticmethod
    def do_action(request, runtime_option=None):
        url = TeaCore.compose_url(request)

        runtime_option = runtime_option or {}
        connect_timeout = 5000
        read_timeout = 10000

        if 'connectTimeout' in runtime_option:
            option_connect_timeout = runtime_option["connectTimeout"]
            connect_timeout = option_connect_timeout if option_connect_timeout else connect_timeout

        if 'readTimeout' in runtime_option:
            option_read_timeout = runtime_option["readTimeout"]
            read_timeout = option_read_timeout if option_read_timeout else read_timeout

        timeout = (int(connect_timeout) / 1000, int(read_timeout) / 1000)
        with Session() as s:
            req = Request(method=request.method, url=url,
                          data=request.body, headers=request.headers)
            prepped = s.prepare_request(req)
            proxy_https = os.environ.get('HTTPS_PROXY') or os.environ.get(
                'https_proxy'
            )
            proxy_http = os.environ.get(
                'HTTP_PROXY') or os.environ.get('http_proxy')

            proxies = {
                "http": proxy_http,
                "https": proxy_https,
            }
            resp = s.send(prepped, proxies=proxies,
                          timeout=timeout, cert=None)
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
        back_off_time = 0
        if not dic.__contains__("policy") or dic.get("policy") is None or len(dic.get("policy")) == 0 or dic.get(
                "policy") == "no":
            return back_off_time
        if dic.__contains__("period") and dic.get("period") is not None:
            back_off_time = int(dic.get("period"))
            if back_off_time <= 0:
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

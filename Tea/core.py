import os
import time

from typing import Any

from requests import Request, Session
from Tea.exceptions import TeaException
from urllib.parse import urlencode


class TeaCore:
    def __init__(self):
        super().__init__()

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

    @classmethod
    def do_action(cls, request, runtime_option={}):
        url = cls.compose_url(request)
        connect_timeout = None
        if 'connectTimeout' in runtime_option:
            connect_timeout = runtime_option.get("connectTimeout")
        read_timeout = None
        if 'readTimeout' in runtime_option:
            read_timeout = runtime_option.get("readTimeout")
        with Session() as s:
            req = Request(method=request.method, url=url,
                          data=request.body,
                          headers=request.headers)
            prepped = s.prepare_request(req)
            proxy_https = os.environ.get('HTTPS_PROXY') or os.environ.get(
                'https_proxy')
            proxy_http = os.environ.get(
                'HTTP_PROXY') or os.environ.get('http_proxy')

            proxies = {
                "http": proxy_http,
                "https": proxy_https,
            }
            resp = s.send(prepped, proxies=proxies,
                          timeout=(connect_timeout, read_timeout),
                          allow_redirects=False, cert=None)
            return resp

    @staticmethod
    def get_response_body(resp):
        return resp.content.decode("utf-8")

    @staticmethod
    def allow_retry(dic, retry_times, now):
        retry = 0
        if dic is None or not dic.__contains__("maxAttempts"):
            return False
        else:
            retry = 0 if dic.get("maxAttempts") is None else int(
                dic.get("maxAttempts"))
        return retry >= retry_times

    @staticmethod
    def get_backoff_time(dic, retry_times):
        backOffTime = 0
        if not dic.__contains__("policy") or dic.get("policy") is None or len(dic.get("policy")) == 0 or dic.get("policy") == "no":
            return backOffTime
        if dic.__contains__("period") and dic.get("period") is not None:
            backOffTime = int(dic.get("period"))
            if backOffTime <= 0:
                return retry_times
        return backOffTime

    @staticmethod
    def sleep(t):
        time.sleep(t)

    @staticmethod
    def is_retryable(ex):
        return isinstance(ex, TeaException)

    @staticmethod
    def bytes_readable(body):
        return body

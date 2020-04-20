import os
import time

from requests import Request, Session
from Tea.exceptions import TeaException
from urllib.parse import urlencode


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


def do_action(request, runtime_option={}):
    url = compose_url(request)
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


def get_response_body(resp):
    return resp.content.decode("utf-8")


def allow_retry(dic, retry_times, now):
    if dic is None or not dic.__contains__("maxAttempts"):
        return False
    else:
        retry = 0 if dic.get("maxAttempts") is None else int(
            dic.get("maxAttempts"))
    return retry >= retry_times


def get_backoff_time(dic, retry_times):
    back_off_time = 0
    if not dic.__contains__("policy") or dic.get("policy") is None or len(dic.get("policy")) == 0 or dic.get("policy") == "no":
        return back_off_time
    if dic.__contains__("period") and dic.get("period") is not None:
        back_off_time = int(dic.get("period"))
        if back_off_time <= 0:
            return retry_times
    return back_off_time


def sleep(t):
    time.sleep(t)


def is_retryable(ex):
    return isinstance(ex, TeaException)


def bytes_readable(body):
    return body

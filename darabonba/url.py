import re
from urllib.parse import urlparse, urlunparse, quote

PORT_MAP = {
    "ftp": "21",
    "gopher": "70",
    "http": "80",
    "https": "443",
    "ws": "80",
    "wss": "443"
}

class Url:
    def __init__(self, url_str):
        self._url = urlparse(url_str)
    
    @staticmethod
    def new_url(url_str):
        try:
            return Url(url_str)
        except Exception as e:
            raise e
    
    def path(self):
        if not self._url.query:
            return self._url.path
        return f"{self._url.path}?{self._url.query}"
    
    def pathname(self):
        return self._url.path
    
    def protocol(self):
        return self._url.scheme
    
    def hostname(self):
        return self._url.hostname
    
    def host(self):
        if self._url.port:
            return f"{self._url.hostname}:{self._url.port}"
        return self._url.hostname
    
    def port(self):
        if self._url.port:
            return str(self._url.port)
        return PORT_MAP.get(self.protocol(), "")
    
    def hash(self):
        return self._url.fragment
    
    def search(self):
        return self._url.query
    
    def href(self):
        return urlunparse(self._url)
    
    def auth(self):
        if self._url.username or self._url.password:
            return f"{self._url.username}:{self._url.password or ''}"
        return ""
    
    @staticmethod
    def parse(url_str):
        return Url.new_url(url_str)
    
    @staticmethod
    def url_encode(url_str):
        if not url_str:
            return ""
        parts = url_str.split('/')
        encoded_parts = [quote(part, safe='') for part in parts]
        encoded_url = '/'.join(encoded_parts)
        encoded_url = encoded_url.replace("+", "%20").replace("*", "%2A").replace("%7E", "~")
        return encoded_url
    
    @staticmethod
    def percent_encode(uri):
        if not uri:
            return ""
        encoded_uri = quote(uri, safe='')
        encoded_uri = encoded_uri.replace("+", "%20").replace("*", "%2A").replace("%7E", "~")
        return encoded_uri

    @staticmethod
    def path_encode(path):
        if not path or path == "/":
            return path
        parts = path.split('/')
        encoded_parts = [quote(part, safe='') for part in parts]
        encoded_path = '/'.join(encoded_parts)
        encoded_path = encoded_path.replace("+", "%20").replace("*", "%2A").replace("%7E", "~")
        return encoded_path
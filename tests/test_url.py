import unittest
from darabonba.url import URL  # Replace 'your_module' with the name of the actual module

class TestURL(unittest.TestCase):
    
    def test_new_url(self):
        url = URL.new_url("http://example.com")
        self.assertIsNotNone(url)
        
        url = URL.new_url("invalid_url")
        self.assertIsNotNone(url)
    
    def test_path(self):
        url = URL("http://example.com/path?query=1")
        self.assertEqual(url.path(), "/path?query=1")
    
    def test_pathname(self):
        url = URL("http://example.com/path")
        self.assertEqual(url.pathname(), "/path")
    
    def test_protocol(self):
        url = URL("https://example.com")
        self.assertEqual(url.protocol(), "https")
    
    def test_hostname(self):
        url = URL("https://example.com")
        self.assertEqual(url.hostname(), "example.com")
    
    def test_host(self):
        url = URL("http://example.com:8080")
        self.assertEqual(url.host(), "example.com:8080")
        
        url = URL("http://example.com")
        self.assertEqual(url.host(), "example.com")
    
    def test_port(self):
        url = URL("http://example.com:8080")
        self.assertEqual(url.port(), "8080")
        
        url = URL("http://example.com")
        self.assertEqual(url.port(), "80")
        
        url = URL("custom://example.com")
        self.assertEqual(url.port(), "")
    
    def test_hash(self):
        url = URL("http://example.com#section")
        self.assertEqual(url.hash(), "section")
    
    def test_search(self):
        url = URL("http://example.com?query=1")
        self.assertEqual(url.search(), "query=1")
    
    def test_href(self):
        url_str = "http://example.com/path?query=1#section"
        url = URL(url_str)
        self.assertEqual(url.href(), url_str)
    
    def test_auth(self):
        url = URL("http://user:pass@example.com")
        self.assertEqual(url.auth(), "user:pass")
        
        url = URL("http://user@example.com")
        self.assertEqual(url.auth(), "user:")
        
        url = URL("http://example.com")
        self.assertEqual(url.auth(), "")
    
    def test_parse(self):
        url = URL.parse("http://example.com")
        self.assertIsNotNone(url)
    
    def test_encode_url(self):
        self.assertEqual(URL.url_encode("hello/world"), "hello/world")
        self.assertEqual(URL.url_encode("hello world"), "hello%20world")
        
    def test_percent_encode(self):
        self.assertEqual(URL.percent_encode("http://example.com/path to encode"), "http%3A%2F%2Fexample.com%2Fpath%20to%20encode")
        
    def test_path_encode(self):
        self.assertEqual(URL.path_encode("/path to encode"), "/path%20to%20encode")
        self.assertEqual(URL.path_encode("/"), "/")

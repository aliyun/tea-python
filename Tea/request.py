class TeaRequest:
    def __init__(self):
        super().__init__()
        self.query = {}
        self.headers = {}
        self.protocol = "http"
        self.port = 80
        self.method = "GET"
        self.host = ""
        self.pathname = ""
        self.body = None

    def set_host(self, host):
        """ Sets the 'host' property. """
        self.host = host
        self.headers['host'] = host

    def set_method(self, method):
        """ Sets the 'method' property. """
        self.method = method.upper()

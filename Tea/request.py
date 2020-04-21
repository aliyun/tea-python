class TeaRequest:
    def __init__(self):
        self.query = {}
        self.protocol = "http"
        self.port = 80
        self.method = "GET"
        self.headers = {}
        self.pathname = ""
        self.body = None


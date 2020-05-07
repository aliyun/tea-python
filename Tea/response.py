class TeaResponse:
    def __init__(self, response):
        self.status_code = response.status_code
        self.status_message = response.reason
        self.headers = response.headers
        self.response = response
        self.body = response.content

class TeaResponse:
    def __init__(self, response):
        super().__init__()
        self.status_code = response.status_code
        self.status_message = response.status_description
        self.headers = response.headers
        self.response = response
        self.body = response.content

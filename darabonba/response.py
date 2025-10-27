from typing import Any, Dict, Optional, Union
from aiohttp import ClientResponse

class DaraResponse:
    def __init__(self):
        # status
        self.status_code: Optional[int] = None
        # reason
        self.status_message: Optional[str] = None
        self.headers: Optional[Dict[str, str]] = None
        self.response: Optional[Union[ClientResponse, Any]] = None
        self.body: Optional[Union[bytes, Any]] = None
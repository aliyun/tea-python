import unittest
import re

from Tea.model import TeaModel


class TestTeaModel(unittest.TestCase):
    class TestRegModel(TeaModel):
        def __init__(self):
            super().__init__()
            self.requestId = "requestID"
            self.items = []
            self.nextMarker = "next"
            self.testNoAttr = "noAttr"
            self.subModel = None
            self.testListStr = ["str", "test"]
            self._names["requestId"] = "RequestId"

    class TestRegSubModel(TeaModel):
        def __init__(self):
            super().__init__()
            self.requestId = "subRequestID"
            self.testInt = 1
            self.test_dict = {'a': 1, 'b': {
                'a': 1, 'b': 2, 'c': '3'}, 'c': '3'}

    class TestModel(TeaModel):
        def __init__(self):
            super().__init__()
            self.a = "a"
            self._names["a"] = "A"
            self.b = "b"
            self.c = "c"
            self.d = 0
            self.d = 1
            self.e = None
            self.f = ""
            self.requestId = "requestId"
            self._validations["e"] = {"required": True}
            self._validations["f"] = {"required": True}
            self._validations["requestId"] = {
                "required": True, "maxLength": 100, "pattern": re.compile(r'\d+')}

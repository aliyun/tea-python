import unittest
import re

from Tea.model import TeaModel
from Tea.exceptions import RequiredArgumentException


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

    def test_to_map(self):
        reg_model = TestTeaModel.TestRegModel()
        list_sub_model = TestTeaModel.TestRegSubModel()
        list_sub_model.requestId = "list subModel"
        reg_model.items.append(list_sub_model)
        reg_model.items.append(None)
        reg_model.subModel = TestTeaModel.TestRegSubModel()
        self.assertEqual({'items': [{'requestId': 'list subModel', 'testInt': 1, 'test_dict': {'a': 1, 'b': {'a': 1, 'b': 2, 'c': '3'}, 'c': '3'}}, None], 'nextMarker': 'next', 'RequestId': 'requestID', 'subModel': {
                         'requestId': 'subRequestID', 'testInt': 1, 'test_dict': {'a': 1, 'b': {'a': 1, 'b': 2, 'c': '3'}, 'c': '3'}}, 'testListStr': ['str', 'test'], 'testNoAttr': 'noAttr'}, reg_model.to_map())

    def test_validate(self):
        model = TestTeaModel.TestModel()
        self.assertRaises(RequiredArgumentException, model.validate)
        model.e = "e"
        self.assertRaises(RequiredArgumentException, model.validate)
        model.f = "f"

        try:
            # no exception
            model.validate()
        except RequiredArgumentException:
            self.fail("model.validate() raised ExceptionType unexpectedly!")

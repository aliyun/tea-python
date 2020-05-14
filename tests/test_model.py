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

    def test_validate_required(self):
        tm = TeaModel()
        n = tm.validate_required('test', 'prop_name')
        self.assertIsNone(n)
        self.assertRaises(Exception, tm.validate_required, prop=None, prop_name='None')

    def test_validate_max_length(self):
        tm = TeaModel()
        tm.validate_max_length('test', 'prop_name', 10)
        self.assertRaises(Exception, tm.validate_max_length,
                          prop='test', prop_name='prop_name', max_length=1)

    def test_validate_min_length(self):
        tm = TeaModel()
        tm.validate_min_length('test', 'prop_name', 1)
        self.assertRaises(Exception, tm.validate_min_length,
                          prop='test', prop_name='prop_name', min_length=10)

    def test_validate_pattern(self):
        tm = TeaModel()
        tm.validate_pattern('test', 'prop_name', 't')
        self.assertRaises(Exception, tm.validate_pattern,
                          prop='test', prop_name='prop_name', pattern='q')

    def test_validate_maximum(self):
        tm = TeaModel()
        tm.validate_maximum(1, 10)
        self.assertRaises(Exception, tm.validate_maximum,
                          num=10, maximum=1)

    def test_validate_minimum(self):
        tm = TeaModel()
        tm.validate_minimum(10, 1)
        self.assertRaises(Exception, tm.validate_minimum,
                          num=1, minimum=10)
import unittest
import re

from alibabacloud_tea_sse.model import TeaModel


class TestTeaModel(unittest.TestCase):
    class TestRegModel(TeaModel):
        def __init__(self):
            self.requestId = "requestID"
            self.items = []
            self.nextMarker = "next"
            self.testNoAttr = "noAttr"
            self.subModel = None
            self.testListStr = ["str", "test"]

        def to_map(self):
            result = {}
            result['requestId'] = self.requestId
            result['items'] = self.items
            result['nextMarker'] = self.nextMarker
            result['testNoAttr'] = self.testNoAttr
            result['subModel'] = self.subModel
            result['testListStr'] = self.testListStr
            return result

    class TestRegSubModel(TeaModel):
        def __init__(self):
            self.requestId = "subRequestID"
            self.testInt = 1
            self.test_dict = {'a': 1, 'b': {
                'a': 1, 'b': 2, 'c': '3'}, 'c': '3'}

    class TestModel(TeaModel):
        def __init__(self):
            self.a = "a"
            self.b = "b"
            self.c = "c"
            self.d = 0
            self.d = 1
            self.e = None
            self.f = ""
            self.requestId = "requestId"

    def test_validate_required(self):
        tm = TeaModel()
        tm.validate()
        tm.to_map()
        tm.from_map()

        n = tm.validate_required('test', 'prop_name')
        self.assertIsNone(n)

        try:
            tm.validate_required(None, 'prop_name')
            assert False
        except Exception as e:
            self.assertEqual('"prop_name" is required.', str(e))

    def test_validate_max_length(self):
        tm = TeaModel()
        tm.validate_max_length('test', 'prop_name', 10)

        try:
            tm.validate_max_length('test', 'prop_name', 1)
            assert False
        except Exception as e:
            self.assertEqual('prop_name is exceed max-length: 1', str(e))

    def test_validate_min_length(self):
        tm = TeaModel()
        tm.validate_min_length('test', 'prop_name', 1)

        try:
            tm.validate_min_length('test', 'prop_name', 10)
            assert False
        except Exception as e:
            self.assertEqual('prop_name is less than min-length: 10', str(e))

    def test_validate_pattern(self):
        tm = TeaModel()
        tm.validate_pattern('test', 'prop_name', 't')

        tm.validate_pattern(123.1, 'prop_name', '1')

        try:
            tm.validate_pattern('test', 'prop_name', '1')
            assert False
        except Exception as e:
            self.assertEqual('prop_name is not match: 1', str(e))

    def test_validate_maximum(self):
        tm = TeaModel()
        tm.validate_maximum(1, 'count', 10)

        try:
            tm.validate_maximum(10, 'count', 1)
            assert False
        except Exception as e:
            self.assertEqual('count is greater than the maximum: 1', str(e))

    def test_validate_minimum(self):
        tm = TeaModel()
        tm.validate_minimum(10, 'count', 1)

        try:
            tm.validate_minimum(1, 'count', 10,)
            assert False
        except Exception as e:
            self.assertEqual('count is less than the minimum: 10', str(e))

    def test_str(self):
        model = str(self.TestRegModel())
        tm = str(TeaModel())
        self.assertTrue(model.startswith('{\''))
        self.assertTrue(model.endswith('}'))
        self.assertTrue(tm.startswith('<alibabacloud_tea_sse.model.TeaModel object'))

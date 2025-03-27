import unittest
from darabonba.model import DaraModel

class TestDaraModel(unittest.TestCase):
    class TestRegModel(DaraModel):
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

    class TestRegSubModel(DaraModel):
        def __init__(self):
            self.requestId = "subRequestID"
            self.testInt = 1
            self.test_dict = {'a': 1, 'b': {
                'a': 1, 'b': 2, 'c': '3'}, 'c': '3'}

    class TestModel(DaraModel):
        def __init__(self):
            self.a = "a"
            self.b = "b"
            self.c = "c"
            self.d = 0
            self.e = None
            self.f = ""

    def test_validate_required(self):
        tm = DaraModel()
        tm.validate()
        tm.to_map()
        tm.from_map()

        n = tm.validate_required('test', 'prop_name')
        self.assertIsNone(n)

        with self.assertRaises(Exception) as context:
            tm.validate_required(None, 'prop_name')
        self.assertEqual('"prop_name" is required.', str(context.exception))

    def test_validate_max_length(self):
        tm = DaraModel()
        tm.validate_max_length('test', 'prop_name', 10)

        with self.assertRaises(Exception) as context:
            tm.validate_max_length('test', 'prop_name', 1)
        self.assertEqual('prop_name is exceed max-length: 1', str(context.exception))

    def test_validate_min_length(self):
        tm = DaraModel()
        tm.validate_min_length('test', 'prop_name', 1)

        with self.assertRaises(Exception) as context:
            tm.validate_min_length('test', 'prop_name', 10)
        self.assertEqual('prop_name is less than min-length: 10', str(context.exception))

    def test_validate_pattern(self):
        tm = DaraModel()
        tm.validate_pattern('test', 'prop_name', 't')

        tm.validate_pattern(123.1, 'prop_name', '1')

        with self.assertRaises(Exception) as context:
            tm.validate_pattern('test', 'prop_name', '1')
        self.assertEqual('prop_name is not match: 1', str(context.exception))

    def test_validate_maximum(self):
        tm = DaraModel()
        tm.validate_maximum(1, 'count', 10)

        with self.assertRaises(Exception) as context:
            tm.validate_maximum(10, 'count', 1)
        self.assertEqual('count is greater than the maximum: 1', str(context.exception))

    def test_validate_minimum(self):
        tm = DaraModel()
        tm.validate_minimum(10, 'count', 1)

        with self.assertRaises(Exception) as context:
            tm.validate_minimum(1, 'count', 10)
        self.assertEqual('count is less than the minimum: 10', str(context.exception))

    def test_str(self):
        model = str(self.TestRegModel())
        tm = str(DaraModel())
        self.assertTrue(model.startswith('{\''))
        self.assertTrue(model.endswith('}'))
        self.assertTrue(tm.startswith('<darabonba.model.DaraModel object'))

    def test_to_map(self):
        test_reg_model = self.TestRegModel()
        self.assertDictEqual(test_reg_model.to_map(), {
            'requestId': "requestID",
            'items': [],
            'nextMarker': "next",
            'testNoAttr': "noAttr",
            'subModel': None,
            'testListStr': ["str", "test"]
        })
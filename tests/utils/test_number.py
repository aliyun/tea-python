import unittest
from darabonba.number import Number

class TestNumber(unittest.TestCase):

    def test_initialization_with_int(self):
        num = Number(10)
        self.assertEqual(num.value, 10.0)

    def test_initialization_with_float(self):
        num = Number(10.5)
        self.assertEqual(num.value, 10.5)

    def test_initialization_with_bool_true(self):
        num = Number(True)
        self.assertEqual(num.value, 1.0)

    def test_initialization_with_bool_false(self):
        num = Number(False)
        self.assertEqual(num.value, 0.0)

    def test_initialization_with_none(self):
        num = Number(None)
        self.assertEqual(num.value, 0.0)

    def test_initialization_with_string_number(self):
        num = Number("123.45")
        self.assertEqual(num.value, 123.45)

    def test_initialization_with_string_invalid(self):
        num = Number("invalid")
        self.assertTrue(isnan(num.value))

    def test_initialization_with_empty_string(self):
        num = Number("")
        self.assertTrue(isnan(num.value))

    def test_initialization_with_list(self):
        num = Number([1, 2, 3])
        self.assertTrue(isnan(num.value))

    def test_initialization_with_dict(self):
        num = Number({"key": "value"})
        self.assertTrue(isnan(num.value))

    def test_str_method(self):
        num = Number(25)
        self.assertEqual(str(num), "25.0")
        
        num = Number("not a number")
        self.assertTrue("nan" in str(num).lower())

def isnan(value):
    """Helper function to check if a value is NaN"""
    try:
        import math
        return math.isnan(value)
    except AttributeError:
        return value != value  # NaN is the only value not equal to itself
import unittest
from darabonba.utils.validation import assert_integer_positive, validate_pattern, is_null
from darabonba.exceptions import ValidateException


class TestValidation(unittest.TestCase):

    def test_assert_integer_positive(self):
        self.assertIsNone(assert_integer_positive(5, "test_param"))
        
        with self.assertRaises(ValidateException) as context:
            assert_integer_positive(-5, "test_param")
        self.assertEqual(str(context.exception), "test_param should be a positive integer.")
        
        with self.assertRaises(ValidateException) as context:
            assert_integer_positive("5", "test_param")
        self.assertEqual(str(context.exception), "test_param should be a positive integer.")

    def test_validate_pattern(self):
        self.assertIsNone(validate_pattern("abc123", "test_param", r"\d+"))
        
        with self.assertRaises(ValidateException) as context:
            validate_pattern("abcdef", "test_param", r"\d+")
        self.assertEqual(str(context.exception), "The parameter test_param not match with \\d+")

    def test_is_null(self):
        with self.assertRaises(ValidateException) as context:
            is_null(None, "test_param")
        self.assertEqual(str(context.exception), "The parameter test_param should not be null.")
        
        self.assertIsNone(is_null("not_none", "test_param"))

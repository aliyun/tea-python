import unittest
import json
from darabonba.utils.array import List  # Replace 'yourmodule' with the actual module name

class TestListToJson(unittest.TestCase):
    
    def test_to_json_with_valid_list(self):
        input_array = [1, 2, 3]
        expected_output = json.dumps(input_array)
        result = List.to_json(input_array)
        self.assertEqual(result, expected_output, "Should convert list to JSON string correctly.")

    def test_to_json_with_non_list(self):
        input_values = [
            "string",
            123,
            123.456,
            {"key": "value"},
            (1, 2),
            {1, 2}
        ]
        
        for input_value in input_values:
            result = List.to_json(input_value)
            self.assertTrue(result.startswith("TypeError"), "Should return TypeError message for non-list inputs.")
    
    def test_to_json_with_empty_list(self):
        input_array = []
        expected_output = json.dumps(input_array)
        result = List.to_json(input_array)
        self.assertEqual(result, expected_output, "Should correctly handle an empty list.")

    def test_to_json_with_nested_list(self):
        input_array = [[1, 2], [3, 4], ['a', 'b']]
        expected_output = json.dumps(input_array)
        result = List.to_json(input_array)
        self.assertEqual(result, expected_output, "Should correctly convert nested lists to JSON string.")

    def test_to_json_with_special_characters(self):
        input_array = ["hello\nworld", "foo\tbar", "baz\"qux"]
        expected_output = json.dumps(input_array)
        result = List.to_json(input_array)
        self.assertEqual(result, expected_output, "Should handle special characters correctly.")
        
    def test_to_json_with_mixed_data_types(self):
        input_array = [1, "string", 3.5, None, True, {"key": "value"}, [1, 2]]
        expected_output = json.dumps(input_array)
        result = List.to_json(input_array)
        self.assertEqual(result, expected_output, "Should handle lists with mixed data types correctly.")

if __name__ == '__main__':
    unittest.main()

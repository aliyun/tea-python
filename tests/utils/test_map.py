import unittest
import json
from darabonba.utils.map import Map 

class TestMap(unittest.TestCase):
    def setUp(self):
        # Called before each testing method to build a testing environment
        self.sample_data = {"key": "value"}
        self.map_instance = Map(self.sample_data)

    def test_initialization(self):
        # Test whether the initialization is correct
        self.assertEqual(self.map_instance.data, self.sample_data)

    def test_to_json_success(self):
        # Test the functionality of to_json method
        json_str = Map.to_json(self.map_instance)
        expected_json_str = json.dumps(self.sample_data)
        self.assertEqual(json_str, expected_json_str)

    def test_to_json_invalid_instance(self):
        # Test whether ValueError is thrown when passing in non Map instances
        with self.assertRaises(ValueError):
            Map.to_json("not a map instance")

    def test_to_json_serialization_error(self):
        # Test whether serialization errors are captured and throw exceptions
        map_instance_with_invalid_data = Map({"key": set([1, 2, 3])})
        with self.assertRaises(Exception) as context:
            Map.to_json(map_instance_with_invalid_data)
        self.assertIn("Serialization error", str(context.exception))

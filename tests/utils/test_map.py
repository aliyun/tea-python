import unittest
import json
from darabonba.utils.map import Map 

class TestMap(unittest.TestCase):
    def setUp(self):
        # 在每个测试方法前被调用，用来构建测试环境
        self.sample_data = {"key": "value"}
        self.map_instance = Map(self.sample_data)

    def test_initialization(self):
        # 测试初始化是否正确
        self.assertEqual(self.map_instance.data, self.sample_data)

    def test_to_json_success(self):
        # 测试to_json方法功能
        json_str = Map.to_json(self.map_instance)
        expected_json_str = json.dumps(self.sample_data)
        self.assertEqual(json_str, expected_json_str)

    def test_to_json_invalid_instance(self):
        # 测试传入非Map实例时是否抛出ValueError
        with self.assertRaises(ValueError):
            Map.to_json("not a map instance")

    def test_to_json_serialization_error(self):
        # 测试序列化错误是否被捕获并抛出异常
        map_instance_with_invalid_data = Map({"key": set([1, 2, 3])})
        with self.assertRaises(Exception) as context:
            Map.to_json(map_instance_with_invalid_data)
        self.assertIn("Serialization error", str(context.exception))

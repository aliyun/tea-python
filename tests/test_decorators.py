import unittest
import asyncio

from darabonba.decorators import deprecated, type_check


class TestDecorators(unittest.TestCase):
    def test_deprecated_function(self):
        @deprecated("Use 'new_function' instead")
        def old_function():
            return "old_function"

        with self.assertWarns(DeprecationWarning) as cm:
            result = old_function()

        self.assertEqual(result, "old_function")
        self.assertIn("Call to deprecated function old_function. Use 'new_function' instead", str(cm.warning))

        @deprecated("Use 'new_function_async' instead")
        async def old_function_async():
            return "old_function_async"

        with self.assertWarns(DeprecationWarning) as cm:
            loop = asyncio.get_event_loop()
            task = asyncio.ensure_future(old_function_async())
            loop.run_until_complete(task)
            result = task.result()

        self.assertEqual(result, "old_function_async")
        self.assertIn("Call to deprecated function old_function_async. Use 'new_function_async' instead", str(cm.warning))

    def test_deprecated_static_method(self):
        class MyClass:
            @deprecated("Use 'new_static_method' instead")
            @staticmethod
            def old_static_method():
                return "old_static_method"

            @deprecated("Use 'new_static_method_async' instead")
            @staticmethod
            async def old_static_method_async():
                return "old_static_method_async"

        with self.assertWarns(DeprecationWarning) as cm:
            result = MyClass.old_static_method()

        self.assertEqual(result, "old_static_method")
        self.assertIn("Call to deprecated function old_static_method. Use 'new_static_method' instead", str(cm.warning))

        with self.assertWarns(DeprecationWarning) as cm:
            loop = asyncio.get_event_loop()
            task = asyncio.ensure_future(MyClass.old_static_method_async())
            loop.run_until_complete(task)
            result = task.result()
        self.assertEqual(result, "old_static_method_async")
        self.assertIn("Call to deprecated function old_static_method_async. Use 'new_static_method_async' instead", str(cm.warning))

    def test_deprecated_class_method(self):
        class MyClass:
            @deprecated("Use 'new_class_method' instead")
            @classmethod
            def old_class_method(cls):
                return "old_class_method"

            @deprecated("Use 'new_class_method_async' instead")
            @classmethod
            async def old_class_method_async(cls):
                return "old_class_method_async"

        with self.assertWarns(DeprecationWarning) as cm:
            result = MyClass.old_class_method()

        self.assertEqual(result, "old_class_method")
        self.assertIn("Call to deprecated function old_class_method. Use 'new_class_method' instead", str(cm.warning))

        with self.assertWarns(DeprecationWarning) as cm:
            loop = asyncio.get_event_loop()
            task = asyncio.ensure_future(MyClass.old_class_method_async())
            loop.run_until_complete(task)
            result = task.result()
        self.assertEqual(result, "old_class_method_async")
        self.assertIn("Call to deprecated function old_class_method_async. Use 'new_class_method_async' instead", str(cm.warning))

    def test_deprecated_instance_method(self):
        class MyClass:
            @deprecated("Use 'new_instance_method' instead")
            def old_instance_method(self):
                return "old_instance_method"

            @deprecated("Use 'new_instance_method_async' instead")
            async def old_instance_method_async(self):
                return "old_instance_method_async"

        instance = MyClass()

        with self.assertWarns(DeprecationWarning) as cm:
            result = instance.old_instance_method()

        self.assertEqual(result, "old_instance_method")
        self.assertIn("Call to deprecated function old_instance_method. Use 'new_instance_method' instead", str(cm.warning))

        with self.assertWarns(DeprecationWarning) as cm:
            loop = asyncio.get_event_loop()
            task = asyncio.ensure_future(instance.old_instance_method_async())
            loop.run_until_complete(task)
            result = task.result()
        self.assertEqual(result, "old_instance_method_async")
        self.assertIn("Call to deprecated function old_instance_method_async. Use 'new_instance_method_async' instead", str(cm.warning))

    def test_type_check_function(self):
        @type_check(int, str, z=str)
        def example_function(x, y, z="default"):
            return f"x: {x}, y: {y}, z: {z}"

        with self.assertWarns(UserWarning) as cm:
            result = example_function('test', 123)

        self.assertEqual(result, "x: test, y: 123, z: default")
        self.assertIn("Argument 0 is not of type <class 'int'>", str(cm.warning))

        result = example_function(10, 'test', z='example')
        self.assertEqual(result, "x: 10, y: test, z: example")

        @type_check(int, str, z=str)
        async def example_function_async(x, y, z="default"):
            return f"x: {x}, y: {y}, z: {z}"

        with self.assertWarns(UserWarning) as cm:
            loop = asyncio.get_event_loop()
            task = asyncio.ensure_future(example_function_async('test', 123))
            loop.run_until_complete(task)
            result = task.result()

        self.assertEqual(result, "x: test, y: 123, z: default")
        self.assertIn("Argument 0 is not of type <class 'int'>", str(cm.warning))

        result = loop.run_until_complete(example_function_async(42, 'test', z='example'))
        self.assertEqual(result, "x: 42, y: test, z: example")
    
    def test_type_check_kwargs(self):
        @type_check(int, str, z=str)
        def example_func(x, y, z="default"):
            return f"x: {x}, y: {y}, z: {z}"

        with self.assertWarns(UserWarning) as cm:
            result = example_func(10, 'valid', z=100)
        self.assertIn("Argument z is not of type <class 'str'>", str(cm.warning))

        result = example_func(10, 'valid', z='valid')
        self.assertEqual(result, "x: 10, y: valid, z: valid")
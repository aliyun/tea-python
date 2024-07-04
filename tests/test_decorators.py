import unittest
import warnings
import asyncio

from Tea.decorators import deprecated


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
            task = asyncio.ensure_future(
                old_function_async()
            )
            loop.run_until_complete(task)
            result = task.result()

        self.assertEqual(result, "old_function_async")
        self.assertIn("Call to deprecated function old_function_async. Use 'new_function_async' instead",
                      str(cm.warning))

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
            task = asyncio.ensure_future(
                MyClass.old_static_method_async()
            )
            loop.run_until_complete(task)
            result = task.result()
        self.assertEqual(result, "old_static_method_async")
        self.assertIn("Call to deprecated function old_static_method_async. Use 'new_static_method_async' instead",
                      str(cm.warning))

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
            task = asyncio.ensure_future(
                MyClass.old_class_method_async()
            )
            loop.run_until_complete(task)
            result = task.result()
        self.assertEqual(result, "old_class_method_async")
        self.assertIn("Call to deprecated function old_class_method_async. Use 'new_class_method_async' instead",
                      str(cm.warning))

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
        self.assertIn("Call to deprecated function old_instance_method. Use 'new_instance_method' instead",
                      str(cm.warning))

        with self.assertWarns(DeprecationWarning) as cm:
            loop = asyncio.get_event_loop()
            task = asyncio.ensure_future(
                instance.old_instance_method_async()
            )
            loop.run_until_complete(task)
            result = task.result()
        self.assertEqual(result, "old_instance_method_async")
        self.assertIn("Call to deprecated function old_instance_method_async. Use 'new_instance_method_async' instead",
                      str(cm.warning))

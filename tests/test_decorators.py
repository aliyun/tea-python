import unittest
import asyncio
from darabonba.decorators import deprecated, type_check
import warnings

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
            result = asyncio.run(old_function_async())

        self.assertEqual(result, "old_function_async")
        self.assertIn(
            "Call to deprecated function old_function_async. Use 'new_function_async' instead",
            str(cm.warning)
        )

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
            result = asyncio.run(MyClass.old_static_method_async())
        
        self.assertEqual(result, "old_static_method_async")
        self.assertIn(
            "Call to deprecated function old_static_method_async. Use 'new_static_method_async' instead",
            str(cm.warning)
        )

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
            result = asyncio.run(MyClass.old_class_method_async())
        
        self.assertEqual(result, "old_class_method_async")
        self.assertIn(
            "Call to deprecated function old_class_method_async. Use 'new_class_method_async' instead",
            str(cm.warning)
        )

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
            result = asyncio.run(instance.old_instance_method_async())

        self.assertEqual(result, "old_instance_method_async")
        self.assertIn(
            "Call to deprecated function old_instance_method_async. Use 'new_instance_method_async' instead",
            str(cm.warning)
        )

class TestDeprecatedDecorator(unittest.TestCase):
    def test_deprecated(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            @deprecated("Use new_function instead.")
            def old_function():
                return "Hello, World!"

            result = old_function()
            self.assertEqual(result, "Hello, World!")
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertEqual(str(w[-1].message), "Call to deprecated function old_function. Use new_function instead.")


class TestTypeCheckDecorator(unittest.TestCase):
    def test_type_check(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            @type_check(int, str)
            def example_function(a, b):
                return f"{a} {b}"

            result = example_function(1, "two")
            self.assertEqual(result, "1 two")
            self.assertEqual(len(w), 0)

            example_function(1, 2)
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, UserWarning))
            self.assertEqual(str(w[-1].message), "Argument 1 is not of type <class 'str'>")

            example_function(a=1, b="two")
            self.assertEqual(len(w), 1)

            example_function(a=1, b=2)
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, UserWarning))


import unittest
from io import StringIO
import sys
from darabonba.utils.logger import Logger

class TestLogger(unittest.TestCase):
    def setUp(self):
        # Redirect stdout to capture print statements
        self.held_stdout = StringIO()
        sys.stdout = self.held_stdout

    def tearDown(self):
        # Restore stdout
        sys.stdout = sys.__stdout__

    def test_initial_level(self):
        # Test the initial log level
        self.assertEqual(Logger.current_level, Logger.levels['DEBUG'])

    def test_log_message(self):
        # Test logging a message
        Logger.debug("Debug message")
        self.assertIn("DEBUG: Debug message", self.held_stdout.getvalue())

    def test_info_logging(self):
        Logger.set_level("INFO")
        Logger.debug("This should not be printed")
        Logger.info("Info message")
        self.assertNotIn("DEBUG: This should not be printed", self.held_stdout.getvalue())
        self.assertIn("INFO: Info message", self.held_stdout.getvalue())
        Logger.set_level("DEBUG")

    def test_warning_logging(self):
        Logger.set_level("WARNING")
        Logger.info("This should not be printed")
        Logger.warning("Warning message")
        self.assertNotIn("INFO: This should not be printed", self.held_stdout.getvalue())
        self.assertIn("WARNING: Warning message", self.held_stdout.getvalue())
        Logger.set_level("DEBUG")

    def test_error_logging(self):
        Logger.set_level("ERROR")
        Logger.warning("This should not be printed")
        Logger.error("Error message")
        self.assertNotIn("WARNING: This should not be printed", self.held_stdout.getvalue())
        self.assertIn("ERROR: Error message", self.held_stdout.getvalue())
        Logger.set_level("DEBUG")

    def test_critical_logging(self):
        Logger.set_level("CRITICAL")
        Logger.error("This should not be printed")
        Logger.critical("Critical message")
        self.assertNotIn("ERROR: This should not be printed", self.held_stdout.getvalue())
        self.assertIn("CRITICAL: Critical message", self.held_stdout.getvalue())
        Logger.set_level("DEBUG")

    def test_set_invalid_level(self):
        with self.assertRaises(ValueError):
            Logger.set_level("INVALID")

    def test_format_change(self):
        new_format = "[{levelname}] - {message}"
        Logger.format(new_format)
        Logger.info("Formatted message")
        self.assertIn("[INFO] - Formatted message", self.held_stdout.getvalue())
        Logger.format("{levelname}: {message}")
        
    def test_default_format_unchanged(self):
        # Ensure default format remains intact on reinitializing test
        Logger.format("{levelname}: {message}")
        Logger.info("Default format message")
        self.assertIn("INFO: Default format message", self.held_stdout.getvalue())
        Logger.format("{levelname}: {message}")
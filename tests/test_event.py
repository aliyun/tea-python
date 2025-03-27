import unittest
from darabonba.event import Event
from darabonba.exceptions import RequiredArgumentException, ValidateException

class TestEvent(unittest.TestCase):
    
    def test_event_initialization(self):
        event = Event(id="123", event="test_event", data="test_data", retry=5)
        self.assertEqual(event.id, "123")
        self.assertEqual(event.event, "test_event")
        self.assertEqual(event.data, "test_data")
        self.assertEqual(event.retry, 5)

    def test_event_validation(self):
        event = Event(id="123", event="test_event", data="test_data", retry=5)
        try:
            event.validate()  # Should not raise any exception
        except Exception as e:
            self.fail(f"validate raised {type(e).__name__} unexpectedly!")

        # Test with missing required fields
        event_missing_id = Event(event="test_event", data="test_data", retry=5)
        with self.assertRaises(RequiredArgumentException) as context:
            event_missing_id.validate()
        self.assertEqual(str(context.exception), "\"id\" is required.")

        event_missing_event = Event(id="123", data="test_data", retry=5)
        with self.assertRaises(RequiredArgumentException) as context:
            event_missing_event.validate()
        self.assertEqual(str(context.exception), "\"event\" is required.")

        event_missing_data = Event(id="123", event="test_event", retry=5)
        with self.assertRaises(RequiredArgumentException) as context:
            event_missing_data.validate()
        self.assertEqual(str(context.exception), "\"data\" is required.")

        event_missing_retry = Event(id="123", event="test_event", data="test_data")
        with self.assertRaises(RequiredArgumentException) as context:
            event_missing_retry.validate()
        self.assertEqual(str(context.exception), "\"retry\" is required.")

    def test_to_map(self):
        event = Event(id="123", event="test_event", data="test_data", retry=5)
        expected_map = {
            'id': "123",
            'event': "test_event",
            'data': "test_data",
            'retry': 5
        }
        self.assertEqual(event.to_map(), expected_map)

        # Test with None values
        event_partial = Event(id="123")
        expected_partial_map = {
            'id': "123"
        }
        self.assertEqual(event_partial.to_map(), expected_partial_map)

    def test_from_map(self):
        map_data = {
            'id': "123",
            'event': "test_event",
            'data': "test_data",
            'retry': 5
        }
        event = Event()
        event.from_map(map_data)
        self.assertEqual(event.id, "123")
        self.assertEqual(event.event, "test_event")
        self.assertEqual(event.data, "test_data")
        self.assertEqual(event.retry, 5)

        event_empty = Event()
        event_empty.from_map({})
        self.assertIsNone(event_empty.id)
        self.assertIsNone(event_empty.event)
        self.assertIsNone(event_empty.data)
        self.assertIsNone(event_empty.retry)
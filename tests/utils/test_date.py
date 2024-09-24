import unittest
from datetime import datetime, timedelta
from darabonba.utils.date import Date  # 替换 your_module_name 为实际模块名

class TestDate(unittest.TestCase):

    def test_init_valid_formats(self):
        self.assertIsInstance(Date("2023-10-01 12:30:00").date, datetime)
        self.assertIsInstance(Date("2023-10-01 12:30:00.123456 +0000 UTC").date, datetime)
        self.assertIsInstance(Date("2023-10-01T12:30:00+0000").date, datetime)
        self.assertIsInstance(Date("2023-10-01T12:30:00Z").date, datetime)
    
    def test_init_invalid_format(self):
        with self.assertRaises(ValueError):
            Date("invalid date string")
    
    def test_format(self):
        d = Date("2023-10-01 12:30:00")
        self.assertEqual(d.format("yyyy-MM-dd hh:mm:ss"), "2023-10-01 12:30:00")
        self.assertEqual(d.format("dd/MM/yyyy hh:mm:ss a"), "01/10/2023 12:30:00 PM")
    
    def test_unix(self):
        d = Date("2023-10-01 12:30:00")
        expected_timestamp = int(datetime.strptime("2023-10-01 12:30:00", "%Y-%m-%d %H:%M:%S").timestamp())
        self.assertEqual(d.unix(), expected_timestamp)
    
    def test_utc(self):
        d = Date("2023-10-01 12:30:00")
        expected_utc = datetime.strptime("2023-10-01 12:30:00", "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S.%f %z %Z")
        self.assertEqual(d.utc(), expected_utc)
    
    def test_sub(self):
        d = Date("2023-10-01 12:30:00")
        self.assertEqual(d.sub(1, "day").date.date(), datetime.strptime("2023-09-30", "%Y-%m-%d").date())
    
    def test_add(self):
        d = Date("2023-10-01 12:30:00")
        self.assertEqual(d.add(1, "day").date.date(), datetime.strptime("2023-10-02", "%Y-%m-%d").date())
    
    def test_diff(self):
        d1 = Date("2023-10-01 12:30:00")
        d2 = Date("2023-10-02 12:30:00")

        self.assertEqual(d1.diff("day", d2), -1)
    
    def test_hour(self):
        d = Date("2023-10-01 12:30:00")
        self.assertEqual(d.hour(), 12)
    
    def test_minute(self):
        d = Date("2023-10-01 12:30:00")
        self.assertEqual(d.minute(), 30)
    
    def test_second(self):
        d = Date("2023-10-01 12:30:00")
        self.assertEqual(d.second(), 0)
    
    def test_month(self):
        d = Date("2023-10-01 12:30:00")
        self.assertEqual(d.month(), 10)
    
    def test_year(self):
        d = Date("2023-10-01 12:30:00")
        self.assertEqual(d.year(), 2023)
    
    def test_day_of_month(self):
        d = Date("2023-10-01 12:30:00")
        self.assertEqual(d.day_of_month(), 1)
    
    def test_day_of_week(self):
        d = Date("2023-10-01 12:30:00")
        self.assertEqual(d.day_of_week(), 7)  # Should be Sunday
    
    def test_week_of_year(self):
        d = Date("2023-10-01 12:30:00")
        self.assertEqual(d.week_of_year(), 39)  # Depending on the year, this might change
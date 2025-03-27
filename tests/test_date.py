import unittest
from datetime import datetime
from darabonba.date import Date

class TestDate(unittest.TestCase):

    def test_init_valid_formats(self):
        self.assertIsInstance(Date("2023-10-01 12:30:00").date, datetime)
        self.assertIsInstance(Date("2023-10-01 12:30:00.123456 +0000 UTC").date, datetime)
        self.assertIsInstance(Date("2023-10-01T12:30:00+0000").date, datetime)
        self.assertIsInstance(Date("2023-10-01T12:30:00Z").date, datetime)
    
    def test_init_invalid_format(self):
        with self.assertRaises(ValueError):
            Date("invalid date string")
    
    def test_strftime(self):
        d = Date("2023-10-01 12:30:00")
        self.assertEqual(d.strftime("yyyy-MM-dd hh:mm:ss"), "2023-10-01 12:30:00")
        self.assertEqual(d.strftime("dd/MM/yyyy hh:mm:ss a"), "01/10/2023 12:30:00 PM")

    def test_timestamp(self):
        d = Date("2023-10-01 12:30:00")
        expected_timestamp = int(datetime.strptime("2023-10-01 12:30:00", "%Y-%m-%d %H:%M:%S").timestamp())
        self.assertEqual(d.timestamp(), expected_timestamp)
    
    def test_utc(self):
        d = Date("2023-10-01 12:30:00")
        expected_utc = datetime.strptime("2023-10-01 12:30:00", "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S.%f %z %Z")
        self.assertEqual(d.UTC(), expected_utc)
    
    def test_sub(self):
        d = Date("2023-10-01 12:30:00")
        self.assertEqual(d.sub("day", 1).date.date(), datetime.strptime("2023-09-30", "%Y-%m-%d").date())
        self.assertEqual(d.sub("hour", 1).date.hour, 11)  # 1 hour subtracted
    
    def test_add(self):
        d = Date("2023-10-01 12:30:00")
        self.assertEqual(d.add("day", 1).date.date(), datetime.strptime("2023-10-02", "%Y-%m-%d").date())
        self.assertEqual(d.add("hour", 1).date.hour, 13)  # 1 hour added

    def test_diff(self):
        d1 = Date("2023-10-01 12:30:00")
        d2 = Date("2023-10-02 12:30:00")

        self.assertEqual(d1.diff("day", d2), -1)
        self.assertEqual(d2.diff("day", d1), 1)  # 反向检查
    
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
        self.assertEqual(d.day_of_week(), 7)
    
    def test_week_of_year(self):
        d = Date("2023-10-01 12:30:00")
        self.assertEqual(d.week_of_year(), 39)
    
    def test_leap_year(self):
        d = Date("2024-02-29 12:30:00")
        self.assertEqual(d.year(), 2024)
        self.assertEqual(d.day_of_month(), 29)

    def test_month_boundary(self):
        d = Date("2023-01-31 12:30:00")
        d_next_month = d.add("month", 1)
        self.assertEqual(d_next_month.date, Date("2023-02-28 12:30:00").date)

    def test_subtract_cross_year(self):
        d1 = Date("2023-01-01 12:30:00")
        d2 = Date("2024-01-01 12:30:00")
        self.assertEqual(d2.diff("year", d1), 1)

    def test_add_cross_year(self):
        d1 = Date("2023-12-31 12:30:00")
        d2 = d1.add("year", 1)
        self.assertEqual(d2.year(), 2024)

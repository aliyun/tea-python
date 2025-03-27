import unittest
from datetime import datetime
from darabonba.date import Date

class TestDate(unittest.TestCase):
    def setUp(self):
        self.date1 = Date("2023-10-10 10:00:00")
        self.date2 = Date("2023-10-05 09:30:00")
        self.date = Date("2023-10-10 10:00:00")

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
        test_cases = [
            ("seconds", 10, "2023-10-10 09:59:50"),
            ("minutes", 5, "2023-10-10 09:55:00"),
            ("hours", 2, "2023-10-10 08:00:00"),
            ("days", 3, "2023-10-07 10:00:00"),
            ("weeks", 1, "2023-10-03 10:00:00"),
            ("months", 1, "2023-09-10 10:00:00"),
            ("years", 1, "2022-10-10 10:00:00"),
        ]

        for unit, amount, expected in test_cases:
            with self.subTest(unit=unit, amount=amount):
                new_date = self.date.sub(unit, amount)
                self.assertEqual(new_date.strftime("%Y-%m-%d %H:%M:%S"), expected)
    
    def test_add(self):
        test_cases = [
            ("seconds", 10, "2023-10-10 10:00:10"),
            ("minutes", 5, "2023-10-10 10:05:00"),
            ("hours", 2, "2023-10-10 12:00:00"),
            ("days", 3, "2023-10-13 10:00:00"),
            ("weeks", 1, "2023-10-17 10:00:00"),
            ("months", 1, "2023-11-10 10:00:00"),
            ("years", 1, "2024-10-10 10:00:00"),
        ]

        for unit, amount, expected in test_cases:
            with self.subTest(unit=unit, amount=amount):
                new_date = self.date.add(unit, amount)
                self.assertEqual(new_date.strftime("%Y-%m-%d %H:%M:%S"), expected)

    def test_diff(self):
        test_cases = [
            ("seconds", 20, "2023-10-10 10:00:00", "2023-10-10 09:59:40",
             20),  # 20 seconds difference
            ("minutes", 40, "2023-10-10 10:00:00", "2023-10-10 09:20:00",
             40),  # 40 minutes difference
            ("hours", 24, "2023-10-10 10:00:00", "2023-10-09 10:00:00",
             24),  # 24 hours difference
            ("days", 5, "2023-10-10 10:00:00", "2023-10-05 10:00:00",
             5),  # 5 days difference
            ("weeks", 1, "2023-10-10 10:00:00", "2023-10-03 10:00:00",
             1),  # 1 week difference
            ("months", 5, "2023-10-10 10:00:00", "2023-05-10 10:00:00",
             5),  # 5 months difference
            ("years", 1, "2023-10-10 10:00:00", "2022-10-10 10:00:00",
             1),  # 1 year difference
        ]

        for unit, expected_diff, base_date_str, compare_date_str, expected in test_cases:
            with self.subTest(unit=unit):
                compare_date = Date(compare_date_str)
                diff_result = self.date1.diff(unit, compare_date)
                self.assertEqual(diff_result, expected)
    
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

from datetime import datetime, timedelta

class Date:
    def __init__(self, date_input):
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f %z %Z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S"
        ]
        
        self.date = None
        for format in formats:
            try:
                self.date = datetime.strptime(date_input, format)
                break
            except ValueError:
                continue
        
        if self.date is None:
            raise ValueError(f"unable to parse date: {date_input}")

    def format(self, layout):
        layout = layout.replace("yyyy", "%Y")
        layout = layout.replace("MM", "%m")
        layout = layout.replace("dd", "%d")
        layout = layout.replace("hh", "%H")
        layout = layout.replace("mm", "%M")
        layout = layout.replace("ss", "%S")
        layout = layout.replace("a", "%p")
        layout = layout.replace("EEEE", "%A")
        layout = layout.replace("E", "%a")
        
        return self.date.strftime(layout)
    
    def unix(self):
        return int(self.date.timestamp())
    
    def utc(self):
        return self.date.strftime("%Y-%m-%d %H:%M:%S.%f %z %Z")
    
    def sub(self, amount, unit):
        if unit in ["second", "seconds"]:
            return Date((self.date - timedelta(seconds=amount)).isoformat())
        elif unit in ["minute", "minutes"]:
            return Date((self.date - timedelta(minutes=amount)).isoformat())
        elif unit in ["hour", "hours"]:
            return Date((self.date - timedelta(hours=amount)).isoformat())
        elif unit in ["day", "days"]:
            return Date((self.date - timedelta(days=amount)).isoformat())
        elif unit in ["week", "weeks"]:
            return Date((self.date - timedelta(weeks=amount)).isoformat())
        elif unit in ["month", "months"]:
            return Date((self.date.replace(month=self.date.month - amount)).isoformat())
        elif unit in ["year", "years"]:
            return Date((self.date.replace(year=self.date.year - amount)).isoformat())
    
    def add(self, amount, unit):
        if unit in ["second", "seconds"]:
            return Date((self.date + timedelta(seconds=amount)).isoformat())
        elif unit in ["minute", "minutes"]:
            return Date((self.date + timedelta(minutes=amount)).isoformat())
        elif unit in ["hour", "hours"]:
            return Date((self.date + timedelta(hours=amount)).isoformat())
        elif unit in ["day", "days"]:
            return Date((self.date + timedelta(days=amount)).isoformat())
        elif unit in ["week", "weeks"]:
            return Date((self.date + timedelta(weeks=amount)).isoformat())
        elif unit in ["month", "months"]:
            return Date((self.date.replace(month=self.date.month + amount)).isoformat())
        elif unit in ["year", "years"]:
            return Date((self.date.replace(year=self.date.year + amount)).isoformat())
    
    def diff(self, amount, diff_date):
        if amount in ["second", "seconds"]:
            return int((self.date - diff_date.date).total_seconds())
        elif amount in ["minute", "minutes"]:
            return int((self.date - diff_date.date).total_seconds() / 60)
        elif amount in ["hour", "hours"]:
            return int((self.date - diff_date.date).total_seconds() / 3600)
        elif amount in ["day", "days"]:
            return int((self.date - diff_date.date).total_seconds() / (3600 * 24))
        elif amount in ["week", "weeks"]:
            return int((self.date - diff_date.date).total_seconds() / (3600 * 24 * 7))
        elif amount in ["month", "months"]:
            return (self.date.year - diff_date.date.year) * 12 + (self.date.month - diff_date.date.month)
        elif amount in ["year", "years"]:
            return self.date.year - diff_date.date.year
    
    def hour(self):
        return self.date.hour
    
    def minute(self):
        return self.date.minute
    
    def second(self):
        return self.date.second
    
    def month(self):
        return self.date.month
    
    def year(self):
        return self.date.year
    
    def day_of_month(self):
        return self.date.day
    
    def day_of_week(self):
        weekday = self.date.weekday() + 1  # Monday is 0 in python, so
        return weekday % 7 or 7  # Convert to Sunday = 7
     
    def week_of_year(self):
        return self.date.isocalendar()[1]
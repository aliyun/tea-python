from datetime import datetime, timedelta

class Date:
    def __init__(self, date_input):
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f %z %Z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f", 
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

    def strftime(self, layout):
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
    
    def timestamp(self):
        return int(self.date.timestamp())
    
    def sub(self, unit, amount):
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
    
    def add(self, unit, amount):
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
            new_month = self.date.month + amount
            new_year = self.date.year + (new_month - 1) // 12
            new_month = (new_month - 1) % 12 + 1
            if self.date.day > 28:
                if new_month == 2:
                    new_day = min(self.date.day, 29)
                    if new_day == 29 and not (new_year % 4 == 0 and (new_year % 100 != 0 or new_year % 400 == 0)):
                        new_day = 28
                else:
                    new_day = min(self.date.day, [31, 30][new_month % 2])
            else:
                new_day = self.date.day
                
            new_date = self.date.replace(year=new_year, month=new_month, day=new_day)
            return Date(new_date.isoformat())
        elif unit in ["year", "years"]:
            return Date((self.date.replace(year=self.date.year + amount)).isoformat())
    
    def diff(self, unit, diff_date):
        if unit in ["second", "seconds"]:
            return int((self.date - diff_date.date).total_seconds())
        elif unit in ["minute", "minutes"]:
            return int((self.date - diff_date.date).total_seconds() / 60)
        elif unit in ["hour", "hours"]:
            return int((self.date - diff_date.date).total_seconds() / 3600)
        elif unit in ["day", "days"]:
            return int((self.date - diff_date.date).total_seconds() / (3600 * 24))
        elif unit in ["week", "weeks"]:
            return int((self.date - diff_date.date).total_seconds() / (3600 * 24 * 7))
        elif unit in ["month", "months"]:
            return (self.date.year - diff_date.date.year) * 12 + (self.date.month - diff_date.date.month)
        elif unit in ["year", "years"]:
            return self.date.year - diff_date.date.year
    
    def hour(self):
        return self.date.hour
    
    def minute(self):
        return self.date.minute
    
    def second(self):
        return self.date.second
    
    def month(self):
        return self.date.month
    
    def day_of_month(self):
        return self.date.day
    
    def day_of_week(self):
        weekday = self.date.weekday() + 1  # Monday is 0 in python, so
        return weekday % 7 or 7  # Convert to Sunday = 7
     
    def week_of_year(self):
        return self.date.isocalendar()[1]
    
    def year(self):
        return self.date.year
    
    def UTC(self):
        return self.date.strftime("%Y-%m-%d %H:%M:%S.%f %z %Z")
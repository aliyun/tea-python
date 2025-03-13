class Number:
    def __init__(self, value):
        self.value = self.to_number(value)

    def to_number(self, value):
        if isinstance(value, bool):
            return 1 if value else 0 
        elif value is None:
            return 0
        elif isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return float('nan')
        elif isinstance(value, (list, dict)):
            return float('nan')
        else:
            return float('nan')

    def __str__(self):
        return str(self.value)
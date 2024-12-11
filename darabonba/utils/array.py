import json

class List:

    @staticmethod
    def to_json(input_array):
        """Convert array to a JSON object assuming a string format."""
        try:
            if not isinstance(input_array, list):
                raise TypeError("Input should be a list.")
            
            json_string = json.dumps(input_array)
            return json_string
        
        except TypeError as te:
            return f"TypeError: {str(te)}"
        
        except Exception as e:
            return f"Exception: {str(e)}"
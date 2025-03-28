import json

class Map:
    def __init__(self, data):
        self.data = data

    @staticmethod
    def to_json(map_instance):
        if not isinstance(map_instance, Map):
            raise ValueError("Input must be an instance of Map")
        try:
            return json.dumps(map_instance.data)
        except TypeError as e:
            raise Exception(f"Serialization error: {e}")
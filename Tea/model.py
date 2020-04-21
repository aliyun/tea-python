import re


class TeaModel:
    def __init__(self):
        self._names = {}
        self._validations = {}

    @staticmethod
    def validate_required(prop, prop_name):
        if prop is None:
            raise Exception(prop_name + ' is required.')

    @staticmethod
    def validate_max_length(prop, prop_name, max_length):
        if len(prop) > max_length:
            raise Exception(prop_name + ' is exceed max-length : ' + max_length)

    @staticmethod
    def validate_pattern(prop, prop_name, pattern):
        match_obj = re.search(pattern, prop, re.M | re.I)
        if not match_obj:
            raise Exception(prop_name + ' is not match : ' + pattern)

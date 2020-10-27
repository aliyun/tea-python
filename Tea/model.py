import re
from .exceptions import RequiredArgumentException


class TeaModel:
    def validate(self):
        pass

    def to_map(self):
        pass

    def from_map(self, map=None):
        pass

    @staticmethod
    def validate_required(prop, prop_name):
        if prop is None:
            raise RequiredArgumentException(prop_name)

    @staticmethod
    def validate_max_length(prop, prop_name, max_length):
        if len(prop) > max_length:
            raise Exception('%s is exceed max-length: %s' % (prop_name, max_length))

    @staticmethod
    def validate_min_length(prop, prop_name, min_length):
        if len(prop) < min_length:
            raise Exception('%s is less than min-length: %s' % (prop_name, min_length))

    @staticmethod
    def validate_pattern(prop, prop_name, pattern):
        match_obj = re.search(pattern, str(prop), re.M | re.I)
        if not match_obj:
            raise Exception('%s is not match: %s' % (prop_name, pattern))

    @staticmethod
    def validate_maximum(num, prop_name, maximum):
        if num > maximum:
            raise Exception('%s is greater than the maximum: %s' % (prop_name, maximum))

    @staticmethod
    def validate_minimum(num, prop_name, minimum):
        if num < minimum:
            raise Exception('%s is less than the minimum: %s' % (prop_name, minimum))

    def __str__(self):
        s = self.to_map()
        if s:
            return str(s)
        else:
            return object.__str__(self)

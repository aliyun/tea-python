import re

from darabonba.exceptions import ValidateException


def assert_integer_positive(integer, name):
    if isinstance(integer, int) and integer > 0:
        return
    raise ValidateException("{0} should be a positive integer.".format(name))


def validate_pattern(prop, prop_name, pattern):
    match_obj = re.search(pattern, prop, re.M | re.I)
    if not match_obj:
        raise ValidateException('The parameter %s not match with %s' % (prop_name, pattern))


def is_null(value, name):
    if value is None:
        raise ValidateException("The parameter {0} should not be null.".format(name))
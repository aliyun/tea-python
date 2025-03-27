import warnings
import functools


def deprecated(reason):
    """This is a decorator which can be used to mark functions as deprecated.
    It will result in a warning being emitted when the function is used.

    Args:
        reason (str): Explanation of why the function is deprecated.
    """

    def decorator(func):
        original_func = func.__func__ if isinstance(func, staticmethod) or isinstance(func, classmethod) else func

        @functools.wraps(original_func)
        def decorated_function(*args, **kwargs):
            warnings.warn(f"Call to deprecated function {original_func.__name__}. {reason}",
                          category=DeprecationWarning,
                          stacklevel=2)
            return original_func(*args, **kwargs)

        if isinstance(func, staticmethod):
            return staticmethod(decorated_function)
        elif isinstance(func, classmethod):
            return classmethod(decorated_function)
        else:
            return decorated_function

    return decorator

def type_check(*arg_types, **kwarg_types):
    """This decorator is used to check whether the input parameter type meets the definition.
    It will result in a warning being emitted when the function is used.
    """

    def decorator(func):
        original_func = func.__func__ if isinstance(func, staticmethod) or isinstance(func, classmethod) else func

        @functools.wraps(original_func)
        def wrapper(*args, **kwargs):
            for i, (a, t) in enumerate(zip(args, arg_types)):
                if not isinstance(a, t):
                    warnings.warn(f"Argument {i} is not of type {t}",
                                  category=UserWarning,
                                  stacklevel=2)
            for k, t in kwarg_types.items():
                if k in kwargs and not isinstance(kwargs[k], t):
                    warnings.warn(f"Argument {k} is not of type {t}",
                                  category=UserWarning,
                                  stacklevel=2)
            return original_func(*args, **kwargs)

        if isinstance(func, staticmethod):
            return staticmethod(wrapper)
        elif isinstance(func, classmethod):
            return classmethod(wrapper)
        else:
            return wrapper

    return decorator
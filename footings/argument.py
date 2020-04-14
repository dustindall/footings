"""Objects tied to creating Arguments"""

from typing import Any, List, Dict, Union, Optional, Callable
from attr import attrs, attrib


class ArgumentTypeError(Exception):
    """Wrong type passed to parameter"""


def _check_type(expected, value):
    if isinstance(value, expected) is False:
        raise ArgumentTypeError(f"Expected type {value} but received {type(value)}")


class ArgumentAllowedError(Exception):
    """Value not allowed passed to parameter"""


def _check_allowed(allowed, value):
    if value not in allowed:
        raise ArgumentAllowedError(f"{value} is not in [{allowed}]")


class ArgumentMinValueError(Exception):
    """Value below allowed minimum passed to parameter"""


def _check_min_val(min_val, value):
    if value < min_val:
        raise ArgumentMinValueError(f"{value} is less than {min_val}")


class ArgumentMaxValueError(Exception):
    """Value above allowed maximum passed to parameter"""


def _check_max_val(max_val, value):
    if value > max_val:
        raise ArgumentMaxValueError(f"{value} is greater than {max_val}")


class ArgumentMinLenError(Exception):
    """Value with length below allowed minimum passed to parameter"""


def _check_min_len(min_len, value):
    if len(value) < min_len:
        raise ArgumentMinLenError(f"len {len(value)} is less than {min_len}")


class ArgumentMaxLenError(Exception):
    """Value with length above allowed maximum passed to parameter"""


def _check_max_len(max_len, value):
    if len(value) > max_len:
        raise ArgumentMaxLenError(f"len {len(value)} is greater than {max_len}")


class ArgumentCustomError(Exception):
    """Value fails custom test"""


def _check_custom(func, value):
    if callable(func) is False:
        raise TypeError("the object passed to custom must be callable")

    if func(value) is False:
        raise ArgumentCustomError(f"The custom test failed with {value}")


_PARAMS_CHECKS = {
    "dtype": _check_type,
    "allowed": _check_allowed,
    "min_val": _check_min_val,
    "max_val": _check_max_val,
    "min_len": _check_min_len,
    "max_len": _check_max_len,
    "custom": _check_custom,
}


@attrs(frozen=True, slots=True)
class Argument:
    """An argument is a representation of a parameter to be passed to model built with \n
    the footings framework.

    Attributes
    ----------
    name : str
        Name to assign the argument. Will show in docstring of created models.
    description : str
        A description of the argument. Will show in docstring of created models.
    default : Any, optional
        The default value when a value is not passed to argument in a model.
    dtype : type, optional
        The expected type of the passed argument value. Will be used as a validator.
    allowed : List[Any], optional
        A list of values that are allowed. Will be used as a validator.
    min_val :
        The minimum value allowed. Will be used as a validator.
    max_val :
        The maximum value allowed. Will be used as a validator.
    min_len :
        The minimum length allowed. Will be used as a valaidator.
    max_len :
        The maximum length allowed. Will be used as a validator.
    custom : callable
        A custom function that acts as a validator.
    other_meta : dict
        Other meta passed to argument.
    """

    # pylint: disable=too-many-instance-attributes
    name: str = attrib()
    description: Optional[str] = attrib(default=None, repr=False)
    default: Optional[Any] = attrib(default=None)
    dtype: Optional[type] = attrib(default=None)
    allowed: Optional[List[Any]] = attrib(default=None)
    min_val: Optional[Union[int, float]] = attrib(default=None)
    max_val: Optional[Union[int, float]] = attrib(default=None)
    min_len: Optional[int] = attrib(default=None)
    max_len: Optional[int] = attrib(default=None)
    custom: Optional[Callable] = attrib(default=None)
    other_meta: Dict = attrib(factory=dict, repr=False)

    def __attrs_post_init__(self):
        if self.default is not None:
            self.valid(self.default)

    def valid(self, value):
        """Test to see if value is valid as a parameter"""
        for k, v in _PARAMS_CHECKS.items():
            if getattr(self, k) is not None:
                v(getattr(self, k), value)
        return True

    def create_validator(self):
        """Create validator for table"""

        def validator(inst, attribute, value):  # pylint: disable=unused-argument
            return self.valid(value)

        return validator


def create_agrument(name: str, **kwargs):
    """Create an argument.

    Parameters
    ----------
    name : str
        Name to assign the argument. Will show in docstring of created models.
    **kwargs
        See Argument details.

    See Also
    --------
    Argument

    Returns
    -------
    Argument
        The created argument.
    """
    return Argument(name, **kwargs)

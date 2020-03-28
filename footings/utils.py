"""utils.py"""


from itertools import product
from functools import partial
from collections.abc import Iterable

from attr import attrs, attrib
from attr.validators import optional, is_callable, instance_of, deep_iterable

#########################################################################################
# established errors
#########################################################################################


class DispatcherKeyError(Exception):
    """Key does not exist within dispatch function registry."""


class DispatcherRegisterError(Exception):
    """Error occuring registering a function to the Dispatcher."""


#########################################################################################
# Dispatcher
#########################################################################################

def _update_registry(registry, keys, function):
    for key in keys:
        registry.update({key: function})
    return registry

@attrs(slots=True, frozen=True)
class Dispatcher:
    """Dispatch function"""

    name = attrib(validator=instance_of(str))
    parameters = attrib(validator=deep_iterable(instance_of(str), instance_of(tuple)))
    default = attrib(default=None, validator=optional(is_callable()))
    registry = attrib(init=False, repr=False, factory=dict)

    def register(self, function=None, **kwargs):
        """Register a key and function to dispatch on."""
        items = []
        for param in self.parameters:
            value = kwargs.get(param, None)
            if value is None:
                raise DispatcherRegisterError(
                    f"The parameter [{param}] is not a parameter of the instance."
                )
            if isinstance(value, str):
                items.append([value])
            elif isinstance(value, Iterable):
                items.append(value)
            else:
                raise DispatcherRegisterError(
                    f"The value for [{param}] is not a str or an iterable."
                )

        keys = list(product(*items))
        if function is None:
            return partial(_update_registry, self.registry, keys)
        return _update_registry(self.registry, keys, function)

    def __call__(self, *args, **kwargs):
        key = []
        for param in self.parameters:
            key.append(kwargs.get(param))
            kwargs.pop(param)
        key = tuple(key)
        func = self.registry.get(key, None)
        if func is None:
            if self.default is None:
                msg = f"The key {key} does not exist within registry and no default."
                raise DispatcherKeyError(msg)
            return self.default(*args, **kwargs)
        return func(*args, **kwargs)
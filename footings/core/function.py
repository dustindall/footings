import pandas as pd

from .annotation import Column, CReturn, Frame, FReturn, Setting, parse_annotation
from .utils import _generate_message


def func_annotation_valid(function):
    # validate all args annotated
    args = set(getfullargspec(function).args)
    anno = set(function.__annotations__.keys())
    diff_args = args.difference(anno)
    if len(diff_args) > 0:
        msg1 = "The following function parameters need to be annotated - "
        raise AssertionError(_generate_message(msg1, diff_args))

    # validate input annotated types
    unk_types = []
    not_inste = []
    for k, v in function.__annotations__.items():
        if k != "return":
            if (
                v is not Column
                and v is not Frame
                and v is not Setting
                and isinstance(v, type)
            ):
                unk_types.append(k)
            if (
                isinstance(v, Column) == False
                and isinstance(v, Frame) == False
                and isinstance(v, Setting) == False
            ):
                not_inste.append(k)

    if len(unk_types) > 0:
        msg2 = "The following function parameters are assigned invalid input types - "
        raise AssertionError(_generate_message(msg2, unk_types))

    if len(not_inste) > 0:
        msg3 = "The following function parameters are assigned non instantiated types - "
        raise AssertionError(_generate_message(msg3, not_inste))

    # validate input combinations
    items = function.__annotations__.items()
    c = [v for k, v in items if k != "return" and isinstance(v, Column)]
    f = [v for k, v in items if k != "return" and isinstance(v, Frame)]
    assert (
        len(c) > 0 and len(f) > 0
    ) == False, "Column and Frame types cannot be used together as annotation inputs."

    # assert len(f) < 2, "Mutiple Frames cannot be used as input"

    # validate function return is annotated
    assert "return" in function.__annotations__, "Function return needs to be annotated"

    # validate input/return combinations
    if len(c) > 0 and isinstance(function.__annotations__["return"], CReturn) == False:
        msg4 = (
            "If using Columns as input, return needs to be annotated with "
            "an instance of CReturn."
        )
        raise AssertionError(msg4)

    if len(f) > 0 and isinstance(function.__annotations__["return"], FReturn) == False:
        msg5 = (
            "If using a Frame as input, return needs to be annotated with "
            "an instance of FReturn."
        )
        raise AssertionError(msg5)

    return True


def ff_function(function, input_columns, output_columns, settings):
    """[summary]
    
    Parameters
    ----------
    function : [type]
        [description]
    input_columns : [type]
        [description]
    output_columns : [type]
        [description]
    settings : [type]
        [description]
    
    Returns
    -------
    [type]
        [description]
    """

    def df_function(function, input_columns, output_columns, settings):
        assert len(output_columns) == 1, "output_columns can only be length 1"
        ret = list(output_columns.keys())[0]

        def wrapper(_df, **settings):
            exp = lambda x: function(
                **{k: x[k] for k in input_columns.keys()}, **settings
            )
            _df = _df.assign(**{ret: exp})
            return _df

        wrapper.__doc__ = function.__doc__
        return wrapper

    if type(function.__annotations__["return"]) == CReturn:
        return df_function(function, input_columns, output_columns, settings)
    else:
        return function


class _BaseFunction:
    """
    A class to identify functions specifically built for the footings framework.
    """

    def __init__(self, function, method, output_attrs={}):

        x = parse_annotation(function, method)

        self._function = function
        self._name = function.__name__
        self._input_columns = x["input_columns"]
        self._settings = x["settings"]
        self._output_columns = x["output_columns"]
        self._ff_function = ff_function(
            function, self.input_columns, self.output_columns, self.settings
        )

    @property
    def function(self):
        return self._function

    @property
    def name(self):
        return self._name

    @property
    def input_columns(self):
        return self._input_columns

    @property
    def settings(self):
        return self._settings

    @property
    def output_columns(self):
        return self._output_columns

    def __call__(self, *args, **kwargs):
        return self._function(*args, **kwargs)

    # def __repr__(self):
    #     pass

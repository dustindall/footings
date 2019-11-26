import pytest

from footings import Column, CReturn, Frame, FReturn, Setting
from footings.core.function import _BaseFunction


def test_base_function():
    # using (Column) -> CReturn
    def func1(i: Column("float")) -> CReturn({"v": "float"}):
        return 1 / (1 + i)

    base1 = _BaseFunction(func1, method="A")
    assert isinstance(base1, _BaseFunction)

    # using (Column, Setting) -> CReturn
    def func2(
        i: Column("float"), period: Setting(allowed=["A", "M"], default="A")
    ) -> CReturn({"v": "float"}):
        if period == "A":
            return 1 / (1 + i)
        elif period == "M":
            return 1 / (1 + i / 12)

    base2 = _BaseFunction(func2, method="A")
    assert isinstance(base2, _BaseFunction)

    # using (Frame) -> FReturn
    def func3(df: Frame({"i": "float"})) -> FReturn({"v": "float"}):
        df["v"] = 1 / (1 + df["i"])
        return df

    base3 = _BaseFunction(func3, method="A")
    assert isinstance(base3, _BaseFunction)

    # using (Frame, Setting) -> FReturn
    def func4(
        df: Frame({"i": "float"}), period: Setting(allowed=["A", "M"], default="A")
    ) -> FReturn({"v": "float"}):
        if period == "A":
            df["v"] = 1 / (1 + df["i"])
            return df
        elif period == "M":
            df["v"] = 1 / (1 + df["i"] / 12)
            return df

    base4 = _BaseFunction(func4, method="A")
    assert isinstance(base4, _BaseFunction)

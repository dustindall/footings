"""test for utils.py"""

# pylint: disable=function-redefined, missing-function-docstring

import pytest

from footings.utils import Dispatcher
from footings.errors import FootingsDispatcherKeyError, FootingsDispatcherRegisterError


def test_dispatch_default():
    def _default():
        return "default"

    test = Dispatcher(name="test", parameters=("key",), default=_default)

    @test.register(key="x")
    def _():
        return "x"

    @test.register(key="y")
    def _():
        return "y"

    assert test(key="x") == "x"
    assert test(key="y") == "y"
    assert test(key="z") == "default"


def test_dispatch_one_parameter_single_value():
    test = Dispatcher(name="test", parameters=("key",))

    @test.register(key="x")
    def _():
        return "x"

    @test.register(key="y")
    def _():
        return "y"

    assert test(key="x") == "x"
    assert test(key="y") == "y"
    pytest.raises(FootingsDispatcherKeyError, test, key="z")


def test_dispatch_one_parameter_multiple_values():
    test = Dispatcher(name="test", parameters=("key",))

    @test.register(key=["x1", "x2", "x3"])
    def _():
        return "x"

    @test.register(key="y")
    def _():
        return "y"

    assert test(key="x1") == "x"
    assert test(key="x2") == "x"
    assert test(key="x3") == "x"
    assert test(key="y") == "y"
    pytest.raises(FootingsDispatcherKeyError, test, key="z")


def test_dispatch_multiple_parameters_single_value():
    test = Dispatcher(name="test", parameters=("key1", "key2"))

    @test.register(key1="x1", key2="x2")
    def _():
        return "x"

    @test.register(key1="y1", key2="y2")
    def _():
        return "y"

    assert test(key1="x1", key2="x2") == "x"
    assert test(key1="y1", key2="y2") == "y"
    pytest.raises(FootingsDispatcherKeyError, test, key1="x", key2="z")


def test_dispatch_many_parameter_multiple_values():
    test = Dispatcher(name="test", parameters=("key1", "key2", "key3"))

    @test.register(key1=["x1", "x2", "x3"], key2=["xa", "xb"], key3="xz")
    def _():
        return "x"

    @test.register(key1=["y1", "y2"], key2=["ya"], key3="y")
    def _():
        return "y"

    assert test(key1="x1", key2="xa", key3="xz") == "x"
    assert test(key1="x2", key2="xa", key3="xz") == "x"
    assert test(key1="x3", key2="xa", key3="xz") == "x"
    assert test(key1="x1", key2="xb", key3="xz") == "x"
    assert test(key1="x2", key2="xb", key3="xz") == "x"
    assert test(key1="x3", key2="xb", key3="xz") == "x"
    assert test(key1="y1", key2="ya", key3="y") == "y"
    assert test(key1="y2", key2="ya", key3="y") == "y"
    pytest.raises(FootingsDispatcherKeyError, test, key1="x1", key2="xa", key3="z")


def test_dispatch_raise_errors():
    test = Dispatcher(name="test", parameters=("key",))

    with pytest.raises(FootingsDispatcherRegisterError):

        @test.register(wrong_key="x")
        def _():
            return "x"

    class Test:
        pass

    with pytest.raises(FootingsDispatcherRegisterError):

        @test.register(key=Test())
        def _():
            return "y"

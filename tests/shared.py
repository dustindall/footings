"""Shared objects to use across testing"""

import pandas as pd
from footings import create_argument, use


def steps_using_integers():
    """Steps using integers"""

    def step_1(a, add):
        """Run step_1"""
        return a + add

    def step_2(b, subtract):
        """Run step_2"""
        return b - subtract

    def step_3(a, b, c):
        """Run step_3"""
        return a + b + c

    list_ = [
        {
            "name": "step_1",
            "function": step_1,
            "args": {
                "a": create_argument("a", description="description for a"),
                "add": 1,
            },
        },
        {
            "name": "step_2",
            "function": step_2,
            "args": {
                "b": create_argument("b", description="description for b"),
                "subtract": 1,
            },
        },
        {
            "name": "step_3",
            "function": step_3,
            "args": {
                "a": use("step_1"),
                "b": use("step_2"),
                "c": create_argument("c", description="description for c"),
            },
        },
    ]
    return list_


def steps_using_pandas():
    """Steps using pandas"""

    def create_frame(n):
        """Create DataFrame with rows equal to n.

        Parameters
        ----------
        n : int
            The number of rows to the frame

        Returns
        -------
        pd.DataFrame
        """
        return pd.DataFrame({"n": range(0, n)})

    def frame_add_column(frame, add):
        """Create add column in frame

        Parameters
        ----------
        frame : pd.DataFrame
            The dataframe passed
        add : int
            The amount to add

        Returns
        -------
        pd.DataFrame
        """
        return frame.assign(add_col=lambda df: df["n"] + add)

    def frame_subtract_column(frame, subtract):
        """Create subtract column in frame

        Parameters
        ----------
        frame : pd.DataFrame
            The dataframe passed
        subtract : int
            The amount to subtract

        Returns
        -------
        pd.DataFrame
        """
        return frame.assign(subtract_col=lambda df: df["n"] - subtract)

    list_ = [
        {
            "name": "create_frame",
            "function": create_frame,
            "args": {"n": create_argument("n", description="N rows of frame.")},
        },
        {
            "name": "frame_add_column",
            "function": frame_add_column,
            "args": {
                "frame": use("create_frame"),
                "add": create_argument("add", description="Amount to add."),
            },
        },
        {
            "name": "frame_subtract_column",
            "function": frame_subtract_column,
            "args": {
                "frame": use("frame_add_column"),
                "subtract": create_argument(
                    "subtract", description="Amount to subtract."
                ),
            },
        },
    ]
    return list_

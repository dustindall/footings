import pandas as pd
from pandas.util.testing import assert_frame_equal
import unittest

from footings import Assumption, as_assumption, Frame, FReturn


class TestAssumption(unittest.TestCase):
    """
    """

    def test_assumption(self):
        def get_i(df: Frame({"t": int})) -> FReturn({"i": float}):
            asn = pd.DataFrame({"t": [0, 1, 2, 3], "i": [0, 0.1, 0.09, 0.08]})
            return df.merge(asn, on="t")

        i = Assumption(get_i)
        assert isinstance(i, Assumption)
        test_df = pd.DataFrame({"t": [0, 1, 2, 3], "cash": [1000, -350, -350, -350]})
        assert_frame_equal(test_df.assign(i=[0, 0.1, 0.09, 0.08]), i(test_df))

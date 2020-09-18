from numpydoc.docscrape import Parameter

from footings.doctools.docscrape import FootingsDoc

from .shared import DocModel


def test_footings_doc():
    doc = FootingsDoc(DocModel)

    assert doc["Parameters"] == [
        Parameter("param_1", str(int), ["This is parameter 1."]),
        Parameter("param_2", str(int), ["This is parameter 2."]),
    ]

    assert doc["Modifiers"] == [
        Parameter("modif_1", str(int), ["This is modifier 1."]),
        Parameter("modif_2", str(int), ["This is modifier 2."]),
    ]

    assert doc["Meta"] == [
        Parameter("meta_1", "", ["This is meta 1."]),
        Parameter("meta_2", "", ["This is meta 2."]),
    ]

    assert doc["Assets"] == [
        Parameter("asset_1", str(int), ["This is asset 1."]),
        Parameter("asset_2", str(int), ["This is asset 2."]),
    ]

    assert doc["Steps"] == [
        "1. _step_1 - Step 1 summary",
        "2. _step_2 - Step 2 summary",
    ]
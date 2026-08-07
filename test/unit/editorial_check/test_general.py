import pandas as pd
import pytest

from typing import Callable
from validateur_batch.control import editorial_check


def test_get_correct_case(case: pd.DataFrame, case_output: pd.DataFrame) -> None:
    pd.testing.assert_frame_equal(editorial_check._get_correct_case(case), case_output)


def test_check_spellcheck_no_dict(null: pd.DataFrame) -> None:
    pd.testing.assert_frame_equal(
        editorial_check._check_spellcheck(null, None), null)


def test_check_spellcheck(spell: pd.DataFrame, spell_output: pd.DataFrame,
                          fake_spell_dict) -> None:
    pd.testing.assert_frame_equal(
        editorial_check._check_spellcheck(spell, fake_spell_dict),
        spell_output)


@pytest.mark.parametrize("df_in, df_out", [("null", "null"), ("ar", "ar2")])
def test_check_ar2(df_in: pd.DataFrame, df_out: pd.DataFrame,
                   request: pytest.FixtureRequest) -> None:
    input = request.getfixturevalue(df_in)
    output = request.getfixturevalue(df_out)
    pd.testing.assert_frame_equal(editorial_check._check_ar2(input), output)


@pytest.mark.parametrize("df_in, df_out", [("null", "null"), ("ar", "ar6")])
def test_check_ar6(df_in: pd.DataFrame, df_out: pd.DataFrame,
                   semtag: Callable[[int], pd.Series],
                   request: pytest.FixtureRequest) -> None:
    input = request.getfixturevalue(df_in)
    output = request.getfixturevalue(df_out)
    tag = semtag(len(input))
    pd.testing.assert_frame_equal(editorial_check._check_ar6(input, tag), output)

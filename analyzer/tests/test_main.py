"""
Module for unit tests that cover the analyzer application's main module.
"""

import pytest

from analyzer.main import preprocess_text


@pytest.mark.parametrize(
    "input_text, expected_output",
    [
        ("This is a test.", "test"),
        ("This example has PUNCTUATION!", "example punctuation"),
        ("Another example, with some stop words.", "another example stop word"),
        ("  Leading and trailing spaces.  ", "leading trailing space"),
        ("123 numbers should be ignored.", "number ignored"),
    ]
)
def test_preprocess_text(input_text: str, expected_output: str) -> None:
    """
    Unit tests to ensure text preprocessing is working as expected.

    :param input_text: The input text to preprocess.
    :param expected_output: The expected output after preprocessing.
    """

    assert preprocess_text(input_text) == expected_output

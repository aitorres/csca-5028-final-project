"""
Unit tests for the collector application's main module.
"""

from typing import Any, Optional

import pytest

from collector.main import filter_record_by_message, parse_and_filter_record


@pytest.mark.parametrize(
    "message, expected",
    [
        ("", None),
        ("   ", None),
        ("invalid json", None),
        ("[]", None),
        ("{}", None),
    ]
)
def test_parse_and_filter_record(
    message: str, expected: Optional[dict[str, Any]]
) -> None:
    """
    Unit test for the parse_and_filter_record function with a combination
    of valid and invalid inputs, and their expected outputs.
    """

    assert parse_and_filter_record(message) == expected


@pytest.mark.parametrize(
    "record, expected",
    [
        (
            {"text": "This is a post about Vancouver"},
            {"text": "This is a post about Vancouver"}
        ),
        ({"text": "This is a post about Toronto"}, None),
        (
            {"text": "Vancouver is great!"},
            {"text": "Vancouver is great!"}
        ),
        ({"text": "I love Van"}, None),
        (
            {"text": "YVR is the best airport"},
            {"text": "YVR is the best airport"}
        ),
        ({"text": "Vancity vibes"}, {"text": "Vancity vibes"}),
        (
            {"text": "Nothing to do with Vancouver"},
            {"text": "Nothing to do with Vancouver"}
        ),
        (
            {"text": "Este es un post en otro idioma", "langs": ["es"]},
            None
        ),
        (
            {"text": "Este es un post en otro idioma sobre Vancouver", "langs": ["es"]},
            None
        ),
    ]
)
def test_filter_record_by_message(
    record: dict[str, Any], expected: Optional[dict[str, Any]]
) -> None:
    """
    Unit test for the filter_record_by_message function with various
    records and their expected outputs.
    """

    assert filter_record_by_message(record) == expected

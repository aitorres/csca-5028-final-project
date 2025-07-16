"""
Unit tests for the collector application's main module.
"""

from typing import Any, Optional

import pytest

from collector.main import parse_and_filter_record


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

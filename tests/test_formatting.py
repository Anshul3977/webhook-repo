"""Ordinal timestamps, including the hours that used to be zero-padded."""

import pytest
from webhook_monitor.formatting import format_timestamp


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2021-04-01T21:30:00Z", "1st April 2021 - 9:30 PM UTC"),
        ("2021-04-02T21:30:00Z", "2nd April 2021 - 9:30 PM UTC"),
        ("2021-04-03T21:30:00Z", "3rd April 2021 - 9:30 PM UTC"),
        ("2021-04-04T09:05:00Z", "4th April 2021 - 9:05 AM UTC"),
        ("2021-04-11T00:00:00Z", "11th April 2021 - 12:00 AM UTC"),
        ("2021-04-12T12:00:00Z", "12th April 2021 - 12:00 PM UTC"),
        ("2021-04-13T15:00:00Z", "13th April 2021 - 3:00 PM UTC"),
        ("2021-04-21T21:30:00Z", "21st April 2021 - 9:30 PM UTC"),
        ("2021-04-22T21:30:00Z", "22nd April 2021 - 9:30 PM UTC"),
        ("2021-04-23T21:30:00Z", "23rd April 2021 - 9:30 PM UTC"),
        ("2021-05-31T21:30:00Z", "31st May 2021 - 9:30 PM UTC"),
    ],
)
def test_ordinal_timestamp(raw, expected):
    assert format_timestamp(raw) == expected

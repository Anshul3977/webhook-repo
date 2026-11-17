"""Environment flags are strings on Render. Only explicit true values enable them."""

import pytest
from webhook_monitor.config import as_bool


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("true", True),
        ("TRUE", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("false", False),
        ("False", False),
        ("0", False),
        ("", False),
        (None, False),
        ("no", False),
    ],
)
def test_as_bool(raw, expected):
    assert as_bool(raw) is expected

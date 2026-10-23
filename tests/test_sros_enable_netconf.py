"""Package metadata checks."""

from sros_enable_netconf import __version__


def test_version():
    """Check the project version."""
    assert __version__ == "0.1.0"

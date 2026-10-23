"""Offline regression tests for SSH and NETCONF trust boundaries."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from ncclient.transport.errors import SSHUnknownHostError
from sros_enable_netconf import enable_netconf, helpers


def test_netconf_checks_known_host():
    """Netconf checks known host."""
    with patch.object(helpers.manager, "connect") as connect:
        helpers.netconfconn(SimpleNamespace(node="example.invalid", port=830), "user", "test-only")
    assert connect.call_args.kwargs["hostkey_verify"] is True


def test_netconf_host_failure_propagates():
    """Netconf host failure propagates."""
    with patch.object(helpers.manager, "connect", side_effect=SSHUnknownHostError("host", "fingerprint")):
        with pytest.raises(SSHUnknownHostError):
            helpers.netconfconn(SimpleNamespace(node="example.invalid", port=830), "user", "test-only")


def test_initial_ssh_checks_known_hosts_before_any_commands():
    """Initial ssh checks known hosts before any commands."""
    with patch.object(
        enable_netconf, "get_arguments", return_value=SimpleNamespace(node="example.invalid", user="user")
    ), patch.object(enable_netconf, "NETCONF_PASS", "test-only"), patch.object(
        enable_netconf.getpass, "getpass", return_value="test-only"
    ), patch.object(
        enable_netconf, "netmiko_logging"
    ), patch.object(
        enable_netconf, "ConnectHandler", side_effect=RuntimeError("unknown host")
    ) as connect, patch.object(
        enable_netconf, "send_commands"
    ) as send:
        with pytest.raises(RuntimeError, match="unknown host"):
            enable_netconf.main()
    assert connect.call_args.kwargs["ssh_strict"] is True
    assert connect.call_args.kwargs["system_host_keys"] is True
    send.assert_not_called()


def test_empty_provisioning_password_fails_before_connection():
    """Empty provisioning password fails before connection."""
    with patch.object(enable_netconf, "get_arguments", return_value=Mock()), patch.object(
        enable_netconf, "NETCONF_PASS", None
    ), patch.object(enable_netconf.getpass, "getpass", return_value=""), patch.object(
        enable_netconf, "ConnectHandler"
    ) as connect:
        with pytest.raises(ValueError, match="password"):
            enable_netconf.main()
    connect.assert_not_called()


@pytest.mark.parametrize("value", ["line\nbreak", "semi;command", 'quote"', "space here", "slash\\escape", "\x00"])
def test_unsafe_credentials_are_rejected_before_network(value):
    """Reject CLI separators in credentials before connecting."""
    with patch.object(enable_netconf, "get_arguments", return_value=Mock()), patch.object(
        enable_netconf, "NETCONF_PASS", value
    ), patch.object(enable_netconf, "ConnectHandler") as connect:
        with pytest.raises(ValueError):
            enable_netconf.main()
    connect.assert_not_called()


def test_configuration_error_does_not_echo_password(capsys):
    """Do not print credentials embedded in library errors."""
    connection = Mock()
    connection.send_config_set.side_effect = RuntimeError("password SECRET-MARKER")
    with pytest.raises(RuntimeError) as error:
        helpers.send_commands(connection, ["password SECRET-MARKER"])
    assert "SECRET-MARKER" not in str(error.value)
    assert "SECRET-MARKER" not in capsys.readouterr().out


def test_transport_logs_cannot_record_credentials(tmp_path, monkeypatch):
    """Filter network-library records including descendant logger names."""
    import io
    import logging

    monkeypatch.chdir(tmp_path)
    output = io.StringIO()
    handler = logging.StreamHandler(output)
    root = logging.getLogger()
    root.addHandler(handler)
    originals = {item: list(item.filters) for item in root.handlers}
    try:
        with patch.object(helpers, "create_folder"), patch.object(helpers, "save_file"), patch.object(
            logging, "basicConfig"
        ):
            helpers.netmiko_logging()
        for name in ("netmiko", "netmiko.channel", "paramiko.transport", "ncclient.transport.ssh"):
            record = logging.LogRecord(name, logging.ERROR, "", 0, "SECRET-MARKER", (), None)
            assert not handler.filter(record)
            handler.handle(record)
        handler.handle(logging.LogRecord("application", logging.WARNING, "", 0, "safe message", (), None))
        assert "SECRET-MARKER" not in output.getvalue()
        assert "safe message" in output.getvalue()
    finally:
        root.removeHandler(handler)
        for item, filters in originals.items():
            item.filters[:] = filters

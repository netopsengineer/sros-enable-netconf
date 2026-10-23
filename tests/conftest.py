"""Prevent accidental external connections in every test."""

import socket
import pytest


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Reject every attempt to connect a socket during tests."""

    def fail(*args, **kwargs):
        raise AssertionError("Tests must not contact any host")

    monkeypatch.setattr(socket.socket, "connect", fail)
    monkeypatch.setattr(socket, "create_connection", fail)

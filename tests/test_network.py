"""Tests for netcast.network module."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from netcast.network import get_local_ip


class TestGetLocalIp:
    """Tests for the get_local_ip() helper."""

    def test_returns_string(self) -> None:
        result = get_local_ip()
        assert isinstance(result, str)

    def test_returns_valid_ipv4_format(self) -> None:
        result = get_local_ip()
        parts = result.split(".")
        assert len(parts) == 4
        assert all(p.isdigit() for p in parts)

    def test_fallback_when_offline(self) -> None:
        """Simulates no network by making socket.connect raise OSError."""
        with patch("netcast.network.socket.socket") as mock_socket:
            mock_socket.return_value.__enter__ = lambda s: s
            mock_socket.return_value.__exit__ = lambda s, *a: None
            mock_socket.return_value.connect.side_effect = OSError("No network")

            result = get_local_ip()
            assert result == "127.0.0.1"

    def test_returns_detected_ip(self) -> None:
        """Simulates a successful network detection."""
        with patch("netcast.network.socket.socket") as mock_socket:
            instance = mock_socket.return_value.__enter__.return_value
            instance.getsockname.return_value = ("192.168.1.42", 0)

            result = get_local_ip()
            assert result == "192.168.1.42"

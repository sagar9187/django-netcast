"""Tests for the share_local management command."""

from __future__ import annotations

import os
from io import StringIO
from unittest.mock import patch

import django
from django.conf import settings
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
django.setup()

from netcast.management.commands.share_local import Command


class TestInjectSettings(SimpleTestCase):
    """Tests for Command._inject_settings()."""

    @override_settings(ALLOWED_HOSTS=[], CSRF_TRUSTED_ORIGINS=[])
    def test_injects_allowed_hosts(self) -> None:
        Command._inject_settings("192.168.1.42", "8000")

        assert "192.168.1.42" in settings.ALLOWED_HOSTS
        assert "127.0.0.1" in settings.ALLOWED_HOSTS
        assert "localhost" in settings.ALLOWED_HOSTS
        assert "0.0.0.0" in settings.ALLOWED_HOSTS

    @override_settings(ALLOWED_HOSTS=[], CSRF_TRUSTED_ORIGINS=[])
    def test_injects_csrf_trusted_origins(self) -> None:
        Command._inject_settings("192.168.1.42", "8000")

        assert "http://192.168.1.42:8000" in settings.CSRF_TRUSTED_ORIGINS
        assert "http://192.168.1.42" in settings.CSRF_TRUSTED_ORIGINS
        assert "http://127.0.0.1:8000" in settings.CSRF_TRUSTED_ORIGINS

    @override_settings(
        ALLOWED_HOSTS=["192.168.1.42", "127.0.0.1"],
        CSRF_TRUSTED_ORIGINS=["http://192.168.1.42:8000"],
    )
    def test_no_duplicate_entries(self) -> None:
        """Running _inject_settings twice must not create duplicates."""
        Command._inject_settings("192.168.1.42", "8000")
        Command._inject_settings("192.168.1.42", "8000")

        assert settings.ALLOWED_HOSTS.count("192.168.1.42") == 1
        assert settings.CSRF_TRUSTED_ORIGINS.count("http://192.168.1.42:8000") == 1

    @override_settings(ALLOWED_HOSTS=[], CSRF_TRUSTED_ORIGINS=[])
    def test_offline_fallback_injection(self) -> None:
        """When offline (ip=127.0.0.1), settings should still be valid."""
        Command._inject_settings("127.0.0.1", "8000")

        assert "127.0.0.1" in settings.ALLOWED_HOSTS
        assert "http://127.0.0.1:8000" in settings.CSRF_TRUSTED_ORIGINS


class TestBanner(SimpleTestCase):
    """Tests for the terminal banner output."""

    def _get_banner_output(self, local_ip: str, port: str) -> str:
        cmd = Command(stdout=StringIO(), stderr=StringIO())
        cmd._print_banner(local_ip, port)
        return cmd.stdout.getvalue()

    def test_banner_shows_local_url(self) -> None:
        output = self._get_banner_output("192.168.1.42", "8000")
        assert "http://127.0.0.1:8000/" in output

    def test_banner_shows_network_url(self) -> None:
        output = self._get_banner_output("192.168.1.42", "8000")
        assert "http://192.168.1.42:8000/" in output

    def test_banner_shows_security_warning(self) -> None:
        output = self._get_banner_output("192.168.1.42", "8000")
        assert "Wi-Fi" in output

    def test_banner_offline_mode(self) -> None:
        output = self._get_banner_output("127.0.0.1", "8000")
        assert "offline" in output


class TestIsReloadProcess(SimpleTestCase):
    """Tests for the reload detection logic."""

    def test_not_reload_when_env_unset(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            # RUN_MAIN not set — should be the main process
            os.environ.pop("RUN_MAIN", None)
            assert Command._is_reload_process() is False

    def test_is_reload_when_env_set(self) -> None:
        with patch.dict(os.environ, {"RUN_MAIN": "true"}):
            assert Command._is_reload_process() is True


class TestDebugGuard(SimpleTestCase):
    """Tests for the DEBUG=False production guard."""

    @override_settings(DEBUG=False)
    def test_blocks_when_debug_false(self) -> None:
        """share_local must refuse to run in production (DEBUG=False)."""
        cmd = Command(stdout=StringIO(), stderr=StringIO())
        with self.assertRaises(CommandError) as ctx:
            cmd.handle(addrport="8000")
        assert "DEBUG=False" in str(ctx.exception)

    @override_settings(DEBUG=True, ALLOWED_HOSTS=[], CSRF_TRUSTED_ORIGINS=[])
    @patch("netcast.management.commands.share_local.get_local_ip", return_value="192.168.1.42")
    @patch.object(Command, "_print_banner")
    @patch("django.contrib.staticfiles.management.commands.runserver.Command.handle")
    def test_allows_when_debug_true(self, mock_handle, mock_banner, mock_ip) -> None:
        """share_local must run normally when DEBUG=True."""
        cmd = Command(stdout=StringIO(), stderr=StringIO())
        cmd.handle(addrport="8000")
        mock_handle.assert_called_once()

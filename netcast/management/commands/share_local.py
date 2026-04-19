"""
share_local — Expose your Django dev server on the local Wi-Fi network.

A drop-in replacement for ``runserver`` that:
  * auto-detects your LAN IP address
  * injects it into ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS
  * binds to 0.0.0.0 so every device on your network can reach the server
"""

from __future__ import annotations

import os
from typing import Any

from django.conf import settings
from django.contrib.staticfiles.management.commands.runserver import (
    Command as StaticFilesRunserverCommand,
)
from django.core.management.base import CommandError

from netcast.network import get_local_ip

# Separator used in the banner
_LINE = "\u2500" * 54


class Command(StaticFilesRunserverCommand):
    """Run the Django development server and share it on the local network."""

    help = (
        "Start Django's development server bound to 0.0.0.0 so that "
        "any device on the same Wi-Fi / LAN can access it."
    )

    # ------------------------------------------------------------------
    # Settings injection
    # ------------------------------------------------------------------

    @staticmethod
    def _inject_settings(local_ip: str, port: str) -> None:
        """Safely inject the LAN IP into ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS."""
        # --- ALLOWED_HOSTS ------------------------------------------------
        allowed: list[str] = list(getattr(settings, "ALLOWED_HOSTS", []))

        for host in ("0.0.0.0", local_ip, "127.0.0.1", "localhost"):  # noqa: S104
            if host not in allowed:
                allowed.append(host)

        settings.ALLOWED_HOSTS = allowed

        # --- CSRF_TRUSTED_ORIGINS -----------------------------------------
        origins: list[str] = list(getattr(settings, "CSRF_TRUSTED_ORIGINS", []))

        for origin in (
            f"http://{local_ip}:{port}",
            f"http://{local_ip}",
            f"http://127.0.0.1:{port}",
            f"http://localhost:{port}",
        ):
            if origin not in origins:
                origins.append(origin)

        settings.CSRF_TRUSTED_ORIGINS = origins

    # ------------------------------------------------------------------
    # Banner
    # ------------------------------------------------------------------

    def _print_banner(self, local_ip: str, port: str) -> None:
        """Print a clean startup banner with clickable URLs."""
        is_offline = local_ip == "127.0.0.1"

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"  \u250c{_LINE}\u2510"))
        self.stdout.write(
            self.style.SUCCESS("  \u2502")
            + "  \U0001f680  django-netcast \u00b7 LAN server running  "
            + self.style.SUCCESS("   \u2502")
        )
        self.stdout.write(self.style.SUCCESS(f"  \u251c{_LINE}\u2524"))

        local_url = f"http://127.0.0.1:{port}/"
        local_padding = " " * (42 - len(local_url))
        self.stdout.write(
            self.style.SUCCESS("  \u2502")
            + f"  Local:    {local_url}{local_padding}"
            + self.style.SUCCESS("\u2502")
        )

        if is_offline:
            msg = "offline \u2014 using localhost only"
            net_padding = " " * (42 - len(msg))
            self.stdout.write(
                self.style.WARNING("  \u2502")
                + f"  Network:  {msg}{net_padding}"
                + self.style.WARNING("\u2502")
            )
        else:
            network_url = f"http://{local_ip}:{port}/"
            net_padding = " " * (42 - len(network_url))
            self.stdout.write(
                self.style.SUCCESS("  \u2502")
                + f"  Network:  {network_url}{net_padding}"
                + self.style.SUCCESS("\u2502")
            )

        self.stdout.write(self.style.SUCCESS(f"  \u251c{_LINE}\u2524"))
        self.stdout.write(
            self.style.WARNING("  \u2502")
            + "  \u26a0  Anyone on your Wi-Fi can access this!  "
            + self.style.WARNING("  \u2502")
        )
        self.stdout.write(self.style.SUCCESS(f"  \u2514{_LINE}\u2518"))
        self.stdout.write("")

    # ------------------------------------------------------------------
    # Entrypoint
    # ------------------------------------------------------------------

    def handle(self, *args: Any, **options: Any) -> None:
        """Resolve LAN IP, patch settings, then delegate to runserver."""
        if not settings.DEBUG:
            raise CommandError(
                "share_local is blocked because DEBUG=False (production mode).\n"
                "This command is intended for local development only.\n"
                "Set DEBUG=True in your settings to use it."
            )

        # Determine port — Django passes it as the first positional arg or
        # via options["addrport"].
        if args:
            addrport = args[0]
        else:
            addrport = options.get("addrport", "") or ""

        # Extract just the port number if the user passed addr:port.
        if ":" in addrport:
            port = addrport.rsplit(":", 1)[1]
        else:
            port = addrport or "8000"

        local_ip = get_local_ip()

        self._inject_settings(local_ip, port)

        # Force binding to all interfaces.
        options["addrport"] = f"0.0.0.0:{port}"  # noqa: S104

        # Print banner only on the first run (not on auto-reload children).
        if not self._is_reload_process():
            self._print_banner(local_ip, port)

        super().handle(*args, **options)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_reload_process() -> bool:
        """Return True when running inside the autoreloader child process."""
        return os.environ.get("RUN_MAIN") == "true"

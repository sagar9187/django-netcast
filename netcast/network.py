"""Network utility for resolving the local LAN IPv4 address."""

from __future__ import annotations

import socket


def get_local_ip() -> str:
    """Resolve the host machine's local IPv4 address via a dummy UDP connection.

    Uses a non-blocking UDP socket aimed at a public DNS address (without
    actually sending data) to determine which local interface the OS would
    route through.  Falls back to 127.0.0.1 when no network is available.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            # Connect to a public DNS — no data is sent over the wire.
            sock.connect(("8.8.8.8", 80))
            ip: str = sock.getsockname()[0]
        return ip
    except OSError:
        return "127.0.0.1"

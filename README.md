# 📡 django-netcast

**Instantly share your Django dev server with any device on your Wi-Fi — zero configuration required.**

No more editing `ALLOWED_HOSTS`. No more Googling "what's my IP". No more `0.0.0.0` confusion.  
Just run **one command** and open the URL on your phone.

```bash
python manage.py share_local
```

```
  ┌──────────────────────────────────────────────────────┐
  │     django-netcast · LAN server running             │
  ├──────────────────────────────────────────────────────┤
  │  Local:    http://127.0.0.1:8000/                    │
  │  Network:  http://182.178.1.42:8000/                 │
  ├──────────────────────────────────────────────────────┤
  │  ⚠  Anyone on your Wi-Fi can access this!            │
  └──────────────────────────────────────────────────────┘
```

---

## Features

| Feature | Details |
|---|---|
| **Zero config** | No changes to `settings.py` needed |
| **LAN IP auto-detection** | Uses the OS routing table — works on macOS, Linux & Windows |
| **ALLOWED_HOSTS injection** | Automatically adds the LAN IP at runtime |
| **CSRF_TRUSTED_ORIGINS** | Adds the correct `http://` origin so Django admin & POST forms work from mobile |
| **Static files** | Inherits from `staticfiles` runserver — your CSS/JS just works |
| **Auto-reload** | Subclasses Django's runserver — file watching & auto-restart included |
| **Offline-safe** | Gracefully falls back to `127.0.0.1` when no network is found |
| **No dependencies** | Only uses the Python standard library + Django itself |

---

## Installation

```bash
pip install django-netcast
```

Then add it to your `INSTALLED_APPS`:

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "netcast",
]
```

That's it. No middleware, no URLs, no database migrations.

---

## Usage

### Basic (default port 8000)

```bash
python manage.py share_local
```

### Custom port

```bash
python manage.py share_local 9000
```

### All standard runserver flags work

```bash
python manage.py share_local --noreload --nothreading
```

---

## How It Works

1. **Resolves your LAN IP** — Opens a dummy UDP socket to `8.8.8.8` (no data is sent) and reads which local interface the OS would route through.
2. **Patches `ALLOWED_HOSTS`** — Adds `0.0.0.0`, `127.0.0.1`, `localhost`, and your LAN IP in-memory so Django doesn't reject the request.
3. **Patches `CSRF_TRUSTED_ORIGINS`** — Adds `http://<LAN-IP>:<PORT>` so POST requests (forms, admin login) work from other devices without CSRF errors.
4. **Binds to `0.0.0.0`** — Tells the server to listen on all network interfaces instead of just localhost.
5. **Prints a clean banner** — Shows clickable local and network URLs, plus a security reminder.

> **Note:** All changes are **in-memory only** — your `settings.py` file is never modified.

---

## Security

This tool is designed **exclusively for local development**.

- It binds your server to all network interfaces (`0.0.0.0`).
- Anyone connected to the same Wi-Fi network can access your dev server.
- **Never** use this in production. Use a proper WSGI/ASGI server behind a reverse proxy instead.

---

## FAQ

### Does this modify my `settings.py`?

**No.** All changes happen in-memory at runtime. Your files are completely untouched.

### Does it work offline?

**Yes.** When no network is detected, it falls back to `127.0.0.1` and works like the normal `runserver`.

### Can I use this with Docker?

It's designed for bare-metal local development. Inside Docker, network exposure is typically handled by port mapping (`-p 8000:8000`).

### Does auto-reload still work?

**Yes.** `share_local` subclasses Django's own `runserver`, so file watching, auto-restart, and threading all behave exactly the same.

### Does it serve static files?

**Yes.** It inherits from the `staticfiles` variant of `runserver`, so `{% static %}` tags work out of the box during development.

---

## Compatibility

| | Supported |
|---|---|
| Python | 3.9, 3.10, 3.11, 3.12, 3.13 |
| Django | 4.2, 5.0, 5.1+ |
| OS | macOS, Linux, Windows |

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

```bash
# Clone the repo
git clone https://github.com/sagar9187/django-netcast.git
cd django-netcast

# Install in editable mode with test dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ❤️ for developers who test on their phones.
</p>

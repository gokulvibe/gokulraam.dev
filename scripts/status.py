#!/usr/bin/env python3
"""Ping the live-status endpoint from your laptop.

Usage:
    python3 scripts/status.py coding "vim · projects.py"
    python3 scripts/status.py court  "indoor session"
    python3 scripts/status.py afk

Reads creds from environment OR ~/.gokulraam-status:
    GOKULRAAM_STATUS_URL=https://api.gokulraam.dev/api/status   (or http://localhost:8000/api/status)
    GOKULRAAM_USERNAME=gokul
    GOKULRAAM_PASSWORD=<your admin password>

Optional macOS hook:
    Wire to Raycast / Alfred / Shortcuts → "Run shell script" with the desired
    `python3 scripts/status.py <state>` line.

Optional cron-based "what app am i in" reporter:
    Add to your crontab (every 5 min):
      */5 * * * * /path/to/scripts/status_cron.sh
    See README for a sample status_cron.sh that calls osascript.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
import urllib.parse
import http.cookiejar
from pathlib import Path

CONFIG_FILE = Path.home() / ".gokulraam-status"


def load_config() -> dict[str, str]:
    cfg: dict[str, str] = {}
    if CONFIG_FILE.exists():
        for line in CONFIG_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            cfg[k.strip()] = v.strip().strip('"').strip("'")
    # Environment overrides config file
    for key in ("GOKULRAAM_STATUS_URL", "GOKULRAAM_USERNAME", "GOKULRAAM_PASSWORD"):
        if key in os.environ:
            cfg[key] = os.environ[key]
    return cfg


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python3 scripts/status.py <state> [detail]", file=sys.stderr)
        print(__doc__.strip(), file=sys.stderr)
        return 2

    state = sys.argv[1]
    detail = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    cfg = load_config()
    base = cfg.get("GOKULRAAM_STATUS_URL", "http://localhost:8000/api/status")
    user = cfg.get("GOKULRAAM_USERNAME")
    pw = cfg.get("GOKULRAAM_PASSWORD")
    if not user or not pw:
        print(
            "Missing credentials. Create ~/.gokulraam-status with:\n"
            "  GOKULRAAM_STATUS_URL=https://api.gokulraam.dev/api/status\n"
            "  GOKULRAAM_USERNAME=gokul\n"
            "  GOKULRAAM_PASSWORD=<your admin password>\n",
            file=sys.stderr,
        )
        return 2

    # Derive the login URL from the status URL
    login_url = base.replace("/status", "/auth/login")

    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    # 1. Log in to get a session cookie
    login_body = json.dumps({"username": user, "password": pw}).encode("utf-8")
    req = urllib.request.Request(
        login_url, data=login_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with opener.open(req, timeout=10) as r:
            if r.status >= 400:
                print(f"login failed: HTTP {r.status}", file=sys.stderr)
                return 1
    except urllib.error.HTTPError as e:
        print(f"login failed: {e.code} {e.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"could not reach {login_url}: {e.reason}", file=sys.stderr)
        return 1

    # 2. Post the ping
    body = json.dumps({"state": state, "detail": detail}).encode("utf-8")
    req = urllib.request.Request(
        base, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with opener.open(req, timeout=10) as r:
            payload = json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"ping failed: {e.code} {e.reason}", file=sys.stderr)
        return 1

    print(f"✓ pinged · state={payload['state']!r} aliveness={payload['aliveness']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

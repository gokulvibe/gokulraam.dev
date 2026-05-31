"""Generate a bcrypt hash for the admin password.

Usage:
    python -m app.tools.hashpw 'your-password-here'
"""

import sys

from app.auth import hash_password


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python -m app.tools.hashpw 'your-password'", file=sys.stderr)
        return 1
    print(hash_password(sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

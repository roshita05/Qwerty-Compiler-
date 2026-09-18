#!/bin/sh
set -eu
cd "$(dirname "$0")"
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else "Python 3.11 or newer is required.")'
exec python3 -m qwerty web "$@"

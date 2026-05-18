#!/usr/bin/env bash
# crab wrapper — finds crab.py relative to the wrapper script, resolving symlinks
set -euo pipefail

# Resolve the wrapper script's real location, following symlinks
SOURCE="${BASH_SOURCE[0]}"
while [ -L "${SOURCE}" ]; do
    DIR="$(cd "$(dirname "${SOURCE}")" && pwd)"
    SOURCE="$(readlink "${SOURCE}")"
    [[ "${SOURCE}" != /* ]] && SOURCE="${DIR}/${SOURCE}"
done
CRAB_DIR="$(cd "$(dirname "${SOURCE}")" && pwd)"
CRAB_PY="${CRAB_DIR}/crab.py"

if [ ! -f "${CRAB_PY}" ]; then
    echo "Error: crab.py not found at ${CRAB_PY}" >&2
    echo "Expected crab.py in the same directory as the wrapper." >&2
    exit 1
fi

exec python3 "${CRAB_PY}" "$@"

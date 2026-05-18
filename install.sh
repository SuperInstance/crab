#!/usr/bin/env bash
set -euo pipefail

CRAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🐚 Installing crab — agent shell for repo entry/leave"

# Destination for the CLI wrapper
INSTALL_DIR="${INSTALL_DIR:-/usr/local/bin}"
CRAB_LINK="${INSTALL_DIR}/crab"

# Check prerequisites
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not found."
    exit 1
fi

# Create the wrapper script
WRAPPER="${CRAB_DIR}/crab-wrapper.sh"
cat > "${WRAPPER}" << 'WRAPPEREOF'
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
WRAPPEREOF
chmod +x "${WRAPPER}"

# Create symlink
if [ -L "${CRAB_LINK}" ] || [ -f "${CRAB_LINK}" ]; then
    echo "  Removing existing: ${CRAB_LINK}"
    rm -f "${CRAB_LINK}"
fi

ln -s "${WRAPPER}" "${CRAB_LINK}"
echo "  Symlinked: ${CRAB_LINK} → ${WRAPPER}"

# Verify
echo -n "  Verifying: "
if "${CRAB_LINK}" --version &>/dev/null; then
    echo "✅ crab installed successfully"
    "${CRAB_LINK}" --version
else
    echo "❌ Installation verification failed"
    exit 1
fi

# Optional: install Python dependencies
if [ -f "${CRAB_DIR}/requirements.txt" ]; then
    echo "  Installing Python dependencies..."
    pip3 install -r "${CRAB_DIR}/requirements.txt" -q 2>/dev/null || true
fi

# Shell completion hint
echo ""
echo "  🔧 Shell completion:"
echo "     Bash:  eval \"\$(${CRAB_LINK} completions bash)\""
echo "     Zsh:   eval \"\$(${CRAB_LINK} completions zsh)\""
echo ""
echo "  Quick start:"
echo "     crab list"
echo "     crab enter ~/.openclaw/workspace/arch-sw"
echo "     crab whoami"
echo "     crab leave"
echo ""

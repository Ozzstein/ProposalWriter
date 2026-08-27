#!/bin/bash
# Launcher: export every string value in secrets.json (repo root, gitignored)
# as an environment variable, then exec the given command.
#
#   usage: with_secrets.sh <command> [args...]
#
# Used by .claude/settings.json to start MCP servers so that API keys live in
# ONE local file instead of being scattered through settings. Also substitutes
# the project venv's python for `python3` when .venv/ exists (PEP 668 setups).
# Missing secrets.json is fine — the command just runs without the extra env.

here="$(cd "$(dirname "$0")/.." && pwd)"

if [ -f "$here/secrets.json" ]; then
  eval "$(python3 - "$here/secrets.json" <<'PYEOF'
import json, sys, shlex
try:
    data = json.load(open(sys.argv[1]))
except Exception as e:
    print(f'echo "with_secrets: cannot parse secrets.json: {e}" >&2')
else:
    for k, v in data.items():
        if isinstance(v, str) and not k.startswith("_"):
            print(f"export {k}={shlex.quote(v)}")
PYEOF
)"
fi

cmd="$1"; shift
if [ "$cmd" = "python3" ] && [ -x "$here/.venv/bin/python" ]; then
  cmd="$here/.venv/bin/python"
fi
exec "$cmd" "$@"

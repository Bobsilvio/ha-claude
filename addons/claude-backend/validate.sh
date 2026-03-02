#!/bin/bash
# Validate Python files for syntax errors and SyntaxWarnings before commit
set -e
ADDON_DIR="$(dirname "$0")"
FAIL=0

for f in "$ADDON_DIR"/*.py; do
  result=$(python3 -W error::SyntaxWarning -c "
with open('$f') as fh:
    src = fh.read()
compile(src, '$f', 'exec')
print('OK')
" 2>&1)
  if [ "$result" != "OK" ]; then
    echo "FAIL: $f"
    echo "$result"
    FAIL=1
  else
    echo "OK:   $f"
  fi
done

exit $FAIL

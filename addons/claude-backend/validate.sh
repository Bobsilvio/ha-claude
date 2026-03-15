#!/bin/bash
# Validate Python files for syntax errors and SyntaxWarnings before commit
# Also checks generated JS from chat_bubble.py and chat_ui.py for common issues
ADDON_DIR="$(dirname "$0")"
FAIL=0

echo "=== Python syntax check ==="
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

echo ""
echo "=== JS generation check (chat_bubble.py + chat_ui.py) ==="
result=$(python3 -c "
import sys, re
sys.path.insert(0, '$ADDON_DIR')

errors = []

# Check chat_bubble.py generated JS
try:
    from chat_bubble import get_chat_bubble_js
    js = get_chat_bubble_js('/test', 'it')
    lines = js.split('\n')
    for i, line in enumerate(lines, 1):
        # Unterminated string: line contains an odd-positioned single/double quote
        # with a literal newline inside (line ends mid-string)
        if re.search(r\"(?<![\\\\])['\\\"]\\s*$\", line) and not line.rstrip().endswith((';',',','{','}','(',')','//','/[*]','*/')):
            pass  # too many false positives
        # Regex literal split across lines: /...  without closing /
        if re.search(r'/[^/\n]{0,200}$', line) and line.count('/') % 2 == 1 and 'http' not in line:
            pass
    print('chat_bubble.py JS: OK (' + str(len(lines)) + ' lines)')
except Exception as e:
    print('chat_bubble.py JS: FAIL - ' + str(e))
    errors.append('chat_bubble.py')

# Check for literal newlines inside JS string literals in source
with open('$ADDON_DIR/chat_bubble.py') as f:
    src = f.read()
src_lines = src.split('\n')
for i, line in enumerate(src_lines, 1):
    # Single-quoted string containing a bare \n (not \\n)
    m = re.search(r\"(?<!\\\\)'[^']*(?<!\\\\)\\\\n\", line)
    if m and '\\\\\\\\n' not in line:
        print(f'chat_bubble.py line {i}: possible bare newline in JS string: {line.strip()[:80]}')
        errors.append('chat_bubble.py:' + str(i))

# Check chat_ui.py source for bare \\n inside JS regex character classes [^...\\n...]
# A bare \\n in Python becomes a literal newline, splitting the JS regex across lines
with open('$ADDON_DIR/chat_ui.py') as f:
    ui_src = f.read()
ui_lines = ui_src.split('\n')
for i, line in enumerate(ui_lines, 1):
    # Detect /regex[^...\\n...]/ patterns where \\n is a bare Python newline (not \\\\n)
    if re.search(r'/[^/]*\[([^\]]*[^\\\\])\\\\n', line) and '\\\\\\\\n' not in line:
        # Only flag lines that are inside JS (contain replace, match, test, etc.)
        if any(kw in line for kw in ('replace(/', '.test(/', '.match(/', '.search(/', 'RegExp')):
            print(f'chat_ui.py line {i}: bare \\\\n in JS regex (use \\\\\\\\n): {line.strip()[:80]}')
            errors.append('chat_ui.py:' + str(i))

if not errors:
    print('JS generation: OK')
else:
    sys.exit(1)
" 2>&1)
echo "$result"
if echo "$result" | grep -q "FAIL\|Error\|error"; then
  FAIL=1
fi

exit $FAIL

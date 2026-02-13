#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, 'addons/claude-backend')
os.environ['HA_URL'] = 'http://localhost'
os.environ['DEBUG_MODE'] = 'False'

# Import api which includes ui_main_js()
import api

# Get the actual output of ui_main_js()
js_response = api.ui_main_js()
js_code = js_response[0]  # First element is the JS code

print(f"✓ Estratto JS from ui_main_js(): {len(js_code)} chars\n")

# Check for syntax errors using Node.js
import subprocess
with open('/tmp/extracted_ui_main_from_api.js', 'w') as f:
    f.write(js_code)

try:
    result = subprocess.run(
        ['node', '-c', '/tmp/extracted_ui_main_from_api.js'],
        capture_output=True,
        timeout=5,
        text=True
    )
    if result.returncode == 0:
        print("✅ Node.js syntax check: OK - NO ERRORS!")
        print("\nThe JavaScript is valid and should execute correctly.")
    else:
        print(f"❌ Node.js syntax error:\n{result.stderr[:500]}")
except FileNotFoundError:
    print("⚠️  Node.js not installed, skipping syntax check")
except Exception as e:
    print(f"⚠️  Node.js check failed: {e}")

# Basic checks
if 'handleButtonClick' in js_code:
    print("  ✓ handleButtonClick is defined")
else:
    print("  ❌ handleButtonClick NOT found")

if 'loadChatList' in js_code:
    print("  ✓ loadChatList is defined")
else:
    print("  ❌ loadChatList NOT found")

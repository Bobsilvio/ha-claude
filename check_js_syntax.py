#!/usr/bin/env python3
import sys
import os
import re

sys.path.insert(0, 'addons/claude-backend')
os.environ['HA_URL'] = 'http://localhost'
os.environ['DEBUG_MODE'] = 'False'

import chat_ui

html = chat_ui.get_chat_ui()

# Estrai il JavaScript inline con il nuovo regex
m = re.search(r'<script(?!\s+src\s*=)[^>]*>\s*(.*?)\s*</script>', html, flags=re.S | re.I)
if not m:
    print("❌ Regex non matcha!")
    sys.exit(1)

js_code = m.group(1)
print(f"✓ Estratto JS: {len(js_code)} chars\n")

# Cerca gli errori comuni
print("=" * 60)
print("Checking for common JavaScript syntax issues")
print("=" * 60)

# Controlla il conteggio delle parentesi
opens = js_code.count('{')
closes = js_code.count('}')
print(f"Parentesi graffe: {{ = {opens}, }} = {closes}")
if opens != closes:
    print(f"  ⚠️  ERRORE: mismatch! ({opens} aperte vs {closes} chiuse)")

# Controlla le parentesi quadre
opens_sq = js_code.count('[')
closes_sq = js_code.count(']')
print(f"Parentesi quadre: [ = {opens_sq}, ] = {closes_sq}")
if opens_sq != closes_sq:
    print(f"  ⚠️  ERRORE: mismatch! ({opens_sq} aperte vs {closes_sq} chiuse)")

# Controlla le parentesi tonde
opens_r = js_code.count('(')
closes_r = js_code.count(')')
print(f"Parentesi tonde: ( = {opens_r}, ) = {closes_r}")
if opens_r != closes_r:
    print(f"  ⚠️  ERRORE: mismatch! ({opens_r} aperte vs {closes_r} chiuse)")

print()
print("=" * 60)
print("Checking for function definitions")
print("=" * 60)

# Cerca le definizioni di funzione
functions = re.findall(r'\b(?:function|const|let|var)\s+(\w+)\s*[\s=]*(?:function|\()', js_code)
print(f"Funzioni trovate: {len(functions)}")
if 'handleButtonClick' in js_code:
    print("  ✓ handleButtonClick presente nel codice")
else:
    print("  ❌ handleButtonClick NON trovato!")

if 'loadChatList' in js_code:
    print("  ✓ loadChatList presente nel codice")
else:
    print("  ❌ loadChatList NON trovato!")

if 'sendMessage' in js_code:
    print("  ✓ sendMessage presente nel codice")
else:
    print("  ❌ sendMessage NON trovato!")

print()
print("=" * 60)
print("Checking for common issues in extracted code")
print("=" * 60)

# Controlla se ci sono problemi di quote/apostrofi
single_quotes = js_code.count("'")
double_quotes = js_code.count('"')
backticks = js_code.count('`')
print(f"Quotes: ' = {single_quotes}, \" = {double_quotes}, ` = {backticks}")

# Cerca linee problematiche (vuote dopo una parentesi aperta)
if re.search(r'{[\s\n]*}', js_code):
    print("  ⚠️  Trovate parentesi graffe vuote {}")

# Scrivi il JS in un file per analisi manuale
with open('/tmp/extracted_ui_main.js', 'w') as f:
    f.write(js_code)
print(f"\n✓ JavaScript estratto salvato in: /tmp/extracted_ui_main.js")
print("  Puoi testarlo con: node /tmp/extracted_ui_main.js")

# Prova un parsing minimale con Node.js se disponibile
import subprocess
try:
    result = subprocess.run(
        ['node', '-c', '/tmp/extracted_ui_main.js'],
        capture_output=True,
        timeout=5,
        text=True
    )
    if result.returncode == 0:
        print("  ✓ Node.js syntax check: OK")
    else:
        print(f"  ❌ Node.js syntax error: {result.stderr[:200]}")
except Exception as e:
    print(f"  ⚠️  Node.js check skipped: {e}")

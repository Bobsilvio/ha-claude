import yaml, re

with open('config.yaml') as f:
    raw = f.read()
schema_match = re.search(r'^schema:(.*?)^(?:documentation|support|maintainers)', raw, re.MULTILINE | re.DOTALL)
schema_keys = set(re.findall(r'^  (\w+):', schema_match.group(1), re.MULTILINE)) if schema_match else set()

for lang in ['it', 'en', 'es', 'fr']:
    trans = yaml.safe_load(open(f'translations/{lang}.yaml'))
    trans_keys = set(trans.get('configuration', {}).keys())
    missing = schema_keys - trans_keys
    extra = trans_keys - schema_keys
    status = 'OK' if not missing and not extra else 'PROBLEMA'
    print(f'[{status}] {lang}.yaml  schema={len(schema_keys)}  trans={len(trans_keys)}')
    for k in sorted(missing): print(f'       MANCANTE: {k}')
    for k in sorted(extra):   print(f'       EXTRA:    {k}')

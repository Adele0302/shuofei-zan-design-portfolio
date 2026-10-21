"""Generate a local .env with random, distinct editor and reviewer secrets."""
import json
import os
import secrets
from pathlib import Path

file=Path('.env')
if file.exists():
    print('.env already exists; no file was overwritten.');raise SystemExit(0)
editor=secrets.token_urlsafe(32)
reviewer=secrets.token_urlsafe(32)
keys={editor:{'workspace':'demo','role':'editor','name':'Local Editor'},
      reviewer:{'workspace':'demo','role':'reviewer','name':'Local Reviewer'}}
envs=['APP_DB_PATH=./local_data/knowledge_v2.sqlite3',
      "APP_API_KEYS='"+json.dumps(keys,separators=(',',':'))+"'",
      'EMBEDDING_BACKEND=off','MCP_PROTOCOL=auto']
with file.open('x',encoding='utf-8') as f:f.write('\n'.join(envs)+'\n')
try:os.chmod(file,0o600)
except OSError:pass
print('Local-only .env created. Never commit this file.')
print('EDITOR KEY:',editor)
print('REVIEWER KEY:',reviewer)
print('Keys can be reused via .env; this script does not print them again.')

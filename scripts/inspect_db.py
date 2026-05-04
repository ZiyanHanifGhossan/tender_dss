import sqlite3
from pathlib import Path
p = Path(__file__).parent.parent / 'database' / 'tender.db'
print('DB_PATH', p)
if not p.exists():
    print('Database file not found')
    raise SystemExit(1)
conn = sqlite3.connect(p)
cur = conn.cursor()
try:
    cnt = cur.execute('SELECT count(*) FROM tender').fetchone()[0]
    print('COUNT', cnt)
    cols = [d[1] for d in cur.execute('PRAGMA table_info(tender)').fetchall()]
    print('COLUMNS', cols)
    rows = cur.execute('SELECT id, project_name, nomor_tender, input_date FROM tender ORDER BY id DESC LIMIT 10').fetchall()
    print('LAST10')
    for r in rows:
        print(r)
except Exception as e:
    print('ERROR', e)
finally:
    conn.close()
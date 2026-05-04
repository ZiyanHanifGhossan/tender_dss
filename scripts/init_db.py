"""Initialization script for the Tender DSS project.

- Ensures DB tables and schema are present (including `outcome` column).
- Optionally inserts a few sample records for manual testing.

Usage:
    python scripts/init_db.py
"""
from modules import db
import datetime

if __name__ == '__main__':
    print('Ensuring database tables and columns...')
    db.create_table()
    db.ensure_outcome_column()
    print('Done: table and outcome column ensured.')

    n_labeled = len(db.get_labeled_tenders())
    print(f'Current labeled records: {n_labeled}')
    if n_labeled == 0:
        print('Inserting example labeled records (10) for testing...')
        conn = db.get_connection()
        cur = conn.cursor()
        for i in range(10):
            cur.execute(
                "INSERT INTO tender (project_name, client, nomor_tender, sumber_tender, wk_migas, jenis_tender, nilai_proyek, nilai_hps, durasi, kompleksitas, risiko, kesiapan_sertifikat, status_tender, outcome, user, input_date) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (f'Example {i}', 'Client', f'EX{i}', 'Open Tender', 'WK-1', 'EPC', 5.0 + i, 2.0, 6 + i, 3 + (i % 4), 2 + (i % 3), 'Siap', 'Identified', 'Menang' if i % 2 == 0 else 'Kalah', 'system', datetime.date.today().isoformat())
            )
        conn.commit()
        conn.close()
        print('Inserted 10 labeled records.')
    else:
        print('Labeled data already present - skipping sample insert.')
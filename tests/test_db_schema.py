import os
from modules import db


def test_outcome_column_exists():
    # Ensure schema migration helper works
    db.create_table()
    db.ensure_outcome_column()
    # If no exception, column exists (DB returns rows safely)
    rows = db.get_tenders_with_outcome()
    assert isinstance(rows, list)


def test_set_and_get_outcome():
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO tender (project_name, client, nomor_tender, sumber_tender, wk_migas, jenis_tender, nilai_proyek, nilai_hps, durasi, kompleksitas, risiko, kesiapan_sertifikat, status_tender, user, input_date) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ('T-Schema','C','N-S','SKK','WK','EPC',1.0,1.0,1,1,1,'Siap','Identified', 'test_user', '2025-01-01'))
    conn.commit()
    tid = cur.lastrowid
    conn.close()

    db.set_tender_outcome(tid, 'Menang')
    row = db.get_tender_by_id(tid)
    # get_tender_by_id returns without outcome to keep backward compatibility; check via get_tenders_with_outcome
    rows = db.get_tenders_with_outcome()
    matched = [r for r in rows if r[0] == tid]
    assert len(matched) == 1
    assert matched[0][6] == 'Menang'
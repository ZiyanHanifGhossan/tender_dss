import sqlite3

import os

DB_PATH = os.environ.get("TENDER_DB_PATH", "database/tender.db")

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def create_table():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tender (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT,
        client TEXT,
        nomor_tender TEXT,
        sumber_tender TEXT,
        wk_migas TEXT,
        jenis_tender TEXT,
        nilai_proyek REAL,
        nilai_hps REAL,
        durasi INTEGER,
        kompleksitas INTEGER,
        risiko INTEGER,
        kesiapan_sertifikat TEXT,
        status_tender TEXT,
        user TEXT,
        input_date TEXT
    )
    """)

    conn.commit()
    conn.close()

    # Ensure schema has expected columns
    ensure_outcome_column()
    ensure_meta_columns()


def ensure_outcome_column():
    """Add an 'outcome' column to tender table if it's missing.
    Values: 'Menang', 'Kalah', or NULL/None"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(tender)")
    cols = [r[1] for r in cur.fetchall()]
    if 'outcome' not in cols:
        cur.execute("ALTER TABLE tender ADD COLUMN outcome TEXT")
        conn.commit()
    conn.close()


def ensure_meta_columns():
    """Ensure 'user' and 'input_date' columns exist (migration helper)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(tender)")
    cols = [r[1] for r in cur.fetchall()]
    if 'user' not in cols:
        cur.execute("ALTER TABLE tender ADD COLUMN user TEXT")
    if 'input_date' not in cols:
        cur.execute("ALTER TABLE tender ADD COLUMN input_date TEXT")
    conn.commit()
    conn.close()


def get_tenders():
    """Return list of tenders as tuples:
    (id, project_name, nilai_proyek, durasi, kompleksitas, risiko, user, input_date)
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, project_name, nilai_proyek, durasi, kompleksitas, risiko, user, input_date
        FROM tender
        ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_tenders_with_outcome():
    """Return tenders including the outcome column:
    (id, project_name, nilai_proyek, durasi, kompleksitas, risiko, outcome, user, input_date)
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, project_name, nilai_proyek, durasi, kompleksitas, risiko, outcome, user, input_date
        FROM tender
        ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_labeled_tenders():
    """Return tenders that have an outcome label"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, project_name, nilai_proyek, durasi, kompleksitas, risiko, outcome, user, input_date
        FROM tender
        WHERE outcome IS NOT NULL
        ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_tender_by_id(tender_id):
    """Return single tender row or None (includes user and input_date)"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, project_name, nilai_proyek, durasi, kompleksitas, risiko, user, input_date
        FROM tender
        WHERE id = ?
    """, (tender_id,))
    row = cur.fetchone()
    conn.close()
    return row


def delete_tender(tender_id):
    """Delete a tender by id"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tender WHERE id = ?", (tender_id,))
    conn.commit()
    conn.close()


def set_tender_outcome(tender_id, outcome):
    """Set outcome for a tender (e.g., 'Menang' or 'Kalah')"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tender SET outcome = ? WHERE id = ?", (outcome, tender_id))
    conn.commit()
    conn.close()

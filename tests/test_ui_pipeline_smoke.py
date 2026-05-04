import os
import subprocess
import time
import tempfile
import requests
import sqlite3
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
PYTHON = sys.executable


import threading

def _start_streamlit(port, env):
    cmd = [PYTHON, "-m", "streamlit", "run", "app.py", "--server.port", str(port), "--server.headless", "true"]
    proc = subprocess.Popen(cmd, cwd=PROJECT_ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # start a thread to collect stderr lines
    stderr_lines = []
    def _read_stderr():
        try:
            for line in proc.stderr:
                stderr_lines.append(line)
        except Exception:
            pass
    t = threading.Thread(target=_read_stderr, daemon=True)
    t.start()

    # wait for server to be ready
    deadline = time.time() + 20
    url = f"http://localhost:{port}"
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=1)
            if r.status_code == 200:
                return proc, url, stderr_lines
        except Exception:
            time.sleep(0.5)
    # if not ready, capture logs
    proc.kill()
    raise RuntimeError(f"Streamlit did not start in time. stderr: {''.join(stderr_lines)}")


def _stop_streamlit(proc):
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        proc.kill()


def test_pipeline_page_with_sample_data(tmp_path):
    # create temp db and initialize with sample labeled data (in-process to avoid subprocess import issues)
    db_path = str(tmp_path / "tender_sample.db")
    os.environ["TENDER_DB_PATH"] = db_path

    # initialize db and insert sample labeled records similar to scripts/init_db.py
    from modules import db as _db
    _db.create_table()
    conn = _db.get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tender")
    for i in range(6):
        cur.execute(
            "INSERT INTO tender (project_name, client, nomor_tender, sumber_tender, wk_migas, jenis_tender, nilai_proyek, nilai_hps, durasi, kompleksitas, risiko, kesiapan_sertifikat, status_tender, outcome, user, input_date) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (f'Example {i}', 'Client', f'EX{i}', 'Open Tender', 'WK-1', 'EPC', 5.0 + i, 2.0, 6 + i, 3 + (i % 4), 2 + (i % 3), 'Siap', 'Identified', 'Menang' if i % 2 == 0 else 'Kalah', 'system', '2026-01-01')
        )
    conn.commit()
    conn.close()

    proc, url, logs = _start_streamlit(port=8505, env=os.environ.copy())
    try:
        r = requests.get(url, timeout=5)
        assert r.status_code == 200
        # ensure server did not log uncaught exceptions
        joined = ''.join(logs)
        assert 'Uncaught app execution' not in joined
    finally:
        _stop_streamlit(proc)


def test_pipeline_page_with_empty_db(tmp_path):
    db_path = str(tmp_path / "tender_empty.db")
    env = os.environ.copy()
    env["TENDER_DB_PATH"] = db_path

    # create table only
    subprocess.run([PYTHON, "-c", "from modules import db; db.create_table()"], cwd=PROJECT_ROOT, env=env, check=True)

    proc, url, logs = _start_streamlit(port=8506, env=os.environ.copy())
    try:
        r = requests.get(url, timeout=5)
        assert r.status_code == 200
        joined = ''.join(logs)
        # pipeline page should not crash (no uncaught exceptions in logs)
        assert 'Uncaught app execution' not in joined
    finally:
        _stop_streamlit(proc)


def test_pipeline_page_with_minimal_schema(tmp_path):
    db_path = str(tmp_path / "tender_min.db")
    # create minimal table schema with only id and project_name
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE tender (id INTEGER PRIMARY KEY AUTOINCREMENT, project_name TEXT)")
    conn.commit()
    conn.close()

    env = os.environ.copy()
    env["TENDER_DB_PATH"] = db_path

    proc, url, logs = _start_streamlit(port=8507, env=env)
    try:
        r = requests.get(url, timeout=5)
        assert r.status_code == 200
        joined = ''.join(logs)
        # should not contain server-side uncaught exceptions
        assert 'Uncaught app execution' not in joined
    finally:
        _stop_streamlit(proc)

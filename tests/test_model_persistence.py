import os
from modules import ml_model, db


def test_model_file_exists_and_info():
    # Ensure model file is available after initialization
    assert ml_model.is_model_available() is True
    info = ml_model.get_model_info()
    assert 'coef_orig' in info and 'intercept_orig' in info


def test_retrain_from_db_smoke():
    # Ensure there are at least some labeled records
    labeled = db.get_labeled_tenders()
    if len(labeled) < 6:
        conn = db.get_connection(); cur = conn.cursor()
        for i in range(6):
            cur.execute("INSERT INTO tender (project_name, client, nomor_tender, sumber_tender, wk_migas, jenis_tender, nilai_proyek, nilai_hps, durasi, kompleksitas, risiko, kesiapan_sertifikat, status_tender, outcome, user, input_date) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (f'AutoTest{i}','C','NT'+str(i),'SKK','WK','EPC', 10+i%5, 2.0, 6+i%3, 3+i%4, 2+i%3, 'Siap','Identified', 'Menang' if i%2==0 else 'Kalah', 'test_user', '2025-01-01'))
        conn.commit(); conn.close()
        labeled = db.get_labeled_tenders()

    metrics = ml_model.retrain_from_db(db.get_labeled_tenders, test_size=0.2)
    assert 'n_samples' in metrics
    assert metrics['n_samples'] >= 6
    assert 'accuracy' in metrics
    assert ml_model.is_model_available() is True
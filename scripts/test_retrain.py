from modules import db, ml_model
# Ensure DB schema exists and includes migration-added columns
# (helps tests run reliably on fresh or older DB files)
db.create_table()

labeled = db.get_labeled_tenders()
print('labelled count:', len(labeled))
if len(labeled) < 20:
    conn = db.get_connection(); cur = conn.cursor()
    for i in range(30):
        cur.execute("INSERT INTO tender (project_name, client, nomor_tender, sumber_tender, wk_migas, jenis_tender, nilai_proyek, nilai_hps, durasi, kompleksitas, risiko, kesiapan_sertifikat, status_tender, outcome, user, input_date) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (f'Auto{i}','C','N'+str(i),'SKK','WK','EPC', 10+i%5, 2.0, 6+i%3, 3+i%4, 2+i%3, 'Siap','Identified', 'Menang' if i%2==0 else 'Kalah', 'test_user', '2025-01-01'))
    conn.commit(); conn.close()
    labeled = db.get_labeled_tenders()
    print('inserted, new labelled count:', len(labeled))

metrics = ml_model.retrain_from_db(db.get_labeled_tenders, test_size=0.2)
print('retrain metrics:', metrics)
print('model file exists:', ml_model.is_model_available())
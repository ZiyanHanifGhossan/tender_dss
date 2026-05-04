import streamlit as st
from modules.db import get_connection, get_tenders, delete_tender, get_tenders_with_outcome, set_tender_outcome, get_labeled_tenders
from modules.ml_model import retrain_from_db, get_model_info, is_model_available
from datetime import date


def safe_rerun():
    """Try to rerun the Streamlit app in a way compatible with multiple versions."""
    try:
        st.experimental_rerun()
    except Exception:
        # Try locations for RerunException across Streamlit versions
        try:
            from streamlit.runtime.scriptrunner.script_runner import RerunException
            raise RerunException
        except Exception:
            try:
                from streamlit.script_runner import RerunException
                raise RerunException
            except Exception:
                st.info("Perubahan disimpan. Silakan refresh halaman untuk melihat pembaruan.")
                st.stop()

st.header("📥 Tender Identification (SKK Migas / KKKS)")

project = st.text_input("Nama Proyek")
client = st.text_input("Client / KKKS")
nomor = st.text_input("Nomor Tender")

sumber = st.selectbox(
    "Sumber Tender",
    ["SKK Migas", "KKKS", "Open Tender"]
)

wk = st.text_input("Wilayah Kerja (WK Migas)")
jenis = st.selectbox(
    "Jenis Tender",
    ["Fabrication", "EPC", "Maintenance", "Jasa Engineering"]
)

nilai = st.number_input("Nilai Proyek (Rp Miliar)", min_value=0.0)
hps = st.number_input("Nilai HPS (Rp Miliar)", min_value=0.0)
durasi = st.number_input("Durasi Proyek (bulan)", min_value=1)

kompleksitas = st.slider("Kompleksitas Teknis", 1, 10)
risiko = st.slider("Risiko Proyek", 1, 10)

sertifikat = st.selectbox(
    "Kesiapan Sertifikat (ISO / ASME / TKDN)",
    ["Siap", "Perlu Update", "Tidak Siap"]
)

user = st.text_input("User (siapa yang menginput)")
input_date = st.date_input("Tanggal Input", value=date.today())

if st.button("💾 Simpan Tender"):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO tender (
            project_name, client, nomor_tender, sumber_tender, wk_migas,
            jenis_tender, nilai_proyek, nilai_hps, durasi,
            kompleksitas, risiko, kesiapan_sertifikat, status_tender, user, input_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        project, client, nomor, sumber, wk,
        jenis, nilai, hps, durasi,
        kompleksitas, risiko, sertifikat,
        "Identified", user, input_date.isoformat()
    ))

    conn.commit()
    conn.close()

    st.success("✅ Tender berhasil diidentifikasi")

# -------------------------------------------------
# Bagian Hapus Tender
# -------------------------------------------------
st.markdown("---")
st.header("🗑️ Hapus Tender")

tenders = get_tenders()
if not tenders:
    st.info("Belum ada tender tersimpan untuk dihapus.")
else:
    options = [f"{r[0]} - {r[1]} (Rp {r[2]} M)" for r in tenders]
    sel = st.selectbox("Pilih Tender untuk dihapus", options, key='del_sel')
    sel_index = options.index(sel)
    tender_row = tenders[sel_index]

    st.markdown(f"**Project:** {tender_row[1]}  \n**Nilai:** Rp {tender_row[2]} M  \n**Durasi:** {tender_row[3]} bulan  \n**Kompleksitas:** {tender_row[4]}  \n**Risiko:** {tender_row[5]}  \n**User:** {tender_row[6] if len(tender_row) > 6 else ''}  \n**Tanggal Input:** {tender_row[7] if len(tender_row) > 7 else ''}")

    confirm = st.checkbox("Saya yakin ingin menghapus tender ini")
    if st.button("🗑️ Hapus Tender"):
        if confirm:
            delete_tender(tender_row[0])
            st.success("✅ Tender berhasil dihapus")
            safe_rerun()
        else:
            st.warning("Centang konfirmasi sebelum menghapus.")


# -------------------------------------------------
# Bagian Tandai Hasil Tender
# -------------------------------------------------
st.markdown("---")
st.header("📝 Tandai Hasil Tender")

all_tenders = get_tenders_with_outcome()
if not all_tenders:
    st.info("Belum ada tender tersimpan untuk ditandai.")
else:
    options2 = [f"{r[0]} - {r[1]} (Rp {r[2]} M) - Outcome: {r[6] if r[6] else 'Belum'}" for r in all_tenders]
    sel2 = st.selectbox("Pilih Tender untuk ditandai", options2, key='label_sel')
    sel2_index = options2.index(sel2)
    tr = all_tenders[sel2_index]

    st.markdown(f"**Project:** {tr[1]}  \n**Nilai:** Rp {tr[2]} M  \n**Durasi:** {tr[3]} bulan  \n**Kompleksitas:** {tr[4]}  \n**Risiko:** {tr[5]}  \n**Outcome saat ini:** {tr[6] if tr[6] else 'Belum'}  \n**User:** {tr[7] if len(tr) > 7 else ''}  \n**Tanggal Input:** {tr[8] if len(tr) > 8 else ''}")

    outcome = st.radio("Pilih hasil tender", ["Menang", "Kalah", "Belum"], index=0)
    if st.button("💾 Simpan Hasil Tender"):
        sel_out = None if outcome == 'Belum' else outcome
        set_tender_outcome(tr[0], sel_out)
        st.success("✅ Hasil tender diperbarui")
        safe_rerun()


# -------------------------------------------------
# Bagian Retrain Model
# -------------------------------------------------
st.markdown("---")
st.header("🔁 Retrain Model (dengan Evaluasi)")

labeled = get_labeled_tenders()
if not labeled:
    st.info("Belum ada data berlabel. Tandai beberapa tender sebagai 'Menang' atau 'Kalah' terlebih dahulu.")
else:
    n_total = len(labeled)
    n_pos = sum(1 for r in labeled if r[6] == 'Menang')
    n_neg = sum(1 for r in labeled if r[6] == 'Kalah')
    st.write(f"Data berlabel: {n_total} (Menang: {n_pos}, Kalah: {n_neg})")

    test_size = st.slider("Proporsi test set untuk evaluasi", 5, 50, 20)
    show_coef = st.checkbox("Tampilkan koefisien model setelah retrain")

    if st.button("🔁 Retrain dan Evaluasi"):
        if n_total < 10:
            st.warning("Disarankan memiliki setidaknya 10 contoh berlabel untuk retrain; lanjutkan dengan hati-hati.")
        with st.spinner("Melatih model..."):
            metrics = retrain_from_db(get_labeled_tenders, test_size=test_size/100.0)
        if 'error' in metrics:
            st.error(metrics['error'])
        else:
            st.success("✅ Retrain selesai dan model tersimpan ke disk")
            st.write("**Metrik evaluasi:**")
            st.write(f"- Jumlah sampel: {metrics['n_samples']}")
            st.write(f"- Train / Test: {metrics['n_train']} / {metrics['n_test']}")
            st.write(f"- Accuracy: {metrics['accuracy']:.4f}")
            if metrics['auc'] is not None:
                st.write(f"- AUC: {metrics['auc']:.4f}")
            st.write("**Confusion Matrix (test set)**")
            st.write(metrics['confusion_matrix'])

            if show_coef:
                info = get_model_info()
                st.subheader("Koefisien (skala asli)")
                features = ['nilai_proyek', 'durasi', 'kompleksitas', 'risiko']
                for name, c in zip(features, info['coef_orig']):
                    st.write(f"- {name}: {c:.6f}")
                st.write(f"Intercept: {info['intercept_orig']:.6f}")

            # show model availability
            st.caption("Model file tersimpan: " + ("Ya" if is_model_available() else "Tidak"))

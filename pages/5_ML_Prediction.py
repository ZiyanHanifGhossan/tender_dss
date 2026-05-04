import streamlit as st
from modules.ml_model import predict_win_probability
from modules.db import get_tenders, get_tender_by_id

st.header("🤖 Win Probability Prediction")

st.markdown("""
Prediksi peluang kemenangan tender menggunakan
**Machine Learning (Logistic Regression)**.
""")

# Pilihan sumber data: manual atau dari tender yang sudah disimpan
# Allow preselecting a stored tender via query param (tender_nomor)
q = st.query_params
preselect_nomor = None
if 'tender_nomor' in q:
    # st.query_params exposes lists for values
    preselect_nomor = q['tender_nomor'][0]
# Fallback: if Streamlit version doesn't support setting query params, check session_state hint
if preselect_nomor is None and 'preselect_nomor_hint' in st.session_state:
    preselect_nomor = st.session_state.pop('preselect_nomor_hint')

data_source = st.radio("Sumber Data", ["Manual Input", "Gunakan Tender yang tersimpan"], index=0)
# If a tender_nomor is passed, switch to stored tender mode
if preselect_nomor is not None:
    data_source = "Gunakan Tender yang tersimpan"

if data_source == "Manual Input":
    nilai = st.number_input("Nilai Proyek (Rp Miliar)", min_value=0.0)
    durasi = st.number_input("Durasi Proyek (bulan)", min_value=1)
    kompleksitas = st.slider("Kompleksitas Teknis", 1, 10)
    risiko = st.slider("Risiko Proyek", 1, 10)
else:
    tenders = get_tenders()
    if not tenders:
        st.info("Tidak ada tender tersimpan. Silakan identifikasi tender di menu 'Input Tender' atau gunakan input manual.")
        # fallback ke manual input
        nilai = st.number_input("Nilai Proyek (Rp Miliar)", min_value=0.0)
        durasi = st.number_input("Durasi Proyek (bulan)", min_value=1)
        kompleksitas = st.slider("Kompleksitas Teknis", 1, 10)
        risiko = st.slider("Risiko Proyek", 1, 10)
    else:
        options = [f"{r[0]} - {r[1]} (Rp {r[2]} M)" for r in tenders]

        # If preselect_nomor is provided, try to select matching tender by nomor_tender
        sel = None
        sel_index = 0
        if preselect_nomor is not None:
            for i, r in enumerate(tenders):
                # tender rows stored as (id, project_name, nilai_proyek, durasi, kompleksitas, risiko, ...), nomor may be at index 8 or elsewhere; try to find
                try:
                    # Search by nomor_tender column if present in DB row tuple
                    if len(r) > 8 and str(r[8]) == str(preselect_nomor):
                        sel_index = i
                        sel = options[i]
                        break
                except Exception:
                    pass
        if sel is None:
            sel = st.selectbox("Pilih Tender", options)
            sel_index = options.index(sel)
        else:
            # show selected tender info
            st.write(f"Terpilih melalui Pipeline: {sel}")

        tender_row = tenders[sel_index]

        # tender_row = (id, project_name, nilai_proyek, durasi, kompleksitas, risiko)
        st.markdown(f"**Project:** {tender_row[1]}  \n**Nilai:** Rp {tender_row[2]} M  \n**Durasi:** {tender_row[3]} bulan  \n**Kompleksitas:** {tender_row[4]}  \n**Risiko:** {tender_row[5]}  \n**User:** {tender_row[6] if len(tender_row) > 6 else ''}  \n**Tanggal Input:** {tender_row[7] if len(tender_row) > 7 else ''}")

        nilai = tender_row[2]
        durasi = tender_row[3]
        kompleksitas = tender_row[4]
        risiko = tender_row[5]

show_details = st.checkbox("Tampilkan perhitungan detail (z, sigmoid, koefisien model)")

if st.button("🔮 Prediksi Peluang Menang"):
    if show_details:
        probability, details = predict_win_probability([
            nilai, durasi, kompleksitas, risiko
        ], return_details=True)
    else:
        probability = predict_win_probability([
            nilai, durasi, kompleksitas, risiko
        ])

    st.metric(
        label="Peluang Menang Tender",
        value=f"{probability * 100:.2f}%"
    )

    if probability >= 0.6:
        st.success("📈 Peluang menang tinggi")
    else:
        st.warning("📉 Peluang menang rendah")

    st.caption("Sumber data: " + ("Manual Input" if data_source == "Manual Input" else "Tender tersimpan"))

    if show_details:
        st.subheader("Perhitungan detail")
        st.write(f"z (decision value) = {details['z']:.4f}")
        st.write(f"sigmoid(z) = {details['sigmoid']:.6f}")
        st.write("**Koefisien (skala asli)**")
        features = ['nilai_proyek', 'durasi', 'kompleksitas', 'risiko']
        coef_pairs = list(zip(features, details['coef_orig']))
        for name, c in coef_pairs:
            st.write(f"- {name}: {c:.6f}")
        st.write(f"Intercept (skala asli): {details['intercept_orig']:.6f}")


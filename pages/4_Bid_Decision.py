import streamlit as st
import pandas as pd
from modules.db import get_connection
from modules.risk import risk_level
from modules import reporting

st.header("✅ Pre-Qualification & Bid Decision")

# Logo upload / default logo management (auto-persist to session and save global if none exists)
import os
# Load global default into session if not already set
if "logo_bytes" not in st.session_state and os.path.exists("assets/logo.png"):
    with open("assets/logo.png", "rb") as f:
        st.session_state["logo_bytes"] = f.read()

logo_bytes = st.session_state.get("logo_bytes")

col1, col2 = st.columns([1, 3])
with col1:
    uploaded_logo = st.file_uploader("Upload company logo (PNG/JPG)", type=["png", "jpg", "jpeg"], key="logo_bid")
    if uploaded_logo is not None:
        logo_bytes = uploaded_logo.read()
        st.session_state["logo_bytes"] = logo_bytes
        st.image(logo_bytes, width=120)
        # If no global default exists, save uploaded one automatically; otherwise allow replace
        if not os.path.exists("assets/logo.png"):
            os.makedirs("assets", exist_ok=True)
            with open("assets/logo.png", "wb") as f:
                f.write(logo_bytes)
            st.success("Saved uploaded logo as global default: assets/logo.png")
        else:
            if st.button("Replace global default logo", key="replace_logo_bid"):
                with open("assets/logo.png", "wb") as f:
                    f.write(logo_bytes)
                st.success("Replaced global default logo: assets/logo.png")
with col2:
    if logo_bytes:
        st.image(logo_bytes, width=120)
    elif os.path.exists("assets/logo.png"):
        with open("assets/logo.png", "rb") as f:
            default_bytes = f.read()
        st.image(default_bytes, width=120)
        st.info("Using saved default logo (assets/logo.png)")

# Company name for header (quick input stored in session)
if "company_name" not in st.session_state:
    st.session_state["company_name"] = ""
st.text_input("Company name (header)", value=st.session_state["company_name"], key="company_name")

conn = get_connection()
df = pd.read_sql("SELECT * FROM tender", conn)
conn.close()

if df.empty:
    st.warning("Belum ada data tender")
else:
    # =========================
    # PRE-QUALIFICATION LOGIC
    # =========================
    def pre_qualification(row):
        if row["kesiapan_sertifikat"] == "Tidak Siap":
            return "Not Qualified"
        if row["nilai_proyek"] > 1.2 * row["nilai_hps"]:
            return "Not Qualified"
        if row["risiko"] == 10:
            return "Not Qualified"
        return "Qualified"

    df["Pre-Qualification"] = df.apply(pre_qualification, axis=1)

    # =========================
    # SCORING (ONLY QUALIFIED)
    # =========================
    df["Risk Level"] = df["risiko"].apply(risk_level)

    df["n_nilai"] = df["nilai_proyek"] / df["nilai_proyek"].max()
    df["n_durasi"] = df["durasi"].min() / df["durasi"]
    df["n_kompleksitas"] = df["kompleksitas"].min() / df["kompleksitas"]
    df["n_risiko"] = df["risiko"].min() / df["risiko"]

    df["Total Score"] = (
        0.4 * df["n_nilai"] +
        0.2 * df["n_durasi"] +
        0.2 * df["n_kompleksitas"] +
        0.2 * df["n_risiko"]
    )

    # =========================
    # BID / NO BID DECISION
    # =========================
    def bid_decision(row):
        if row["Pre-Qualification"] != "Qualified":
            return "NO BID"
        if row["Total Score"] >= 0.5 and row["Risk Level"] != "High":
            return "BID"
        return "NO BID"

    df["Decision"] = df.apply(bid_decision, axis=1)

    st.subheader("📋 Hasil Pre-Qualification & Keputusan Tender")

    df_export = df[
        [
            "project_name",
            "client",
            "user",
            "input_date",
            "nomor_tender",
            "status_tender",
            "Pre-Qualification",
            "Total Score",
            "Risk Level",
            "Decision"
        ]
    ]

    st.dataframe(df_export)

    # Export buttons
    csv_bytes = reporting.df_to_csv_bytes(df_export)
    st.download_button("⬇️ Download CSV", data=csv_bytes, file_name="bid_decision_report.csv", mime="text/csv")

    try:
        pdf_bytes = reporting.df_to_pdf_bytes(
            df_export,
            title="Bid Decision Report",
            logo_bytes=logo_bytes,
            company_name=st.session_state.get("company_name"),
        )
        st.download_button("📄 Download PDF", data=pdf_bytes, file_name="bid_decision_report.pdf", mime="application/pdf")
    except RuntimeError as e:
        st.warning("PDF export unavailable: " + str(e))
        st.info("Install in the running environment: `pip install reportlab`")

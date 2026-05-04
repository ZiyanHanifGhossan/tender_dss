import streamlit as st
import pandas as pd
from modules.db import get_connection
from modules import reporting

st.header("📊 Tender Pipeline Dashboard")

# Logo upload / default logo management (auto-persist to session and save global if none exists)
import os
# Load global default into session if not already set
if "logo_bytes" not in st.session_state and os.path.exists("assets/logo.png"):
    with open("assets/logo.png", "rb") as f:
        st.session_state["logo_bytes"] = f.read()

logo_bytes = st.session_state.get("logo_bytes")

col1, col2 = st.columns([1, 3])
with col1:
    uploaded_logo = st.file_uploader("Upload company logo (PNG/JPG)", type=["png", "jpg", "jpeg"], key="logo_pipeline")
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
            if st.button("Replace global default logo", key="replace_logo_pipeline"):
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
    # STATUS DERIVED FROM DATA
    # =========================
    def pipeline_status(row):
        if row["status_tender"] == "Identified":
            return "Identified"
        return row["status_tender"]

    # COUNT PIPELINE — use reporting helper so NO BID follows the same Bid Decision rules
    stats = reporting.compute_pipeline_stats(df)

    st.subheader("📌 Ringkasan Pipeline Tender")
    st.metric("Total Tender Masuk", stats["identified"])
    st.metric("Tender Qualified", stats["qualified"])
    # Tender Gugur (NO BID) is computed using the Bid Decision logic (pre-qualification, score, and risk)
    st.metric("Tender Gugur (NO BID)", stats.get("no_bid", 0))
    # New: Auto-flagged candidate — Total Score < 0.6 and model predicts WinProb > 0.8 (highlighted in yellow)
    st.metric("Auto-Flagged Candidates", stats.get("exception_candidates", 0))
    st.caption("'NO BID' ditentukan oleh logika pada menu Pre-Qualification & Bid Decision. Baris yang diwarnai kuning otomatis ketika WinProb > 0.8 dan Total Score < 0.6.")

    # Add visualizations: funnel, monthly bar, risk pie
    st.divider()
    st.subheader("📈 Visualisasi Pipeline")
    try:
        # compute pipeline stats using reporting helper
        funnel_fig = reporting.pipeline_funnel_figure(df)
        bar_fig = reporting.monthly_tenders_bar_figure(df)
        pie_fig = reporting.risk_pie_figure(df)

        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.plotly_chart(funnel_fig, use_container_width=True)
            st.markdown("**Funnel:** Identified → Qualified → Bid → Win (prob≥0.5)")
        with col_b:
            st.plotly_chart(pie_fig, use_container_width=True)
            st.markdown("**Distribusi Risk Level**")

        st.markdown("---")
        st.subheader("📅 Tender per Bulan")
        st.plotly_chart(bar_fig, use_container_width=True)

    except RuntimeError as e:
        st.warning("Visualisasi interaktif memerlukan package tambahan. Install: `pip install plotly` to enable charts")
        st.info(str(e))

    st.divider()

    st.subheader("📋 Daftar Tender (Pipeline View)")

    df_export = df[
        [
            "project_name",
            "client",
            "user",
            "input_date",
            "nomor_tender",
            "sumber_tender",
            "wk_migas",
            "jenis_tender",
            "nilai_proyek",
            "nilai_hps",
            "kesiapan_sertifikat",
            "status_tender"
        ]
    ]

    # Automatically compute Exception flags for display/export so UI always highlights them
    try:
        from modules.ml_model import predict_win_probability
    except Exception:
        predict_win_probability = None

    df_flags = reporting.apply_bid_decision(df.copy())
    if predict_win_probability is not None:
        def _prob_row(r):
            try:
                return predict_win_probability([r["nilai_proyek"], r["durasi"], r["kompleksitas"], r["risiko"]])
            except Exception:
                return None
        df_flags["Win_Prob"] = df_flags.apply(_prob_row, axis=1)
    else:
        df_flags["Win_Prob"] = None

    # use helper to compute auto-flag mask (no Exception column in export)
    df_flags["Auto_Flag"] = reporting.flag_exception_candidates(df_flags)

    # Build a display dataframe (keep same columns as before)
    df_display = df_export.copy()

    # Apply yellow highlight for auto-flagged rows on the main pipeline table
    def _highlight_auto_flag_main(row):
        idx = row.name
        return ["background-color: #ffeb3b; color: black" if idx in df_flags[df_flags["Auto_Flag"]].index else "" for _ in row]

    try:
        styled_main = df_display.style.apply(_highlight_auto_flag_main, axis=1)
        st.dataframe(styled_main)
        st.markdown("**Legend:** baris berwarna kuning menunjukkan analisis otomatis: WinProb > 0.8 dan Total Score < 0.6")
    except Exception:
        st.dataframe(df_display)

    # Optional: show per-tender win probabilities (uses same ML model as ML Prediction)
    if st.checkbox("Tampilkan Win Probabilities (untuk tenders yang diputuskan BID)"):
        from modules.ml_model import predict_win_probability

        # Ensure Decision column exists by applying the same Bid Decision logic
        df_probs = reporting.apply_bid_decision(df.copy())

        def _prob_for_row(r):
            try:
                prob = predict_win_probability([r["nilai_proyek"], r["durasi"], r["kompleksitas"], r["risiko"]])
                return prob
            except Exception:
                return None

        # Compute Win_Prob for all rows (needed to flag auto-flag candidates)
        df_probs["Win_Prob"] = df_probs.apply(_prob_for_row, axis=1)

        # Build export including Decision and numeric Win_Prob/Total Score for transparency
        desired_cols = ["project_name", "nomor_tender", "nilai_proyek", "durasi", "kompleksitas", "risiko", "Decision", "Win_Prob", "Total Score"]
        import pandas as _pd
        df_probs_export = _pd.DataFrame()
        for c in desired_cols:
            if c in df_probs.columns:
                df_probs_export[c] = df_probs[c]
            else:
                df_probs_export[c] = None

        # format percentage for display while keeping numeric Win_Prob for logic
        if "Win_Prob" in df_probs_export.columns:
            df_probs_export["Win_Prob_Display"] = df_probs_export["Win_Prob"].apply(lambda v: f"{v*100:.2f}%" if (v is not None and not _pd.isna(v)) else "-")
        else:
            df_probs_export["Win_Prob_Display"] = None

        # Apply compute mask for auto-flagging (use numeric columns)
        def _is_auto_flag(r):
            try:
                ts = float(r.get("Total Score"))
                wp = float(r.get("Win_Prob"))
                return (ts < 0.6) and (wp > 0.8)
            except Exception:
                return False

        df_probs_export["Auto_Flag"] = df_probs_export.apply(_is_auto_flag, axis=1)

        # Build display DataFrame without an explicit Exception column/badge
        display_df = df_probs_export[[c for c in df_probs_export.columns if c != "Auto_Flag"]]
        # Order display columns
        ordered_cols = [c for c in ["project_name", "nomor_tender", "nilai_proyek", "durasi", "kompleksitas", "risiko", "Decision", "Win_Prob_Display", "Total Score"] if c in display_df.columns]
        display_df = display_df[ordered_cols]

        # Apply row highlight using pandas Styler (Streamlit supports styled dataframes)
        def _highlight_auto_flag(row):
            return ["background-color: #ffeb3b; color: black" if row.name in df_probs_export[df_probs_export["Auto_Flag"]].index else "" for _ in row]

        try:
            styled = display_df.style.apply(_highlight_auto_flag, axis=1)
            st.dataframe(styled)
            st.markdown("**Legend:** baris berwarna kuning menunjukkan analisis otomatis: WinProb > 0.8 dan Total Score < 0.6")
        except Exception:
            # If styling fails for any reason, fall back to plain dataframe and show legend
            st.dataframe(display_df)
            st.markdown("**Legend:** baris berwarna kuning menunjukkan analisis otomatis: WinProb > 0.8 dan Total Score < 0.6")
        # Allow user to pick a tender and jump to ML Prediction page with that tender pre-selected
        if "Win_Prob" in df_probs_export.columns:
            options = df_probs_export[~df_probs_export["Win_Prob"].isin(["-"])]
            if not options.empty:
                options = options.reset_index()
                select_options = [f"{i} - {row.project_name} (Rp {row.nilai_proyek} M)" for i, row in options.iterrows()]
                sel = st.selectbox("Pilih tender untuk lihat detail prediksi di halaman ML Prediction", select_options)
                if st.button("Buka ML Prediction untuk tender ini"):
                    # get index and map to original row
                    idx = int(sel.split(" - ")[0])
                    row = options.iloc[idx]
                    # prefer nomor_tender if present
                    nomor = row.get('nomor_tender') if 'nomor_tender' in row else None
                    # Use the recommended stable API when available. If not, fall back to assigning to
                    # `st.query_params` (some Streamlit builds accept assignment), otherwise store hint in session.
                    if hasattr(st, 'set_query_params'):
                        st.set_query_params(tender_nomor=nomor)
                    elif hasattr(st, 'query_params'):
                        try:
                            # assignment uses list of values for each param
                            st.query_params = {'tender_nomor': [nomor] if nomor is not None else []}
                        except Exception:
                            st.session_state['preselect_nomor_hint'] = nomor
                            st.warning('Unable to set query params programmatically in this Streamlit build; copy the "nomor_tender" and paste it on the ML Prediction page.')
                    else:
                        # Last-resort fallback: store a hint in session state and inform the user
                        st.session_state['preselect_nomor_hint'] = nomor
                        st.warning('Your Streamlit version does not support setting query params programmatically. Copy the "nomor_tender" and paste it on the ML Prediction page.')
                    # Use a compatibility-safe rerun approach to support multiple Streamlit versions
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
                                st.info('Perubahan disimpan. Silakan refresh halaman untuk melihat pembaruan.')
                                st.stop()

    # Prepare export including auto-flag indicator so CSV and PDF include the Auto_Flag column
    try:
        from modules.ml_model import predict_win_probability
    except Exception:
        predict_win_probability = None

    df_flags = reporting.apply_bid_decision(df.copy())
    if predict_win_probability is not None:
        def _prob_row(r):
            try:
                return predict_win_probability([r["nilai_proyek"], r["durasi"], r["kompleksitas"], r["risiko"]])
            except Exception:
                return None
        df_flags["Win_Prob"] = df_flags.apply(_prob_row, axis=1)
    else:
        df_flags["Win_Prob"] = None

    # Compute Auto_Flag using the shared helper so CSV/PDF exports include the auto-flag indicator
    df_flags["Auto_Flag"] = reporting.flag_exception_candidates(df_flags)

    df_export_with_flags = df_export.copy()
    # Include numeric Win_Prob and Total Score for transparency in exports
    if "Win_Prob" in df_flags.columns:
        df_export_with_flags["Win_Prob"] = df_flags["Win_Prob"]
    if "Total Score" in df_flags.columns:
        df_export_with_flags["Total Score"] = df_flags["Total Score"]

    # Include Auto_Flag boolean column instead of the old 'Exception' column
    df_export_with_flags["Auto_Flag"] = df_flags["Auto_Flag"].astype(bool)

    # Export buttons
    csv_bytes = reporting.df_to_csv_bytes(df_export_with_flags)
    st.download_button("⬇️ Download CSV", data=csv_bytes, file_name="tender_pipeline_report.csv", mime="text/csv")

    try:
        pdf_bytes = reporting.df_to_pdf_bytes(
            df_export_with_flags,
            title="Tender Pipeline Report",
            logo_bytes=logo_bytes,
            company_name=st.session_state.get("company_name"),
        )
        st.download_button("📄 Download PDF", data=pdf_bytes, file_name="tender_pipeline_report.pdf", mime="application/pdf")
    except RuntimeError as e:
        st.warning("PDF export unavailable: " + str(e))
        st.info("Install in the running environment: `pip install reportlab`")

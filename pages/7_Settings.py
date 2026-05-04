import streamlit as st
from modules import reporting
import os

st.header("⚙️ Settings — Global Logo")

st.markdown("Manage the global company logo used in PDF headers.")

# Show current global logo
current = reporting.get_global_logo_bytes()
if current:
    st.subheader("Current global logo")
    st.image(current, width=200)
    if st.button("Delete global logo", key="delete_global_logo"):
        confirmed = st.checkbox("Confirm delete", key="confirm_delete_logo")
        if confirmed:
            if reporting.delete_global_logo():
                st.success("Global logo deleted.")
                if "logo_bytes" in st.session_state:
                    del st.session_state["logo_bytes"]
            else:
                st.warning("No global logo found to delete.")

else:
    st.info("No global logo is set.")

st.subheader("Upload / Replace global logo")
uploaded = st.file_uploader("Upload new global logo (PNG/JPG)", type=["png", "jpg", "jpeg"], key="settings_upload")
if uploaded is not None:
    logo_bytes = uploaded.read()
    st.image(logo_bytes, width=200)
    keep_backup = st.checkbox("Keep a backup of the previous global logo", value=True, key="keep_backup")
    if st.button("Save as global logo", key="save_global_logo"):
        reporting.save_global_logo_bytes(logo_bytes, backup_old=keep_backup)
        st.success("Saved uploaded logo as assets/logo.png")
        st.session_state["logo_bytes"] = logo_bytes

# Provide quick action to restore default if an example logo is included
if os.path.exists("assets/logo.png"):
    st.caption("Global logo path: assets/logo.png")
else:
    st.caption("No global logo file at assets/logo.png")

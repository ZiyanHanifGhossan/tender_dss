import streamlit as st
import sys

# Runtime check for optional dependency `plotly` and helpful guidance
try:
    import plotly
    _plotly_ok = True
    _plotly_ver = getattr(plotly, "__version__", "unknown")
except Exception:
    _plotly_ok = False
    _plotly_ver = None

# If plotly is missing, show a clear warning with actionable steps
from pathlib import Path
project_root = Path(__file__).resolve().parent
venv_python = project_root / ".venv" / "Scripts" / "python.exe"
if not _plotly_ok:
    if venv_python.exists():
        st.warning(
            "Optional dependency 'plotly' is not installed in the Python interpreter running Streamlit.\n"
            f"Python interpreter: {sys.executable}\n\n"
            "Fix: run Streamlit with the project's virtual environment. Examples:\n"
            "PowerShell:\n  .\\.venv\\Scripts\\Activate.ps1\n  python -m streamlit run app.py\n\n"
            "Direct (without activating):\n  " + str(venv_python) + " -m streamlit run app.py"
        )
    else:
        st.warning(
            "Optional dependency 'plotly' is not installed in the Python interpreter running Streamlit.\n"
            f"Python interpreter: {sys.executable}\n\n"
            "Fix: run Streamlit with the project's virtual environment. Examples:\n"
            "PowerShell:\n  .\\.venv\\Scripts\\Activate.ps1\n  python -m streamlit run app.py\n\n"
            "Direct (without activating):\n  .\\.venv\\Scripts\\python.exe -m streamlit run app.py"
        )

    st.markdown("---")
    st.write("If you prefer, you can install `plotly` into this Python interpreter now.\n"
             "This will modify the Python environment that is currently running Streamlit.")

    if st.button("Install plotly into this Python interpreter"):
        import subprocess
        import shlex
        pkg = "plotly==6.5.1"
        st.info(f"Installing {pkg} into: {sys.executable}")
        try:
            # Run pip install using the same interpreter
            completed = subprocess.run([sys.executable, "-m", "pip", "install", pkg], check=False, capture_output=True, text=True)
            st.code(completed.stdout + "\n" + completed.stderr)
            if completed.returncode == 0:
                st.success(f"Successfully installed {pkg}. Please refresh the page or restart Streamlit.")
                try:
                    import importlib
                    importlib.invalidate_caches()
                except Exception:
                    pass
            else:
                st.error("Installation failed. Check output above and fix permissions or network, or use the project venv instead.")
        except Exception as e:
            st.error(f"Installation attempt raised an error: {e}")

    st.stop()
else:
    # show a small info so it's easy to confirm the process has plotly
    if venv_python.exists():
        st.info(f"Optional dependency 'plotly' available (version {_plotly_ver}). Running with: {venv_python}")
    else:
        st.info(f"Optional dependency 'plotly' available (version {_plotly_ver}).")

from modules.db import create_table

st.set_page_config(
    page_title="Tender DSS",
    layout="wide"
)

create_table()

st.title("📊 Tender Decision Support System")
st.markdown("""
Sistem pendukung keputusan tender berbasis scoring, risk analysis,
dan machine learning. Digunakan secara internal dan offline.
""")

st.info("Gunakan menu di sidebar untuk navigasi.")

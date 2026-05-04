import json
from modules import reporting


def test_load_defaults(tmp_path):
    # when file is missing, defaults returned
    cfg = reporting.load_reporting_config(path=str(tmp_path / "nope.json"))
    assert isinstance(cfg, dict)
    assert "company_name" in cfg


def test_config_integration(tmp_path):
    p = tmp_path / "cfg.json"
    data = {
        "company_name": "My Test Co",
        "logo_path": "assets/logo.png",
        "logo_position": "right",
        "company_name_position": "center",
        "title_font_size": 16,
        "company_font_size": 10,
        "logo_max_height": 20,
        "author": "QA"
    }
    reporting.save_reporting_config(data, path=str(p))
    loaded = reporting.load_reporting_config(path=str(p))
    assert loaded["company_name"] == "My Test Co"

    # ensure df_to_pdf_bytes accepts config_path
    import pandas as pd
    df = pd.DataFrame({"x": [1, 2]})
    pdf = reporting.df_to_pdf_bytes(df, title="T", config_path=str(p))
    assert pdf.startswith(b"%PDF")

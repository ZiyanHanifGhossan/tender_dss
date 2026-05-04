import pandas as pd
from modules import reporting


def test_df_to_csv_bytes():
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    csv = reporting.df_to_csv_bytes(df)
    assert b"a,b" in csv or b"a,b" in csv
    assert b"1" in csv


def test_df_to_pdf_bytes_small():
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    pdf = reporting.df_to_pdf_bytes(df, title="Test PDF")
    assert pdf.startswith(b"%PDF")


def test_df_to_pdf_bytes_large():
    # Create a large dataframe to trigger multi-page behavior
    df = pd.DataFrame({f"col{i}": [f"val{j}" for j in range(200)] for i in range(6)})
    pdf = reporting.df_to_pdf_bytes(df, title="Large Report")
    assert pdf.startswith(b"%PDF")


def test_df_to_pdf_with_logo():
    # generate a small in-memory PNG using Pillow
    from PIL import Image
    import io

    img = Image.new("RGBA", (100, 40), (255, 0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    logo_bytes = buf.getvalue()

    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    pdf = reporting.df_to_pdf_bytes(df, title="With Logo", logo_bytes=logo_bytes)
    assert pdf.startswith(b"%PDF")


def test_df_to_pdf_with_company_name():
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    pdf = reporting.df_to_pdf_bytes(df, title="With Company", company_name="PT Contoh")
    assert pdf.startswith(b"%PDF")


def test_df_to_pdf_includes_column_list():
    # PDF should include a short 'Included columns' paragraph or list of column names
    df = pd.DataFrame({"project": ["A", "B"], "Total Score": [0.4, 0.7], "Win_Prob": [0.85, 0.3]})
    pdf = reporting.df_to_pdf_bytes(df, title="With Columns")
    assert pdf.startswith(b"%PDF")
    # Ensure at least one column name appears in the PDF content stream or in metadata
    assert b"project" in pdf or b"Total Score" in pdf or b"Win_Prob" in pdf or b"Included columns" in pdf


def test_df_to_csv_includes_total_score_and_win_prob():
    # Exports should include Total Score, Win_Prob and the Auto_Flag column when present
    df = pd.DataFrame({"a": [1], "Total Score": [0.42], "Win_Prob": [0.77], "Auto_Flag": [False]})
    csv = reporting.df_to_csv_bytes(df)
    assert b"Total Score" in csv
    assert b"Win_Prob" in csv
    assert b"Auto_Flag" in csv


def test_flag_exception_candidates():
    df = pd.DataFrame({
        "Total Score": [0.4, 0.6, 0.3],
        "Win_Prob": [0.85, 0.9, 0.5],
    })
    mask = reporting.flag_exception_candidates(df)
    assert mask.tolist() == [True, False, False]

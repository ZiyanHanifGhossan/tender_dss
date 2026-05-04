import pandas as pd
from modules import reporting


def sample_df():
    return pd.DataFrame([
        {
            'project_name': 'P1', 'client': 'C', 'nomor_tender': 'N1', 'sumber_tender': 'SKK',
            'wk_migas': 'WK', 'jenis_tender': 'EPC', 'nilai_proyek': 10.0, 'nilai_hps': 8.0,
            'durasi': 6, 'kompleksitas': 3, 'risiko': 2, 'kesiapan_sertifikat': 'Siap', 'status_tender': 'Identified', 'user': 'u1', 'input_date': '2025-01-05'
        },
        {
            'project_name': 'P2', 'client': 'C', 'nomor_tender': 'N2', 'sumber_tender': 'Open Tender',
            'wk_migas': 'WK', 'jenis_tender': 'EPC', 'nilai_proyek': 5.0, 'nilai_hps': 6.0,
            'durasi': 12, 'kompleksitas': 7, 'risiko': 8, 'kesiapan_sertifikat': 'Perlu Update', 'status_tender': 'Identified', 'user': 'u2', 'input_date': '2025-02-10'
        },
    ])


def test_compute_pipeline_stats_basic():
    df = sample_df()
    stats = reporting.compute_pipeline_stats(df)
    assert isinstance(stats, dict)
    for k in ['identified', 'qualified', 'bid', 'win_prob_count', 'expected_wins']:
        assert k in stats
    assert stats['identified'] == 2


def test_visual_functions_no_crash():
    df = sample_df()
    # figures may raise RuntimeError if plotly not installed; that's acceptable
    try:
        fig = reporting.pipeline_funnel_figure(df)
        assert fig is not None
        fig2 = reporting.monthly_tenders_bar_figure(df)
        assert fig2 is not None
        fig3 = reporting.risk_pie_figure(df)
        assert fig3 is not None
    except RuntimeError:
        pass

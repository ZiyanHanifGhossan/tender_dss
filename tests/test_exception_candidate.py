from modules import reporting
import pandas as pd

def test_exception_candidate_count():
    df = pd.DataFrame([
        {'nilai_proyek': 10.0, 'durasi': 6, 'kompleksitas': 5, 'risiko': 3, 'kesiapan_sertifikat': 'Siap', 'nilai_hps': 8.0},
        {'nilai_proyek': 2.0, 'durasi': 12, 'kompleksitas': 3, 'risiko': 9, 'kesiapan_sertifikat': 'Siap', 'nilai_hps': 2.0},
    ])
    stats = reporting.compute_pipeline_stats(df)
    # Stats should include an integer 'exception_candidates'
    assert 'exception_candidates' in stats
    assert isinstance(stats['exception_candidates'], int)

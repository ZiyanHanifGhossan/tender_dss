from modules import reporting
from modules.ml_model import predict_win_probability
import pandas as pd


def test_pipeline_win_prob_consistency():
    # create a small example df with two rows
    df = pd.DataFrame([
        {
            'nilai_proyek': 10.0,
            'durasi': 6,
            'kompleksitas': 5,
            'risiko': 3,
            'kesiapan_sertifikat': 'Siap',
            'nilai_hps': 8.0,
            'durasi': 6,
            'kompleksitas': 5,
            'risiko': 3
        },
        {
            'nilai_proyek': 2.0,
            'durasi': 12,
            'kompleksitas': 3,
            'risiko': 8,
            'kesiapan_sertifikat': 'Tidak Siap',
            'nilai_hps': 2.0,
            'durasi': 12,
            'kompleksitas': 3,
            'risiko': 8
        }
    ])

    stats = reporting.compute_pipeline_stats(df)

    # for each row that would be BID, compute prob directly and compare counts
    probs = []
    for _, r in df.iterrows():
        # apply same bid decision as in reporting
        preq = 'Not Qualified' if r['kesiapan_sertifikat'] == 'Tidak Siap' else 'Qualified'
        if preq == 'Qualified':
            prob = predict_win_probability([r['nilai_proyek'], r['durasi'], r['kompleksitas'], r['risiko']])
            probs.append(prob)

    win_prob_count = sum(1 for p in probs if p >= 0.5)
    assert stats['win_prob_count'] == win_prob_count

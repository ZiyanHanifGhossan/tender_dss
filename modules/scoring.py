def saw_score(data, weights):
    """
    Simple Additive Weighting (SAW)
    data    : dict nilai kriteria (sudah dinormalisasi)
    weights : dict bobot kriteria
    """
    score = 0
    for k in data:
        score += data[k] * weights[k]
    return score

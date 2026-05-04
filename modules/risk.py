def risk_level(risk_score):
    """
    Mengklasifikasikan risiko proyek
    """
    if risk_score <= 4:
        return "Low"
    elif risk_score <= 7:
        return "Medium"
    else:
        return "High"

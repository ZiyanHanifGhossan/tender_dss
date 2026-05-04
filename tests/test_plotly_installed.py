def test_plotly_importable():
    """Ensure optional dependency `plotly` is available to the test runner / CI."""
    try:
        import plotly
    except Exception as e:
        raise AssertionError("Optional dependency 'plotly' is not installed. Install it with: pip install plotly") from e
    assert hasattr(plotly, "__version__") and plotly.__version__ != "", "plotly appears to be improperly installed"
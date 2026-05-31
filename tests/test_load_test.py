from finops_gateway.scripts.load_test import RequestResult, _percentile, format_summary


def test_percentile():
    assert _percentile([1.0, 2.0, 3.0, 4.0], 50) == 2.5


def test_format_summary_includes_failures():
    results = [
        RequestResult(0, "q", ok=True, latency_s=1.0, tier="simple"),
        RequestResult(1, "q", ok=False, latency_s=0.5, error="Timeout"),
    ]
    text = format_summary(results, elapsed_s=2.0, concurrency=2)
    assert "failed: 1" in text
    assert "Timeout" in text

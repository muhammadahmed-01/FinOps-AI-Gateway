from finops_gateway.eval.llm_sanitize import sanitize_ragas_llm_output


def test_sanitize_strips_thinking_and_fences():
    raw = 'reasoning\n```json\n{"statements": ["a"]}\n```'
    assert sanitize_ragas_llm_output(raw) == '{"statements": ["a"]}'


def test_sanitize_extracts_embedded_json():
    raw = 'Here is the result: {"verdict": 1} thanks'
    assert sanitize_ragas_llm_output(raw) == '{"verdict": 1}'

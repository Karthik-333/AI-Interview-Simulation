from app.services.scoring_service import analyze_response, score_answer, semantic_match, validate_factuality


def test_multi_dimensional_scoring_and_semantic_matching():
    result = score_answer(
        "I designed a database API and debugged a production issue because the query was slow.",
        "database API debugging",
        ["I designed a database API and debugged production issues."],
        "Design a database API and debug production issues.",
    )
    assert set(result["dimensions"]) == {"technical_depth", "communication", "problem_solving", "domain_expertise"}
    assert result["score"] >= 0
    assert semantic_match("database API", "API database") == 1.0


def test_response_analysis_and_factuality_are_safe():
    assert analyze_response("") == "missing"
    factuality = validate_factuality("I used Python", ["I used Python for APIs"])
    assert factuality["is_supported"]

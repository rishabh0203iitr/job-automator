"""Tests for AI response parsing in job_scorer."""

import pytest

from job_automator.ai.job_scorer import parse_score_response


class TestParseScoreResponse:
    def test_valid_json(self):
        response = '{"score": 85, "reasons": "Strong Python skills match"}'
        score, reasons = parse_score_response(response)
        assert score == 85
        assert reasons == "Strong Python skills match"

    def test_json_with_whitespace(self):
        response = '  \n  {"score": 72, "reasons": "Good fit"}  \n  '
        score, reasons = parse_score_response(response)
        assert score == 72

    def test_markdown_wrapped_json(self):
        response = '```json\n{"score": 90, "reasons": "Excellent match"}\n```'
        score, reasons = parse_score_response(response)
        assert score == 90
        assert reasons == "Excellent match"

    def test_markdown_no_language_tag(self):
        response = '```\n{"score": 65, "reasons": "Decent"}\n```'
        score, reasons = parse_score_response(response)
        assert score == 65

    def test_score_clamped_to_100(self):
        response = '{"score": 150, "reasons": "Over the top"}'
        score, _ = parse_score_response(response)
        assert score == 100

    def test_score_clamped_to_0(self):
        response = '{"score": -10, "reasons": "Negative"}'
        score, reasons = parse_score_response(response)
        assert score == 0
        assert reasons == "Negative"

    def test_score_as_string_number(self):
        response = '{"score": "75", "reasons": "OK"}'
        score, _ = parse_score_response(response)
        assert score == 75

    def test_missing_reasons_field(self):
        response = '{"score": 50}'
        score, reasons = parse_score_response(response)
        assert score == 50
        assert reasons == ""

    def test_missing_score_field(self):
        response = '{"reasons": "No score provided"}'
        with pytest.raises(ValueError, match="Missing 'score'"):
            parse_score_response(response)

    def test_json_embedded_in_text(self):
        response = 'Here is my analysis:\n{"score": 80, "reasons": "Great"}\nHope this helps!'
        score, reasons = parse_score_response(response)
        assert score == 80

    def test_completely_invalid_response(self):
        response = "I think this job is a great fit for you!"
        with pytest.raises(ValueError, match="Could not parse"):
            parse_score_response(response)

    def test_empty_response(self):
        with pytest.raises(ValueError):
            parse_score_response("")

    def test_json_with_extra_text_before(self):
        response = 'Based on my analysis:\n```json\n{"score": 55, "reasons": "Partial match"}\n```\nLet me know if you need more.'
        score, reasons = parse_score_response(response)
        assert score == 55

    def test_multiple_code_blocks_picks_json(self):
        response = '```\nsome text\n```\n```json\n{"score": 70, "reasons": "Good"}\n```'
        score, reasons = parse_score_response(response)
        assert score == 70

    def test_score_zero_is_valid(self):
        response = '{"score": 0, "reasons": "No match at all"}'
        score, reasons = parse_score_response(response)
        assert score == 0
        assert reasons == "No match at all"

    def test_html_garbage(self):
        response = "<html><body>Error 500</body></html>"
        with pytest.raises(ValueError):
            parse_score_response(response)

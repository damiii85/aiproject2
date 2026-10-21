import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from src.services.naver_map import map_html
from src.services.pilot_report import load_spot_data, parse_request
from src.services.spot_catalog import load_spots
from src.services.spot_recommender import recommend_candidates


class RecommendationTests(unittest.TestCase):
    def test_intent_clears_previous_address(self):
        df, _ = load_spot_data("dongseongro")
        llm = Mock()
        llm.invoke.return_value = SimpleNamespace(content=json.dumps({
            "intent": "spot_recommendation", "address": "중앙대로 412-21",
            "categories": [{"level": "small", "name": "카페"}]}))
        result = parse_request("동성로 카페 어디가 좋을까", df,
                               {"address": "중앙대로 412-21"}, llm=llm)
        self.assertEqual(result["intent"], "spot_recommendation")
        self.assertEqual(result["address"], "")

    def test_real_data_candidates_are_covered_and_counts_match(self):
        for spot in load_spots():
            with self.subTest(spot=spot["id"]):
                df, metadata = load_spot_data(spot["id"])
                result = recommend_candidates(spot["id"], df, metadata, [{"level": "small", "name": "카페"}])
                self.assertGreater(len(result["candidates"]), 0)
                self.assertLessEqual(len(result["candidates"]), 3)
                for report in result["candidates"]:
                    self.assertTrue(report["coverage_complete"])
                    self.assertGreaterEqual(report["total_stores"], result["median_total"])
                    self.assertEqual(report["competitor_count"], len(report["competitors"]))
                    self.assertTrue(all(row["업종"] == "카페" for row in report["competitors"]))

    def test_map_escapes_untrusted_labels(self):
        html = map_html("test-client-id", 35.87, 128.595,
                        [{"lat": 35.87, "lon": 128.595, "label": "</script><script>alert(1)</script>"}])
        self.assertNotIn("</script><script>alert", html)
        self.assertIn("ncpKeyId=test-client-id", html)
        self.assertIn("textContent", html)
        self.assertNotIn("CLIENT_SECRET", html)

    def test_recommendation_ui_does_not_ask_address(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=20).run()
        self.assertFalse(any(e.label == "스팟별 데이터 확보 현황" for e in app.expander))
        request = {"intent": "spot_recommendation", "address": "", "categories": [{"level": "small", "name": "카페"}]}
        with patch("src.services.pilot_report.parse_request", return_value=request):
            app.chat_input[0].set_value("동성로에서 카페 어디가 좋을까?").run()
        self.assertFalse(app.exception)
        reports = app.session_state["spot_sessions"]["dongseongro"]["reports"]
        self.assertEqual(reports[-1]["type"], "recommendation")
        self.assertGreater(len(reports[-1]["candidates"]), 0)

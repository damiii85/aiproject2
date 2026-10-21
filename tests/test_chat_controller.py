import unittest
from unittest.mock import patch

from src.services.chat_controller import answer_question, local_request
from src.services.pilot_report import load_spot_data


class ChatControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stores, cls.metadata = load_spot_data("dongseongro")

    def test_address_analysis_without_model_connection(self):
        location = {"address": "동성로 2길 5", "latitude": 35.87, "longitude": 128.595}
        with patch("src.services.pilot_report.parse_request", side_effect=RuntimeError("offline")) as model:
            answer, report = answer_question("dongseongro", "여기서 카페 창업을 분석해 줘", {},
                self.stores, self.metadata, 200, location)
        model.assert_not_called()
        self.assertGreater(report["total_stores"], 0)
        self.assertEqual(report["address"], location["address"])
        self.assertIn("카페", answer)

    def test_recommendation_preserves_selected_mode(self):
        request = local_request("카페", self.stores, {"intent": "spot_recommendation"})
        self.assertEqual(request["intent"], "spot_recommendation")

    def test_study_cafe_is_not_regular_cafe(self):
        request = local_request("스터디 카페", self.stores, {})
        self.assertEqual(request["categories"], [{"level": "small", "name": "독서실/스터디 카페"}])

    def test_unknown_question_reports_connection_issue(self):
        with patch("src.services.pilot_report.parse_request", side_effect=RuntimeError("offline")):
            answer, report = answer_question("dongseongro", "궁금합니다", {}, self.stores, self.metadata, 200)
        self.assertIsNone(report)
        self.assertIn("연결하지 못했습니다", answer)

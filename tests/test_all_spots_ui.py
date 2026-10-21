"""All four spots must support real-data analysis through the UI, without an LLM."""
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from src.services.spot_catalog import load_spots
from src.services.pilot_report import load_spot_data
from src.services.location_analyzer import calculate_distance


def click(app, label):
    next(b for b in app.button if b.label == label).click().run()
    if app.exception:
        raise AssertionError(str(app.exception))


class AllSpotsUI(unittest.TestCase):
    def test_each_spot_address_and_recommendation(self):
        for spot in load_spots():
            with self.subTest(spot=spot["name"]):
                app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=20).run()
                app.button(key="start").click().run()
                app.button(key="select_" + spot["id"]).click().run()
                click(app, "이 지역으로 분석하기")
                stores, _ = load_spot_data(spot["id"])
                # Choose a building near the centre, ensuring analysis uses this spot's data.
                rows = stores.copy()
                rows["offset"] = [calculate_distance(spot["latitude"], spot["longitude"], r.lat, r.lon) for r in rows.itertuples()]
                address = rows.sort_values("offset").iloc[0].rdnmAdr
                app.selectbox(key="browse_address_" + spot["id"]).set_value(address).run()
                click(app, "이 위치로 분석 시작하기")
                with patch("src.services.pilot_report.parse_request", side_effect=RuntimeError("offline")):
                    app.button(key="quick_카페").click().run()
                self.assertFalse(app.exception)
                state = app.session_state["spot_sessions"][spot["id"]]
                self.assertEqual(state["reports"][-1]["spot"], spot["name"])
                self.assertGreater(state["reports"][-1]["total_stores"], 0)
                click(app, "위치 수정")
                app.radio[0].set_value("스팟 내 위치 추천").run()
                click(app, "이 스팟에서 후보지 찾아보기")
                with patch("src.services.pilot_report.parse_request", side_effect=RuntimeError("offline")):
                    app.button(key="quick_카페").click().run()
                self.assertFalse(app.exception)
                report = app.session_state["spot_sessions"][spot["id"]]["reports"][-1]
                self.assertEqual(report["type"], "recommendation")
                self.assertGreater(len(report["candidates"]), 0)
                self.assertTrue(all(r["spot"] == spot["name"] for r in report["candidates"]))
                other = next(s for s in load_spots() if s["id"] != spot["id"])
                app.selectbox(key="chat_spot_selector").set_value(other["id"]).run()
                self.assertFalse(app.exception)
                self.assertEqual(app.session_state["active_spot"], other["id"])
                self.assertEqual(app.session_state["ui_stage"], "location")
                self.assertEqual(len(app.session_state["spot_sessions"][spot["id"]]["reports"]), 2)

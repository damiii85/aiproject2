"""화면과 분리한 채팅 처리. 집계·추천 서비스는 기존 구현을 사용한다."""

import re

from src.services import pilot_report as pilot
from src.services.spot_recommender import recommend_candidates, recommendation_markdown


def local_request(question, stores, previous):
    """Resolve explicit catalogue labels without making basic counts depend on an API."""
    compact = re.sub(r"\s+", "", question)
    catalogue = pilot.category_catalog(stores)
    aliases = {"여성옷가게": "여성 의류 소매업", "여성의류": "여성 의류 소매업",
               "남성의류": "남성 의류 소매업", "네일샵": "네일숍",
               "커피숍": "카페", "스터디카페": "독서실/스터디 카페"}
    names = [name for name in catalogue["small"] if re.sub(r"\s+", "", name) in compact]
    names += [name for alias, name in aliases.items() if alias in compact and name in catalogue["small"]]
    # A study cafe is a separate official category, rather than a regular cafe.
    if "독서실/스터디 카페" in names:
        names = [name for name in names if name != "카페"]
    categories = [{"level": "small", "name": name} for name in dict.fromkeys(names)]
    if not categories and "음식점" in compact and "음식" in catalogue["large"]:
        categories = [{"level": "large", "name": "음식"}]
    if not categories:
        return None
    recommendation = any(term in compact for term in ["어디", "추천", "후보지찾"])
    intent = "spot_recommendation" if recommendation else previous.get("intent", "address_analysis")
    address = previous.get("address", "")
    matches = pilot.match_addresses(question, stores)
    if len(matches) == 1:
        address = matches[0]
        if not recommendation:
            intent = "address_analysis"
    return {"address": "" if intent == "spot_recommendation" else address,
            "intent": intent, "categories": categories, "clarification": ""}


def answer_question(spot_id, question, state, stores, metadata, radius, location=None):
    previous = dict(state.get("request", {}))
    if location:
        previous["address"] = location["address"]
    request = local_request(question, stores, previous)
    if request is None:
        try:
            request = pilot.parse_request(question, stores, previous)
        except ValueError:
            raise
        except Exception:
            return "언어 모델에 연결하지 못했습니다. 카페·여성 의류·미용실·편의점·네일숍처럼 업종을 입력하면 외부 연결 없이 상가 현황을 분석할 수 있습니다.", None
    state["request"] = request
    if not request["categories"]:
        return request.get("clarification") or "어떤 업종을 생각하고 계신가요? 업종을 조금 더 구체적으로 알려주세요.", None
    if request.get("intent") == "spot_recommendation":
        report = recommend_candidates(spot_id, stores, metadata, request["categories"], radius)
        return recommendation_markdown(report), report
    address = request["address"]
    if not address:
        return "정해 둔 주소를 알려주시거나, ‘이 스팟에서 어디가 좋을까?’라고 물어보세요.", None
    addresses = pilot.match_addresses(address, stores)
    coordinates = None
    if location and address == location["address"]:
        coordinates = (location["latitude"], location["longitude"])
    if len(addresses) != 1 and coordinates is None:
        return "주소의 위치를 하나로 확인하지 못했습니다. ‘위치 수정’에서 도로명·건물번호를 확인하거나 지도에서 확인한 좌표를 입력해 주세요.", None
    resolved = addresses[0] if len(addresses) == 1 and coordinates is None else address
    report = pilot.build_report(spot_id, stores, metadata, resolved, request["categories"], radius, coordinates)
    return pilot.report_markdown(report), report

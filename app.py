"""SPOT CHECK 대구 스팟 선택·주소/업종 채팅 파일럿."""

import json

import pandas as pd
import streamlit as st

from src.services.spot_catalog import BASE_DIR, load_spots, data_paths
from src.services.pilot_report import load_spot_data, parse_request, match_addresses, build_report, report_markdown
from src.services.naver_map import render_map
from src.services.spot_recommender import recommend_candidates, recommendation_markdown


@st.cache_data(ttl=300, max_entries=8)
def cached_spot_data(spot_id, csv_mtime, metadata_mtime):
    return load_spot_data(spot_id)

st.set_page_config(page_title="SPOT CHECK · 대구", page_icon="📍", layout="wide")
st.title("📍 SPOT CHECK")
st.caption("대구 창업 후보지 분석 파일럿 · 실제 상가 데이터 기반")
spots = load_spots()
with st.sidebar:
    st.header("분석 지역")
    st.selectbox("도시", ["대구"])
    spot_id = st.selectbox("스팟", [s["id"] for s in spots],
                           format_func=lambda value: next(s["name"] for s in spots if s["id"] == value))
    radius = st.slider("후보지 분석 반경(m)", 100, 500, 200, step=50)
    st.caption("스팟별 수집 범위는 파일럿 중심 반경 1km입니다. 공식 상권 경계와 다릅니다.")
    manual_coordinates = st.checkbox("지도에서 확인한 후보지 좌표 직접 입력")
    spot = next(s for s in spots if s["id"] == spot_id)
    if manual_coordinates:
        st.caption("입력한 주소와 같은 위치인지 확인해 주세요. 분석에는 아래 좌표를 사용합니다.")
        lat = st.number_input("후보지 위도", min_value=35.0, max_value=37.0, value=spot["latitude"], format="%.6f")
        lon = st.number_input("후보지 경도", min_value=128.0, max_value=130.0, value=spot["longitude"], format="%.6f")

st.subheader(f"대구 › {spot['name']}")
st.write("**주소를 정해 두셨나요?** 주소와 업종을 알려주세요. **위치를 찾고 계신가요?** 선택한 스팟에서 원하는 업종의 후보지를 물어보세요.")
render_map(spot["latitude"], spot["longitude"])
st.caption(f"지도 표시는 {spot['anchor']}이며 사용자 후보지 주소가 아닙니다.")

states = st.session_state.setdefault("spot_sessions", {})
state = states.setdefault(spot_id, {"messages": [], "request": {}, "reports": []})
if st.sidebar.button("이 스팟 대화 초기화"):
    states[spot_id] = {"messages": [], "request": {}, "reports": []}
    st.rerun()
try:
    csv_path, metadata_path = data_paths(spot_id)
    stores, metadata = cached_spot_data(spot_id, csv_path.stat().st_mtime_ns, metadata_path.stat().st_mtime_ns)
except (ValueError, OSError):
    st.warning("상가 데이터가 없습니다. 터미널에서 스팟 수집 명령을 실행해 주세요.")
    st.code(f"python src/collectors/collect_spot_stores.py --spot {spot_id}")
    st.stop()
st.caption(f"보유 상가 {len(stores):,}건 · 수집일 {metadata['collected_at_utc'][:10]}")
example = stores.iloc[((stores.lat - spot["latitude"]) ** 2 + (stores.lon - spot["longitude"]) ** 2).argmin()]
st.caption(f"주소 분석: ‘{example.rdnmAdr}에서 카페를 열고 싶어.’")
st.caption(f"후보지 추천: ‘{spot['name']}에서 카페를 하고 싶은데 어디가 좋을까?’")
with st.expander("매출·유동인구·보고서는 어떻게 확보하나요?"):
    sources = json.loads((BASE_DIR / "config/spot_report_sources.json").read_text(encoding="utf-8"))
    for source in sources["sources"]:
        st.markdown(f"[{source['name']}]({source['url']}) · {source['purpose']}")
        st.caption(source["status"])
    st.info("위 링크는 자료 탐색 경로입니다. 스팟별 보고서 원문과 통계는 아직 확보하지 않았습니다.")
for message in state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if question := st.chat_input("주소와 업종을 입력하거나, 스팟에서 창업할 위치를 물어보세요"):
    state["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)
    try:
        with st.spinner("주소·업종 확인 및 상가 집계 중…"):
            request = parse_request(question, stores, state["request"])
            state["request"] = request
            if not request["categories"]:
                answer = request["clarification"] or "분석할 업종을 구체적으로 알려주세요. 모든 업종을 선택할 수 있습니다."
            elif request.get("intent") == "spot_recommendation":
                report = recommend_candidates(spot_id, stores, metadata, request["categories"], radius)
                state["reports"].append(report)
                answer = recommendation_markdown(report)
            elif not request["address"]:
                answer = "정해 둔 후보지의 도로명 주소·건물번호를 알려주시거나, ‘이 스팟에서 어디가 좋을까?’라고 물어보세요."
            else:
                addresses = match_addresses(request["address"], stores)
                coordinates = (lat, lon) if manual_coordinates else None
                if len(addresses) != 1 and coordinates is None:
                    answer = ("수집된 상가 주소에서 후보지 위치를 하나로 확인하지 못했습니다. "
                              "도로명·건물번호를 확인하거나 왼쪽에서 지도 좌표를 직접 입력한 뒤 다시 요청해 주세요.")
                    if addresses:
                        answer += "\n\n일치 후보: " + ", ".join(addresses[:5])
                else:
                    address = addresses[0] if len(addresses) == 1 and coordinates is None else request["address"]
                    report = build_report(spot_id, stores, metadata, address, request["categories"], radius, coordinates)
                    state["reports"].append(report)
                    answer = report_markdown(report)
    except Exception as error:
        answer = (str(error) if isinstance(error, ValueError)
                  else "요청 처리에 실패했습니다. GMS 설정과 네트워크 상태를 확인한 뒤 다시 시도해 주세요.")
    state["messages"].append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)

if state["reports"]:
    latest = state["reports"][-1]
    st.divider()
    st.subheader("최근 분석의 상세 데이터")
    if latest.get("type") == "recommendation":
        candidates = latest["candidates"]
        if candidates:
            render_map(candidates[0]["latitude"], candidates[0]["longitude"],
                       markers=[{"lat": r["latitude"], "lon": r["longitude"], "label": f"후보 {i}: {r['address']}"}
                                for i, r in enumerate(candidates, 1)], radius=latest["radius_m"])
            for i, candidate in enumerate(candidates, 1):
                with st.expander(f"후보 {i} · {candidate['address']} 주변 점포"):
                    st.dataframe(pd.DataFrame(candidate["competitors"]), hide_index=True, alt="후보지 주변 선택 업종 점포")
    else:
        render_map(latest["latitude"], latest["longitude"],
                   markers=[{"lat": latest["latitude"], "lon": latest["longitude"], "label": latest["address"]}],
                   radius=latest["radius_m"], zoom=15)
        st.dataframe(pd.DataFrame(latest["category_counts"]), hide_index=True, alt="선택 업종별 점포 수")
        st.write("선택 업종 점포 목록 · 직선거리 순")
        st.dataframe(pd.DataFrame(latest["competitors"]), hide_index=True, width="stretch", alt="주변 경쟁 점포 목록")
    st.download_button("리포트 JSON 다운로드", json.dumps(latest, ensure_ascii=False, indent=2),
                       file_name=f"{spot_id}_report.json", mime="application/json")
    st.caption("대화와 리포트는 현재 브라우저 세션에서 스팟별로 관리합니다. 서버 재시작 시 사라질 수 있습니다.")

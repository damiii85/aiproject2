"""SPOT CHECK: 소개 → 지역 → 후보지 설정 → 채팅 분석."""

import json
from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from src.services.spot_catalog import BASE_DIR, load_spots, data_paths
from src.services.pilot_report import load_spot_data, match_addresses, coordinates_for_address
from src.services.chat_controller import answer_question
from src.services.naver_map import render_map
from src.ui.styles import apply_styles, brand, stepper, page_title

st.set_page_config(page_title="SPOT CHECK · 좋은 입지의 시작", page_icon=":material/location_on:",
                   layout="wide", initial_sidebar_state="collapsed")
apply_styles()
spots = load_spots()
st.session_state.setdefault("ui_stage", "home")
st.session_state.setdefault("active_spot", "dongseongro")
states = st.session_state.setdefault("spot_sessions", {})
spot_id = st.session_state["active_spot"]
spot = next(s for s in spots if s["id"] == spot_id)
state = states.setdefault(spot_id, {"messages": [], "request": {}, "reports": [], "location": None, "radius": 200})
state.setdefault("location", None)
state.setdefault("radius", 200)


@st.cache_data(ttl=300, max_entries=8)
def cached_data(spot_id, csv_mtime, metadata_mtime):
    return load_spot_data(spot_id)


def navigate(stage):
    st.session_state["ui_stage"] = stage
    st.rerun()


def choose_spot(value):
    st.session_state["active_spot"] = value
    st.rerun()


def change_chat_spot():
    st.session_state["active_spot"] = st.session_state["chat_spot_selector"]
    st.session_state["ui_stage"] = "location"


def source_content():
    st.markdown("**상가 데이터** · 소상공인시장진흥공단 상가정보 API")
    st.caption("대구 4개 파일럿 중심 반경 1km의 수집본입니다. 현재 영업 여부와 공식 상권 경계를 보장하지 않습니다.")
    st.markdown("**외부 보고서** · 확보한 PDF는 현재 채팅에 연결하기 전입니다.")
    st.caption("매출·유동인구·임대료를 현재 점포의 실측값처럼 제공하지 않습니다.")
    st.markdown("**지도** · NAVER Maps")


def topbar():
    left, right = st.columns([1, 1.5], vertical_alignment="center")
    with left:
        brand()
    with right:
        if st.session_state["ui_stage"] in {"region", "location"}:
            stepper(1 if st.session_state["ui_stage"] == "region" else 2)
        else:
            links = st.columns(3)
            with links[0].popover("서비스 소개", width="stretch"):
                st.write("실제 상가 데이터에서 주변 업종과 경쟁 점포를 살펴보는 창업 입지 분석 파일럿입니다.")
            with links[1].popover("이용 가이드", width="stretch"):
                st.write("① 지역 선택 ② 주소 또는 스팟 추천 선택 ③ 채팅으로 업종과 궁금한 점 입력")
                st.caption("대화는 현재 브라우저 세션에 저장됩니다.")
            with links[2].popover("데이터 출처", width="stretch"):
                source_content()


def render_details(report):
    if report.get("type") == "recommendation":
        candidates = report["candidates"]
        if candidates:
            render_map(candidates[0]["latitude"], candidates[0]["longitude"],
                       markers=[{"lat": r["latitude"], "lon": r["longitude"], "label": f"후보 {i}: {r['address']}"}
                                for i, r in enumerate(candidates, 1)], radius=report["radius_m"])
            for i, candidate in enumerate(candidates, 1):
                with st.expander(f"후보 {i} · {candidate['address']}"):
                    st.dataframe(pd.DataFrame(candidate["competitors"]), hide_index=True, alt="추천 후보지 주변 경쟁 점포")
    else:
        render_map(report["latitude"], report["longitude"],
                   markers=[{"lat": report["latitude"], "lon": report["longitude"], "label": report["address"]}],
                   radius=report["radius_m"], zoom=16)
        st.dataframe(pd.DataFrame(report["category_counts"]), hide_index=True, alt="선택 업종 점포 수")
        st.dataframe(pd.DataFrame(report["competitors"]), hide_index=True, alt="후보지 주변 경쟁 점포")
    st.download_button("분석 데이터 다운로드", json.dumps(report, ensure_ascii=False, indent=2),
                       file_name=f"{spot_id}_report.json", mime="application/json", icon=":material/download:")


topbar()
stage = st.session_state["ui_stage"]
if stage == "home":
    with st.container(key="hero"):
        st.html('<div class="eyebrow">데이터로 찾는, 더 나은 시작</div>')
        st.title("SPOT CHECK")
        st.header("당신의 창업, 좋은 위치에서 시작하세요.")
        st.html('<p class="hero-copy">대구 주요 지역의 상가 데이터와 업종별 경쟁 현황을 살펴보고,<br>내 창업 아이디어에 맞는 위치를 차근차근 탐색하세요.</p>')
        if st.button("분석 시작하기", icon=":material/arrow_forward:", type="primary", key="start"):
            navigate("region")
        st.space("large")
        a, b, c = st.columns(3)
        a.metric("파일럿 분석 지역", "대구 4곳")
        b.metric("지역별 수집 반경", "1km")
        c.metric("분석 대상", "다양한 업종")
    st.space("large")
    for col, number, title, description in zip(st.columns(3), ["01", "02", "03"],
        ["관심 지역을 고르세요", "나에게 맞는 위치를 설정하세요", "질문하며 상권을 살펴보세요"],
        ["동성로부터 수성못까지, 대구의 주요 스팟을 선택하세요.",
         "정확한 주소를 분석하거나 스팟 안에서 후보지를 찾아보세요.",
         "궁금한 업종을 입력하면 점포 분포와 경쟁 현황을 정리합니다."]):
        with col:
            st.html(f'<div class="feature"><span>{number}</span><h3>{title}</h3><p>{description}</p></div>')
    st.html('<div class="footer"><span>SPOT CHECK · 대구 창업 입지 분석 파일럿</span></div>')
    st.stop()

try:
    csv_path, metadata_path = data_paths(spot_id)
    stores, metadata = cached_data(spot_id, csv_path.stat().st_mtime_ns, metadata_path.stat().st_mtime_ns)
except (ValueError, OSError):
    st.warning("선택한 지역의 상가 데이터를 불러올 수 없습니다.")
    if st.button("지역 다시 선택"):
        navigate("region")
    st.stop()

if stage == "region":
    page_title("어떤 지역에서 창업을 생각하고 계신가요?", "관심 있는 스팟을 검색하거나 아래 지역 중 선택해 주세요.")
    left, right = st.columns([1, 1.35], gap="large")
    with left, st.container(key="region-panel"):
        keyword = st.text_input("지역 검색", placeholder="예: 동성로, 수성못, 동대구역", label_visibility="collapsed")
        st.caption("추천 지역 · 대구")
        filtered = [s for s in spots if keyword.strip() in s["name"] or keyword.strip() in s["district"]]
        if not filtered:
            st.info("현재 지원하는 대구 4개 스팟에서 선택해 주세요.")
        cards = st.columns(2)
        for index, item in enumerate(filtered):
            with cards[index % 2], st.container(key="spot-card-" + item["id"]):
                if st.button(f"{item['name']}  ·  대구 {item['district']}", icon=":material/location_on:",
                             type="primary" if item["id"] == spot_id else "secondary", width="stretch", key="select_" + item["id"]):
                    choose_spot(item["id"])
        st.html(f'<div class="selection-card">선택한 지역 · <strong>{escape(spot["name"])}</strong><small>파일럿 중심 반경 1km · 공식 상권 경계와 다릅니다.</small></div>')
    with right:
        render_map(spot["latitude"], spot["longitude"], markers=[{"lat": spot["latitude"], "lon": spot["longitude"], "label": spot["name"]}], radius=1000)
    back, advance = st.columns([1, 2])
    if back.button("처음으로", icon=":material/arrow_back:", width="stretch"):
        navigate("home")
    if advance.button("이 지역으로 분석하기", type="primary", icon=":material/arrow_forward:", width="stretch"):
        navigate("location")
    st.stop()

if stage == "location":
    page_title("더 정확한 분석을 위해 위치를 설정해 주세요", "주소가 정해져 있다면 후보지를 선택하고, 아직 없다면 스팟 안에서 추천받으세요.")
    left, right = st.columns([1, 1.15], gap="large")
    with left, st.container(key="location-panel"):
        mode = st.radio("분석 방식", ["정확한 주소 분석", "스팟 내 위치 추천"],
                        horizontal=True, key="mode_" + spot_id)
        st.caption(f"선택 지역 · 대구 {spot['district']} {spot['name']}")
        if mode == "정확한 주소 분석":
            query = st.text_input("후보지 주소 검색", placeholder="도로명과 건물번호를 입력하세요", key="address_query_" + spot_id)
            if state.get("location_query", "") != query:
                state["location"] = None
                state["location_query"] = query
            results = match_addresses(query, stores) if query.strip() else []
            if results:
                address = st.selectbox("검색된 주소", results, key="address_result_" + spot_id)
                try:
                    latitude, longitude = coordinates_for_address(address, stores)
                    state["location"] = {"address": address, "latitude": latitude, "longitude": longitude}
                except ValueError as error:
                    st.warning(str(error))
            elif query.strip():
                st.warning("일치하는 도로명 주소가 없습니다. 주소를 확인하거나 아래에서 지도 좌표를 입력해 주세요.")
            else:
                addresses = sorted(a for a in stores["rdnmAdr"].unique() if a.strip())
                address = st.selectbox(f"{spot['name']}의 수집된 주소에서 선택", addresses, index=None,
                                       placeholder="클릭한 뒤 도로명으로 검색하세요", key="browse_address_" + spot_id)
                if address:
                    try:
                        latitude, longitude = coordinates_for_address(address, stores)
                        state["location"] = {"address": address, "latitude": latitude, "longitude": longitude}
                    except ValueError as error:
                        state["location"] = None
                        st.warning(str(error))
            with st.expander("지도에서 확인한 좌표 직접 입력"):
                manual_address = st.text_input("직접 지정한 위치의 주소·이름", key="manual_address_" + spot_id)
                lat = st.number_input("위도", min_value=35.0, max_value=37.0, value=spot["latitude"], format="%.6f", key="lat_" + spot_id)
                lon = st.number_input("경도", min_value=128.0, max_value=130.0, value=spot["longitude"], format="%.6f", key="lon_" + spot_id)
                if st.button("이 좌표 선택", disabled=not manual_address.strip()):
                    state["location"] = {"address": manual_address.strip(), "latitude": lat, "longitude": lon}
                    st.rerun()
        else:
            st.info(f"{spot['name']} 안에서 업종에 맞는 탐색 후보를 비교합니다. 상세 주소는 입력하지 않아도 됩니다.")
        st.markdown("**분석 반경 설정**")
        state["radius"] = st.segmented_control("분석 반경", [100, 200, 300, 500], default=state["radius"],
                            required=True, format_func=lambda value: f"{value}m", key="radius_" + spot_id, label_visibility="collapsed")
        st.caption("선택한 위치를 중심으로 원형 반경 안의 수집 상가를 분석합니다.")
        location = state["location"] if mode == "정확한 주소 분석" else None
        if location:
            st.html(f'<div class="selection-card">선택한 위치<br><strong>{escape(location["address"])}</strong><small>위도 {location["latitude"]:.6f} · 경도 {location["longitude"]:.6f}</small></div>')
        elif mode == "정확한 주소 분석":
            st.caption("도로명 주소와 건물번호를 검색해 후보지를 선택해 주세요.")
    with right:
        target = location or spot
        render_map(target["latitude"], target["longitude"], markers=[{"lat": target["latitude"], "lon": target["longitude"],
                   "label": location["address"] if location else spot["name"]}], radius=state["radius"] if location else 1000, zoom=16 if location else 14)
        st.caption("주소는 수집본의 건물 대표 좌표로 표시합니다. 실제 출입구·층 위치는 현장에서 확인해 주세요.")
    back, advance = st.columns([1, 2])
    if back.button("이전으로", icon=":material/arrow_back:", width="stretch"):
        navigate("region")
    if advance.button("이 위치로 분석 시작하기" if location else "이 스팟에서 후보지 찾아보기", type="primary",
                      icon=":material/arrow_forward:", width="stretch", disabled=mode == "정확한 주소 분석" and location is None):
        state["location"] = location
        state["request"] = {"address": location["address"] if location else "", "categories": [],
                            "intent": "address_analysis" if location else "spot_recommendation"}
        state["analysis_mode"] = "address_analysis" if location else "spot_recommendation"
        navigate("chat")
    st.stop()

# 채팅 화면
context, conversation = st.columns([1, 3], gap="large")
with context, st.container(key="chat-context"):
    st.markdown("### 선택한 분석 정보")
    st.session_state["chat_spot_selector"] = spot_id
    st.selectbox("분석 지역", [s["id"] for s in spots],
                                format_func=lambda value: next(s["name"] for s in spots if s["id"] == value),
                                key="chat_spot_selector", on_change=change_chat_spot)
    st.caption(f"대구 › {spot['name']}")
    location = state["location"]
    if location:
        label = location["address"]
    else:
        label = f"{spot['name']} 내 후보지 추천"
    st.html(f'<div class="selection-card"><strong>{escape(label)}</strong><small>분석 반경 {state["radius"]}m</small></div>')
    if st.button("위치 수정", icon=":material/edit_location_alt:", width="stretch"):
        navigate("location")
    st.divider()
    st.markdown("### 주요 분석 항목")
    st.markdown(":material/storefront: 주변 상가 현황\n\n:material/query_stats: 업종별 경쟁 분석\n\n:material/location_on: 후보지 비교")
    st.caption("교통·외부 문서 기반 해설은 연결 준비 중입니다.")
    if st.button("새로운 분석하기", icon=":material/add:", width="stretch"):
        navigate("region")
    st.divider()
    st.markdown("### 분석 기록")
    if not state["reports"]:
        st.caption("첫 분석을 시작해 보세요.")
    for report in reversed(state["reports"][-5:]):
        industries = ", ".join(c["name"] for c in report.get("categories", []))
        st.markdown(f"**{escape(spot['name'])} · {escape(industries or '입지')}**")
        st.caption(report.get("created_at", "현재 세션"))
    if st.button("이 스팟 대화 초기화", width="stretch"):
        state["messages"], state["reports"], state["request"] = [], [], {}
        st.rerun()

with conversation:
    chat_feed = st.container(height=610, border=False, key="chat-feed")
    with chat_feed:
        with st.chat_message("assistant", avatar=":material/smart_toy:"):
            st.markdown("안녕하세요! **SPOT CHECK**입니다.")
            st.write("선택하신 위치의 상가 데이터를 바탕으로 창업 입지 분석을 도와드릴게요. 어떤 업종을 생각하고 계신가요?")
        quick_question = None
        with st.container(horizontal=True):
            for industry in ["카페", "여성 의류", "미용실", "음식점", "편의점", "네일숍"]:
                if st.button(industry, key="quick_" + industry):
                    quick_question = (f"{label}에서 {industry} 창업을 분석해 줘" if location
                                      else f"{spot['name']}에서 {industry}를 하고 싶은데 어디가 좋을까?")
        for message in state["messages"]:
            with st.chat_message(message["role"], avatar=":material/smart_toy:" if message["role"] == "assistant" else ":material/person:"):
                st.markdown(message["content"])
    question = st.chat_input("창업할 업종이나 추가로 궁금한 점을 질문해 주세요.", max_chars=3000) or quick_question
    if question:
        with chat_feed:
            state["messages"].append({"role": "user", "content": question})
            with st.chat_message("user", avatar=":material/person:"):
                st.write(question)
            with st.chat_message("assistant", avatar=":material/smart_toy:"):
                with st.status("입지 분석을 진행하고 있습니다…", expanded=True) as progress:
                    st.write("주소와 업종을 확인하고 수집 상가에서 분석 근거를 집계합니다.")
                    try:
                        answer, report = answer_question(spot_id, question, state, stores, metadata,
                                                         state["radius"], state["location"])
                        if report:
                            report["created_at"] = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y.%m.%d %H:%M")
                            state["reports"].append(report)
                        progress.update(label="분석 완료" if report else "추가 정보가 필요합니다", state="complete", expanded=False)
                    except Exception as error:
                        answer = str(error) if isinstance(error, ValueError) else "분석 요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요."
                        progress.update(label="분석을 완료하지 못했습니다", state="error", expanded=False)
                st.markdown(answer)
            state["messages"].append({"role": "assistant", "content": answer})
    if state["reports"]:
        with st.expander("최근 분석의 지도·상세 데이터 보기"):
            render_details(state["reports"][-1])
    st.caption("현재 세션의 분석 기록입니다. 수집 범위와 시점에 따른 한계를 함께 확인해 주세요.")

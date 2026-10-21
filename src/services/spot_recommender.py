"""수집본에서 비교 가능한 탐색 후보를 뽑는다. 수익성 예측 모델이 아니다."""

import numpy as np
import pandas as pd

from src.services.pilot_report import CATEGORY_FIELDS, build_report
from src.services.location_analyzer import calculate_distance
from src.services.spot_catalog import get_spot


def recommend_candidates(spot_id, df, metadata, categories, radius=200, top_k=3):
    if not categories or not 50 <= radius <= 500 or not 1 <= top_k <= 5:
        raise ValueError("업종, 50~500m 반경과 1~5개 후보 수가 필요합니다.")
    category_mask = np.zeros(len(df), dtype=bool)
    for item in categories:
        column = CATEGORY_FIELDS.get(item.get("level"))
        if not column or item.get("name") not in set(df[column]):
            raise ValueError("실제 분류에 있는 업종을 선택해 주세요.")
        category_mask |= (df[column] == item["name"]).to_numpy()
    # 200m 격자마다 기존 상가 건물 한 곳을 비교 중심으로 선정한다.
    sample = df[df.rdnmAdr.str.strip() != ""].copy()
    sample["grid_x"] = np.floor((sample.lon - metadata["center_lon"]) * 111320
                                * np.cos(np.radians(metadata["center_lat"])) / 200)
    sample["grid_y"] = np.floor((sample.lat - metadata["center_lat"]) * 111320 / 200)
    sample = sample.sort_values(["rdnmAdr", "bizesId"]).drop_duplicates(["grid_x", "grid_y"])
    sample = sample[[calculate_distance(metadata["center_lat"], metadata["center_lon"], r.lat, r.lon)
                      + radius <= metadata["radius_m"] for r in sample.itertuples()]]
    candidates = []
    latitudes, longitudes = np.radians(df.lat.to_numpy()), np.radians(df.lon.to_numpy())
    for row in sample.itertuples():
        latitude, longitude = np.radians(row.lat), np.radians(row.lon)
        a = np.sin((latitudes - latitude) / 2) ** 2 + np.cos(latitude) * np.cos(latitudes) * np.sin((longitudes - longitude) / 2) ** 2
        distances = 6371000 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
        nearby = distances <= radius
        total = int(nearby.sum())
        if total >= 10:
            competitors = int((nearby & category_mask).sum())
            candidates.append({"address": row.rdnmAdr, "latitude": row.lat, "longitude": row.lon,
                               "total": total, "competitors": competitors, "share": competitors / total})
    if not candidates:
        return {"type": "recommendation", "spot": get_spot(spot_id)["name"], "candidates": [],
                "reason": "동일 반경이 모두 수집 범위 안에 있고 주변 상가가 10곳 이상인 비교 후보가 없습니다."}
    median_total = float(np.median([c["total"] for c in candidates]))
    eligible = sorted((c for c in candidates if c["total"] >= median_total),
                      key=lambda c: (c["share"], -c["total"], c["address"]))
    selected = []
    for candidate in eligible:
        if any(calculate_distance(candidate["latitude"], candidate["longitude"],
                                  previous["latitude"], previous["longitude"]) < radius
               for previous in selected):
            continue
        selected.append(candidate)
        if len(selected) == top_k:
            break
    reports = [build_report(spot_id, df, metadata, c["address"], categories, radius,
                            (c["latitude"], c["longitude"])) for c in selected]
    for report in reports:
        report["coordinates_source"] = "상가 CSV의 격자별 비교 중심 건물 좌표"
    return {"type": "recommendation", "spot": get_spot(spot_id)["name"], "categories": categories,
            "candidates": reports, "median_total": median_total, "evaluated": len(candidates),
            "radius_m": radius,
            "method": "200m 격자의 기존 상가 건물을 비교 중심으로 사용. 분석 원 전체가 수집 범위 안이고 주변 상가 10곳 이상인 후보 중, 상가 수가 후보 중앙값 이상인 곳을 동종 업종 비중 오름차순으로 비교. 후보 간 최소 분석 반경만큼 간격 유지."}


def recommendation_markdown(result):
    if not result["candidates"]:
        return result["reason"]
    lines = [f"**{result['spot']} · 입지 탐색 후보 {len(result['candidates'])}곳**",
             "주변 상가가 비교적 모여 있는 구역 중 동종 업종 비중이 낮은 곳입니다. 매출·유동인구·임대료는 반영하지 않았습니다."]
    for i, report in enumerate(result["candidates"], 1):
        lines.append(f"{i}. **{report['address']}** — 반경 {report['radius_m']}m 내 상가 {report['total_stores']}곳, "
                     f"선택 업종 {report['competitor_count']}곳 ({report['competitor_count']/report['total_stores']:.1%})")
    lines += ["기존 상가 건물을 구역 비교의 중심으로 사용했습니다. 임대 가능한 매물 추천은 아니며 현장 확인이 필요합니다.",
              "경쟁 비중이 낮아도 수요가 적을 수 있습니다. 수익성이나 창업 성공 가능성을 판단한 순위가 아닙니다.",
              f"비교 기준: {result['method']}",
              f"수집일: {result['candidates'][0]['collected_at'][:10]} · [상가정보 API]({result['candidates'][0]['source']})"]
    return "\n\n".join(lines)

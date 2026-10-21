"""동성로 인근 상가 데이터 수집 (실제 상권 경계가 아닌 원형 반경 기준).

실행: python collect_stores.py
환경변수: PUBLIC_DATA_API_KEY (.env)
"""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("PUBLIC_DATA_API_KEY", "").strip()
URL = "https://apis.data.go.kr/B553077/api/open/sdsc2/storeListInRadius"
# 동성로 일대 예시 좌표. 확정된 공식 상권 경계가 아닙니다.
CX, CY, RADIUS = 128.595, 35.870, 1000
PAGE_SIZE = 1000
MAX_PAGES = 100
OUT = Path("data/raw")

def unpack(payload):
    response = payload.get("response", payload)
    header = response.get("header", {})
    code = str(header.get("resultCode", "00"))
    if code not in ("00", "0"):
        raise RuntimeError(f"API 오류 ({code}): {header.get('resultMsg', '')}")
    body = response.get("body", {})
    items = body.get("items", [])
    if isinstance(items, dict):
        items = items.get("item", [])
    if isinstance(items, dict):
        items = [items]
    if not isinstance(items, list):
        raise ValueError(f"예상하지 못한 items 형식: {type(items).__name__}")
    return items, int(body.get("totalCount") or 0)

def main():
    if not API_KEY:
        raise SystemExit(".env에 PUBLIC_DATA_API_KEY를 설정해 주세요.")
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    with requests.Session() as session:
        for page in range(1, MAX_PAGES + 1):
            params = {"serviceKey": API_KEY, "radius": RADIUS, "cx": CX, "cy": CY,
                      "pageNo": page, "numOfRows": PAGE_SIZE, "type": "json"}
            try:
                res = session.get(URL, params=params, timeout=30)
                res.raise_for_status()
                items, total = unpack(res.json())
            except (requests.RequestException, ValueError, RuntimeError) as exc:
                raise SystemExit(f"{page}페이지 수집 실패: {exc}") from exc
            rows.extend(items)
            print(f"{page}페이지: {len(items)}건 / 누적 {len(rows)}건 / 전체 {total or '미확인'}건")
            if not items or (total and len(rows) >= total) or len(items) < PAGE_SIZE:
                break
            time.sleep(0.2)
        else:
            print("주의: MAX_PAGES에 도달해 일부 데이터가 누락되었을 수 있습니다.")
    if not rows:
        print("조회 결과가 없습니다. 좌표·반경·API 승인 상태를 확인하세요.")
        return
    df = pd.DataFrame(rows)
    if "bizesId" in df.columns:
        df = df.drop_duplicates(subset=["bizesId"])
    (OUT / "dongseongro_stores.json").write_text(
        json.dumps(df.to_dict(orient="records"), ensure_ascii=False, indent=2), encoding="utf-8")
    df.to_csv(OUT / "dongseongro_stores.csv", index=False, encoding="utf-8-sig")
    meta = {"source": URL, "collected_at_utc": datetime.now(timezone.utc).isoformat(),
            "center_lon": CX, "center_lat": CY, "radius_m": RADIUS, "count": len(df),
            "note": "원형 조회 범위이며 동성로 공식 상권 경계가 아님"}
    (OUT / "collection_metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"완료: 중복 제거 후 {len(df)}건 저장 → {OUT.resolve()}")
    print("컬럼:", ", ".join(df.columns))

if __name__ == "__main__":
    main()

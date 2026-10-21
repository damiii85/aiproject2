# SPOT CHECK

동성로 상권 브리핑 및 창업 후보지 입지 분석을 위한 RAG 프로젝트입니다.

## 시작하기

1. Python 3.10+ 설치
2. `python -m venv .venv`
3. Windows PowerShell: `.\.venv\Scripts\Activate.ps1` (또는 Git Bash: `source .venv/Scripts/activate`)
4. `pip install -r requirements.txt`
5. `.env`에 `PUBLIC_DATA_API_KEY` 및 필요 시 `OPENAI_API_KEY` 입력
6. `python collect_stores.py` → `data/raw/`에 JSON/CSV 저장
7. `streamlit run app.py` → UI 골격 실행

## 프로젝트 폴더
- `collect_stores.py`: 상가(상권)정보 API 수집
- `data/raw/`: 원본 및 수집 결과 (Git 제외)
- `data/processed/`: 가공 데이터 (Git 제외)
- `src/collectors/`: 외부 문서 수집 코드 예정
- `src/rag/`: 청킹·색인·LangGraph 검색/생성 예정
- `src/services/`: 상권 통계·주소 비교 예정
- `src/utils/`: 공통 유틸 예정
- `config/`: 검색 설정 예정
- `docs/`: 요구사항·파이프라인 설계·출처 기록
- `tests/`: 검증 코드 예정

## 주의
- `.env`의 실제 키를 Git 또는 ZIP 공유본에 포함하지 마세요.
- API 키는 일반적으로 **Decoding 키**를 사용하고, `requests`의 `params`로 전달합니다.
- 좌표는 동성로 일대의 **예시 중심점**이며 공식 상권 경계가 아닙니다.
- 현재 `app.py`는 동작하는 UI 골격만 포함합니다. RAG 및 주소 비교는 미구현입니다.
- 수업 `step7_skeleton.py`를 참고해 Streamlit UI를 확장하세요.
- 외부 API 응답 구조 및 호출 제한은 최초 실행 시 확인해야 합니다.

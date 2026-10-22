# SPOT CHECK

API 수집본과 사용자 제공 PDF를 함께 읽는 대구 상권 정보 대시보드입니다. 실제 채팅은 LangGraph의 `retrieve → generate`를 통과하며 두 Chroma 컬렉션의 검색 결과와 검증된 집계를 결합합니다.

지원 권역: **대구 도심 통합상권(동성로·대구역·반월당) / 수성못 / 삼덕동 / 동대구역 / 칠곡3지구**.

- 도심 API 수집본은 세 지역 원본 23,785행을 상가 ID로 중복 제거한 10,759곳입니다. 단순 합산하지 않습니다.
- 동대구역 3,321곳, 칠곡3지구 2,359곳, 수성못 2,106곳, 삼덕동 7,009곳의 수집본이 있습니다. 수집 시점의 등록 정보입니다.
- 채팅 지정 PDF는 `data/reports/상권보고서.pdf`(개정판 10쪽)입니다. 종전 지정 PDF는 프로젝트에서 삭제했습니다.
- PDF의 도심 세 구역 통계는 각각 표시하고 합산하지 않습니다. 동대구역·칠곡3지구의 PDF 상권 경계는 미확정입니다.
- 질문의 `100m`, `100미터`, `0.1km`를 파싱해 실제 좌표 거리로 다시 집계합니다. 반경·기준점·출처를 표시하고 후속 질문에서도 업종과 기준점을 유지합니다.
- 위치 정보가 없으면 지역별 수집 기준점을 사용하며 사용자의 현재 위치라고 표현하지 않습니다. 알려지지 않은 현재 위치나 수집 범위 밖의 전체 점포 수는 추측하지 않습니다.
- 주소와 반경을 입력하면 해당 주소의 API 등록 좌표를 기준으로 계산합니다(예: `대구 중구 중앙대로 412-21 100m 카페`). 후속 반경 질문에서도 주소를 유지하며 `지역 전체`로 해제합니다. 수집본에서 확인되지 않는 주소는 기점으로 대체하지 않습니다. 별도 주소 검색 API는 호출하지 않습니다.
- 수치 카드·도넛·막대그래프와 지도 범위는 같은 집계 결과를 사용합니다. PDF 수치를 요청 반경으로 환산하지 않습니다.
- 특정 점포·주소 추천과 후보 순위는 제공하지 않습니다. PDF의 외부 임베딩·모델 처리는 명시적 전송 승인 설정에 따릅니다.

## 실행 (Git Bash)

```bash
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
python scripts/run_tests.py
```

`.env`의 키는 공유·커밋하지 않습니다. API 수집에는 `PUBLIC_DATA_API_KEY`, 모호한 업종 해석에는 `GMS_API_KEY`를 사용합니다. 원본 CSV/PDF는 Git 제외이므로 다른 서버에는 별도 복사하거나 수집해야 합니다.

설치 파일은 `requirements.txt` 하나입니다. 요구서의 필수 버전 14개와 실제 검증한 Windows/Python 3.11 `.venv` 환경의 전체 의존성 버전을 고정했습니다. 새 환경은 먼저 `python -m venv .venv`로 생성하세요. 기존 `venv`는 보존했습니다. [버전 대조표](docs/dependency_versions.md), 신규 환경의 키·설정·자료 준비는 [제출 준비 상태](docs/submission_readiness.md)를 참고하세요. Playwright/Edge 브라우저 검사는 별도의 개발 도구가 필요합니다.

실행 중 모듈 정의가 바뀌면 서버 터미널에서 Ctrl+C 후 다시 실행하세요. 브라우저 새로고침만으로 오래된 import가 교체되지는 않을 수 있습니다.

자료 범위·실행: `docs/daegu_pilot.md`. 화면 흐름: `docs/ui_flow.md`. 파일별 변경 기록: `작업진행.md`.

## 환경변수와 외부 처리

`.env.example`은 키 이름과 빈 값만 제공합니다. `.env`에 실제 키를 넣고 Git에 추가하지 마세요.

| 변수 | 용도 |
|---|---|
| `PUBLIC_DATA_API_KEY` | 상가정보 수집 |
| `GMS_API_KEY` | SSAFY GMS 임베딩 및 프롬프트 1·2·3 |
| `TAVILY_API_KEY` | 선택적인 웹 자동 검색. 지정 로컬 PDF 모드는 이 키 없이 동작 |
| `NAVER_MAP_CLIENT_ID` | 기존 네이버 지도 |

`config/rag_settings.json`에서 청크 크기/중복, 각 컬렉션 Top-k, TTL, 생성 모드, 임베딩 방식을 관리합니다. 현재 환경은 사용자의 명시 승인에 따라 GMS 전송을 허용하고 `generation_mode=llm`입니다. 질문·상권 메타데이터·PDF 청크가 GMS로 전송됩니다. 비밀 키는 설정 JSON에 저장하지 않습니다.

외부 처리가 허용되지 않는 환경은 `config/rag_settings.example.json`의 로컬 설정을 사용하세요. 로컬 문자 n-gram 벡터화는 GMS 학습형 의미 임베딩과 같지 않으며, 모델/자료 버전이 다른 색인은 검색에 혼합하지 않습니다. 임베딩 설정을 바꾸면 해당 설정으로 다시 색인해야 합니다.

## 자료 준비와 색인

기존 수집 모듈/자료 준비는 [파일럿 안내](docs/daegu_pilot.md)를 참고합니다. 지정 파일 `data/reports/상권보고서.pdf`, 활성 보고서 메타데이터와 다섯 지역의 CSV/수집 메타데이터가 필요합니다.

```bash
python scripts/prepare_rag.py
python scripts/prepare_rag.py --inventory
python scripts/verify_rag.py --live-llm
```

- DB: `data/chroma_db`, 컬렉션: `store_metadata`, `external_documents`.
- 현재 색인: 기존 개별 상가 8,496문서 + 지역/공식 업종 메타데이터 1,452문서 = 9,948레코드. 활성 PDF 14청크. 이는 실제 영업 점포 수의 합계가 아닙니다.
- 동일 자료 재실행은 새 임베딩과 레코드 증가가 없습니다. 자료·청크 설정·모델 변경은 새 revision으로 갱신합니다.
- 상가 수·비중·주소 반경은 매 질문의 전체 CSV 계산값을 사용합니다. 벡터 검색에서 가져온 표본 개수를 전체 개수로 쓰지 않습니다.
- 외부 웹 수집의 독립 CLI `src/rag/index_documents.py --question/--url`은 유지하지만 Tavily 실호출은 현재 키가 없어 미검증입니다. 기본 채팅 문서 집합은 지정 PDF이며, 법령 자료는 계속 제외합니다.

## 흐름 및 모듈

```text
app.py                              지역 선택 / 기존 채팅·지도·통계 UI
src/collectors/                      기존 API·HTML/PDF 수집
src/rag/index_stores.py              기존 개별 상가 텍스트·색인
src/rag/index_documents.py           재사용 청킹·멱등 문서 색인
src/rag/knowledge.py                 활성 PDF와 지역/업종 메타데이터 구성
src/rag/collection_flow.py           프롬프트1·2 / 후보 및 질의 캐시
src/rag/retrieval.py                 두 컬렉션 검색 / 필터 / 중복 제거
src/rag/pipeline.py                  실제 LangGraph retrieve → generate
src/rag/generation.py                프롬프트3 / 원문 검증 / 인용 번호
src/services/                       기존 주소·거리·통계·PDF 분석 재사용
src/ui/                             기존 답변 카드·참고 자료·상세 원문
config/rag_settings.json             비밀이 아닌 RAG 동작 설정
```

모든 정상 분석 질문은 검색·선별·생성 단계를 거칩니다. 생성 모델은 검색 원문의 실제 발췌만 반환하고, ID/원문 검증을 통과한 내용만 답변에 추가합니다. 사용한 출처만 `[근거 n]`으로 연결합니다. 자료가 부족한 질문, 지원 외 지역, 잘못된 주소에는 무관한 자료나 임의 숫자를 추가하지 않습니다. SDK 오류 원문도 화면에 표시하지 않습니다.

모델이 필요 없는 빠른 직접 응답을 원하면 `on_demand` 또는 `extractive` 모드를 선택할 수 있습니다. 기본 제출/검증 모드인 `llm`과 실행 경로 차이를 [설계문서](docs/rag_pipeline.md)에 기록했습니다. 같은 질의와 근거의 검증된 생성 결과는 캐시하고, API 범위 집계는 다시 계산합니다.

## 검증과 제출 문서

```bash
python scripts/run_tests.py
python scripts/check_rag_security.py
python scripts/verify_rag.py --live-llm
python scripts/check_rag_browser.py --url http://localhost:8501
python scripts/check_answer_browser.py --url http://localhost:8501
```

단위/회귀 실행기는 외부 호출을 끕니다. 실제 GMS 실행은 별도 검증 스크립트로 구분합니다. 브라우저 검사는 개발 환경의 Playwright/Edge를 사용하며 서비스에 새 UI 라이브러리를 추가하지 않았습니다. 결과 JSON과 캡처는 `data/processed`에 저장됩니다.

- [요구사항 정의·대조표](docs/requirements_audit.md)
- [RAG 설계](docs/rag_pipeline.md)
- [실행·테스트 결과표](docs/rag_test_results.md)
- [셀프·상호 체크리스트](docs/submission_checklist.md)
- [출처 및 이용 조건](docs/data_sources.md)
- [선택 심화 F2015: 실제 5문항 전후 비교](docs/rag_quality_comparison.md)
- [최종 제출 준비 및 남은 수동 확인](docs/submission_readiness.md)

실제 검증: 최신 단위/회귀 72개 통과, 실제 GMS 임베딩·두 컬렉션 검색·프롬프트 1·2·3 및 근거 번호, 브라우저 자연어 탐색·선택·원문 복사·PDF 다운로드·기록 복원. 같은 모델의 무검색/RAG 서비스 대표 5문항 비교를 별도 실시했습니다. Tavily 웹 실수집, 타인의 상호 검토, 공개 재배포 이용 허가, 배포 서버 부하 검증은 완료한 것으로 표시하지 않습니다. CSV/PDF/DB/캐시는 Git 제외이므로 제출·배포 환경에 별도로 준비해야 합니다.

제출용 코드·증빙 ZIP 재생성: `python scripts/build_submission.py`. 출력은 `data/processed/submission/SPOT_CHECK_submission.zip`이며, 키·원문 PDF/CSV·DB·질문 캐시는 포함하지 않습니다. 실제 제출 전 원문 자료 준비와 상호 검토, 제출자 정보에 맞춘 파일명 변경이 필요합니다. GMS 비교 재실행은 `python scripts/compare_rag_quality.py`이며 실제 호출 비용이 발생합니다.

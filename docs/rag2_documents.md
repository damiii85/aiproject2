# RAG 2 외부 문서 검색·수집·색인

`store_metadata`는 변경하지 않고, 같은 `data/chroma_db/` 아래 별도 컬렉션 `external_documents`에 문서 본문을 저장한다.

## 준비

```bash
source venv/Scripts/activate
pip install -r requirements.txt
```

이번에 추가한 라이브러리는 HTML 파싱용 `beautifulsoup4`다. PDF는 기존 `pypdf`를 사용한다.

`.env` 설정(실제 키를 공유하거나 커밋하지 않는다):

```dotenv
GMS_API_KEY=사용중인_GMS_키
GMS_LLM_MODEL=gpt-4o-mini
TAVILY_API_KEY=자동_웹검색용_키
```

`GMS_LLM_MODEL`은 GMS에서 사용 가능한 모델로 변경할 수 있다. 임베딩 모델 기본값은 `text-embedding-3-small`이다. 자동 검색용 Tavily 키는 GMS 키와 별개다. Tavily 키가 없으면 직접 문서 URL을 지정할 수 있다. 자동 검색은 Tavily 공식 Search API를 사용한다: https://docs.tavily.com/documentation/api-reference/endpoint/search

## 실행

자동 검색·선별·본문 수집·색인:

```bash
python src/rag/index_documents.py --question "동성로 여성 의류 매장 창업 준비와 입지 분석" --max-documents 3
```

필요하면 `--store-context data/processed/location_report.json`으로 실제 상가·분석 정보를 검색어 생성에 전달한다. 입력 파일에는 개인정보나 비밀정보를 넣지 않는다.

검색 키 없이 실제 문서 URL로 색인:

```bash
python src/rag/index_documents.py --url "https://www.easylaw.go.kr/CSP/CnpClsMainBtr.laf?ccfNo=1&cciNo=1&cnpClsNo=1&csmSeq=706&menuType=cnpcls"
```

이 URL은 실제 수집 검증에 사용한 커피전문점 창업 안내 예제다. 구현은 모든 업종의 HTML/PDF 자료에 적용할 수 있다. `--url`은 여러 번 지정할 수 있다. 이 경로는 검색어 생성과 후보 선별을 생략한다.

본문만 수집하고 임베딩 생략:

```bash
python src/rag/index_documents.py --url "실제_문서_URL" --collect-only
```

저장된 문서 검색:

```bash
python src/rag/index_documents.py --search "커피전문점 창업 준비" --top-k 3
```

검색 결과에는 청크 본문, 원문 URL, 출처 기관, 수집일, 벡터 거리를 표시한다. `--max-distance`로 거리 상한을 설정할 수 있다. 거리값은 관련성 확률이 아니며 문서 표본으로 적절한 상한을 검증해야 한다.

청크 설정과 후보 관련성 기준:

```bash
python src/rag/index_documents.py --question "미용실 창업 인허가" --chunk-size 1000 --chunk-overlap 200 --candidates 5 --min-score 0.6
```

## 파이프라인

1. 프롬프트 1은 질문과 상가 정보를 받아 검색어 1~3개를 JSON으로 생성한다.
2. Tavily로 공공기관 중심 실제 검색을 수행하고 URL 기준으로 후보 중복을 제거한다.
3. 프롬프트 2는 제목·요약으로 관련성을 평가한다. 반환 후보 ID와 점수 범위를 검증하고 기준 미달 후보를 제외한다. `last_selection.json`에 검색어와 선정 이유를 남긴다.
4. robots.txt를 확인하고 원문 HTML/PDF를 가져온다. 기관 루트 URL, 내부 주소, 과도한 크기의 응답은 거부한다. 실패한 문서는 오류를 표시하고 다음 문서를 처리한다.
5. 본문과 제목·출처·수집일·이용조건 메모를 `data/raw/external_documents/`의 JSON에 보존한다. 검색 결과 요약만으로 색인하지 않는다.
6. 본문을 청킹하고 GMS 임베딩을 생성해 `external_documents`에 저장한다. 같은 URL·본문·청크 설정·모델이면 재임베딩하지 않는다. 내용이나 청크 설정이 바뀌면 새 청크 저장 성공 후 해당 문서의 이전 청크만 제거한다.

## 검증과 남은 작업

```bash
python -m unittest discover -s tests -v
```

2026-10-21 검증:

- 자동 테스트 4개 통과: JSON 검증·허위 후보 ID 거부, HTML 본문 저장, URL·청크 설정 검증, 실제 메모리 Chroma에서 중복 방지·청크 변경·검색·임베딩 실패 시 기존 청크 보존.
- 실제 생활법령 문서 1개에서 본문 1,932자 수집.
- GMS로 두 프롬프트 실행, 본문 3개 청크 색인 및 검색 성공.
- 동일 문서 반복 색인 시 임베딩 0건 확인.
- `TAVILY_API_KEY`가 없어 자동 웹 검색 전체 경로는 미검증.

robots.txt 허용은 저작권 이용 허가를 뜻하지 않는다. 현재 예제 문서의 상세 재이용 조건은 미확인 상태로 기록했다. 확인한 이용 조건은 `--usage-note`로 남기고, 기관을 직접 지정하려면 `--source`를 사용한다. 이용 허가를 자동으로 판정하지 않는다.

HWP, 스캔 PDF OCR, 로그인·자바스크립트 렌더링은 지원하지 않는다. HTML 구조에 따라 메뉴 일부가 포함될 수 있으므로 저장 본문을 확인한다. 후보 선별은 제목·요약 단계의 관련성 판단이며 본문의 최신성이나 정확성을 보증하지 않는다. 같은 내용이 서로 다른 URL에 게시된 경우 URL별 문서로 보존한다.

F2003~F2005에 해당하는 코드 경로를 추가했다. 자동 검색 실검증, 자료 확충, RAG 1·2 병합(F2006), LangGraph와 프롬프트 3(F2007), UI 연결과 최종 요구사항 검증은 남아 있다. 현재 작업 시작 시 이전 RAG 1 자동 인식 추가 파일이 없었던 점도 후속 확인이 필요하다.

# PDF 근거 답변

활성 자료는 `data/reports/상권보고서.pdf`(10쪽)다. 2쪽의 7개 지역 통계표는 각 지역의 4개 지표 행 두 개를 검증해 읽으며, 지역명 수성못(두산동)·동대구역(신천4동)의 표기를 처리한다. 본문 페이지와 기준·정의 1·10쪽을 함께 출처로 표시한다.

`src/services/pdf_evidence.py`에서 로컬 파일을 직접 읽는다. 기본 답변은 PDF를 외부 모델로 전송하지 않는다. 도심 통합상권의 PDF 통계는 동성로·대구역·반월당별로 표시하며 합산하지 않는다. API 상가 ID 중복 제거 합집합과 구별한다.

거리 요청은 `src/services/distance_scope.py`에서 API 상가 좌표에만 적용한다. PDF 유동인구·매출을 반경 비율로 환산하지 않으며 요청 범위의 미확인 값은 알 수 없다고 안내한다.

외부 문서 CLI `src/rag/index_documents.py`는 별도 상권 자료 수집·검색 도구로 보존한다. 기존 벡터 컬렉션을 현재 채팅 PDF 근거에 자동 병합하지 않는다.

지역별 자료·거리 처리: `docs/daegu_pilot.md`.
검증: `python -m unittest discover -s tests -v`.

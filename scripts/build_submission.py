"""로컬 코드·검증 증빙 ZIP 생성. 비밀값·원문·사용자 캐시는 포함하지 않는다."""
import hashlib
import json
import os
import platform
import shutil
import sys
import zipfile
from importlib.metadata import version
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
from dotenv import load_dotenv


def write_reports():
    required = dict(zip(
        ['langchain','langgraph','langsmith','langchain-core','langchain-openai',
         'langchain-community','langchain-chroma','langchain-text-splitters','chromadb',
         'openai','streamlit','requests','python-dotenv','typing-extensions'],
        ['1.3.14','1.2.10','0.10.17','1.6.0','1.4.3','0.4.2','1.1.0','1.1.2',
         '1.5.9','2.54.0','1.62.0','2.34.2','1.2.3','4.16.0']))
    lines = ['# 요구서와 검증 환경의 버전 대조', '',
        f'실제 실행: {platform.system()}, Python {platform.python_version()}.', '',
        '기존 `venv`는 보존하고 별도 `.venv`에 요구서 버전을 설치해 검증했다. '
        '`requirements.txt` 하나에 요구서 필수 버전과 검증 환경의 전체 의존성을 고정했다. '
        '지정 버전 72개 회귀·pip check·GMS 검색/모델 연동 기록은 `evidence/spec_environment.json`에 보존한다. '
        '브라우저 도구는 기존 개발용 venv에서 실행하며 서비스 서버는 지정 버전 .venv를 사용했다.', '',
        '| 패키지 | 요구서 | 검증 환경 | 일치 |','|---|---|---|---|']
    for name, expected in required.items():
        actual = version(name)
        lines.append(f'| {name} | {expected} | {actual} | {"예" if actual==expected else "아니오"} |')
    (BASE/'docs/dependency_versions.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    evidence = BASE/'docs/evidence'
    evidence.mkdir(exist_ok=True)
    for name in ('unit_test_results.json','rag_quality_comparison.json','rag_inventory.json',
                 'rag_verification.json','rag_security.json','spec_environment.json'):
        shutil.copyfile(BASE/'data/processed'/name,evidence/name)
    quality=json.loads((evidence/'rag_quality_comparison.json').read_text(encoding='utf-8'))
    assert len(quality['cases'])==5
    from src.rag.pipeline import graph
    (evidence/'rag_graph.mmd').write_text(graph().get_graph().draw_mermaid(),encoding='utf-8')
    import chromadb
    client=chromadb.PersistentClient(path=str(BASE/'data/chroma_db'))
    sample=client.get_collection('store_metadata').get(where={'category_level':'region'},limit=1,include=['documents','metadatas'])
    assert sample['ids']
    (evidence/'index_sample.json').write_text(json.dumps(sample,ensure_ascii=False,indent=2),encoding='utf-8')
    matching=[]
    for path in (BASE/'data/raw/rag_collection_cache').glob('*.json'):
        item=json.loads(path.read_text(encoding='utf-8'))
        if item.get('question')==quality['cases'][0]['question'] and item.get('prompt1_executed') and item.get('prompt2_executed'):
            matching.append(item)
    assert matching, '실제 후보 선별 기록 없음'
    audit=max(matching,key=lambda item:item['created_at'])
    audit={k:audit.get(k) for k in ('created_at','question','region_id','queries','candidates','selected','rejected','prompt1_executed','prompt2_executed')}
    (evidence/'collection_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    notes = {
        'counts':'무검색 모델은 수치를 모른다고 답했다. 서비스는 실제 CSV의 전체 2,106곳·카페 95곳을 제공했다. 무검색 기권을 오답으로 처리하지 않으며, 검증 가능한 정보 제공량이 늘어난 사례다.',
        'radius':'무검색 모델은 기권했다. 서비스는 입력 주소의 등록 좌표와 100m 거리 필터로 전체 272곳·카페 19곳을 계산했다. 상권 기점으로 대체하지 않았으며 PDF를 반경 통계로 환산하지 않았다.',
        'pdf':'무검색 모델은 정확한 수치를 모른다고 답했다. 서비스는 보고서 2쪽의 43,284명/일과 2026-07 기준을 제공했다. 이는 보고서 수치와의 일치이며 현재 실측 사실을 독립 검증한 것은 아니다.',
        'transport':'무검색 답변에는 고속도로 접근·주차·보행량에 대한 출처 없는 주장이 있다. 이 주장을 거짓으로 확정하지 않고 제공 자료에서 검증할 수 없는 내용으로 판정했다. 서비스는 9쪽의 팔거역 접근 후보와 경계 미확정 한계를 인용했다. 다만 교통 질문에 불필요한 인구 통계도 포함되어 답변 길이 개선 여지가 있다.',
        'unknown':'두 답변 모두 실시간 임대료를 알 수 없다고 답했다. 서비스는 근거 0건으로 기권했고 무관한 인용이나 금액을 만들지 않았다. 이 문항에서는 RAG의 정확성 우위를 주장하지 않는다.'}
    lines=['# F2015 RAG 사용 전후 답변 품질 비교','',
        f'실제 실행 시각(UTC): {quality["executed_at"]}. 모델: `{quality["model"]}`, temperature=0.', '',
        '비교는 기존 venv에서 실제 GMS로 수행했고 지정 버전 .venv의 회귀/실연동은 별도 검증했다. '
        '같은 질문·지역명을 사용했다. 무검색 조건은 CSV/PDF·정답·검색 문서·이전 대화를 전달하지 않았다. '
        'RAG 조건은 현재 서비스의 CSV 전체 계산·PDF 처리·두 컬렉션 검색·LangGraph·검증된 발췌를 사용했다. '
        '따라서 **전체 서비스와 무검색 모델의 비교**이며 검색 문맥만 바꾼 통제 실험은 아니다. '
        'API 계산의 효과와 검색의 효과를 분리했다고 주장하지 않는다. 모델은 1회씩 실행해 표본·확률적 변동의 한계가 있다. '
        '정확성은 제공 CSV/PDF와의 일치 기준이고, 근거 없는 기권은 틀린 답으로 채점하지 않았다.', '',
        '| 문항 | 검증 자료 기반 답 제공 | 실제 연결 출처 수 | 모르는 정보 처리 |',
        '|---|---|---:|---|']
    for i,case in enumerate(quality['cases'],1):
        lines.append(f'| {i}. {case["kind"]} | {"금액을 추정하지 않음" if case["kind"]=="unknown" else "CSV/PDF와 대조"} | {len(case["citations"])} | {"양쪽 모두 기권" if case["kind"]=="unknown" else "공간·시점 한계 명시"} |')
    for i,case in enumerate(quality['cases'],1):
        assert case['trace']['nodes']==['retrieve','generate']
        lines += ['',f'## {i}. {case["question"]}', '', '### RAG 사용 전', '',case['before'], '',
            '### RAG 서비스 사용 후','',case['after'],'','### 평가','',notes[case['kind']], '',
            f'시간: 무검색 {case["before_seconds"]}초 / 서비스 {case["after_seconds"]}초. '
            f'프롬프트3 실호출: {case["trace"]["prompt3_executed"]}, 캐시 재사용: {case["trace"]["generation_cache_hit"]}.', '']
        for citation in case['citations']:
            lines.append(f'- [근거 {citation["number"]}] {citation.get("title", "")} · {citation.get("source", "")} · '
                         f'{citation.get("page") or "페이지 해당 없음"} · {citation.get("reference", "")} · {citation.get("scope", "")}')
    lines += ['', '## 결론과 한계','',
        '수치 3문항은 무검색 조건이 기권한 반면 서비스가 검증 자료의 값을 제공했다. 교통 문항은 근거를 확인할 수 있는 원문과 경계 한계를 제공했다. '
        '실시간 임대료는 양쪽 모두 안전하게 기권했다. 모든 문항에서 RAG가 더 우수하거나 환각을 완전히 제거했다고 결론 내리지 않는다. '
        '상호 검토는 사용자가 미실시라고 확인했으며 이 평가는 AI가 제공 자료를 대조한 결과다.', '',
        '재현: `python scripts/compare_rag_quality.py` 후 `python scripts/build_submission.py`. '
        '실모델 실행은 승인된 GMS 설정과 실제 자료/색인이 필요하고 호출 비용이 발생한다. '
        '원시 실행 기록은 [evidence/rag_quality_comparison.json](evidence/rag_quality_comparison.json).']
    (BASE/'docs/rag_quality_comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (evidence/'README.md').write_text(
        '# 제출 증빙\n\nJSON은 실제 실행 기록이다. 72개 오프라인 테스트와 별도 실제 GMS 실행을 구분한다. '
        '기존 rag_verification은 23단계 기록이며 rag_quality_comparison은 26단계 실제 5문항 비교다. '
        '실제 원문·CSV·DB·키·캐시는 포함하지 않는다. 상호 검토 및 새 환경 확인은 미완료다.\n',encoding='utf-8')


def build_zip():
    load_dotenv(BASE/'.env')
    secrets=[os.getenv(k,'').encode() for k in ('GMS_API_KEY','PUBLIC_DATA_API_KEY','TAVILY_API_KEY') if len(os.getenv(k,''))>8]
    files=[]
    for root in ('src','scripts','tests','docs','config','.streamlit','assets'):
        files.extend(p for p in (BASE/root).rglob('*') if p.is_file() and p.suffix in ('.py','.md','.mmd','.json','.toml','.txt','.png'))
    files.extend(BASE/name for name in ('app.py','README.md','requirements.txt','.env.example','.gitignore','작업진행.md'))
    files.extend(BASE/'data/reports'/name for name in ('README.md','active_report.source.json'))
    files.extend((BASE/'data/processed/ui_preview').glob('25_*.png'))
    files=sorted(set(p for p in files if p!=BASE/'config/rag_settings.json'))
    manifest=[]
    destination=BASE/'data/processed/submission/SPOT_CHECK_submission.zip'
    destination.parent.mkdir(parents=True,exist_ok=True)
    # 사전 검사 후에만 ZIP을 연다. 기존 완성 ZIP을 비밀값이 든 파일로 덮어쓰지 않는다.
    for path in files:
        payload=path.read_bytes()
        if any(secret in payload for secret in secrets):
            raise ValueError('비밀값 검사 실패: 파일 내용을 출력하지 않습니다.')
        manifest.append({'path':path.relative_to(BASE).as_posix(),'sha256':hashlib.sha256(payload).hexdigest()})
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path,path.relative_to(BASE).as_posix())
        archive.writestr('SUBMISSION_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        assert '.env' not in archive.namelist()
        assert not any(name.endswith('.pdf') or 'data/raw/' in name or 'chroma_db/' in name for name in archive.namelist())
    print(f'Created: {destination.relative_to(BASE)} ({len(files)} files). No keys/raw PDF/CSV/DB/caches.')


if __name__=='__main__':
    write_reports()
    build_zip()

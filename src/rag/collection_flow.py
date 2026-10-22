"""지정된 기존 PDF 후보 검색·선별 및 검색어/선별 결과 캐시."""
import hashlib
import json
import time

from src.rag.index_documents import generate_queries, select_candidates
from src.rag.knowledge import pdf_documents, corpus_signature
from src.rag.settings import BASE_DIR, load_settings
from src.services.spot_catalog import get_spot

CACHE_DIR=BASE_DIR/'data/raw/rag_collection_cache'


def _cached(path,ttl):
    try:
        value=json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value,dict) and time.time()-float(value['created_at'])<ttl else None
    except (OSError,ValueError,KeyError,TypeError):
        return None


def collect_candidates(question,region_id,llm=None,cache_dir=CACHE_DIR,settings=None,store_context=None):
    settings=settings or load_settings()
    signature=hashlib.sha256(json.dumps([question.strip(),region_id,corpus_signature(),bool(llm),
        settings['selection_min_score'],store_context or {},'selection-v2'],ensure_ascii=True).encode()).hexdigest()
    path=cache_dir/(signature+'.json')
    cached=_cached(path,settings['cache_ttl_seconds'])
    if cached:
        return dict(cached,cache_hit=True)
    context={'region_id':region_id,'region_name':get_spot(region_id)['name'],'domain':'상권 분석',**(store_context or {})}
    errors=[]
    queries=[]
    prompt1=prompt2=False
    if llm:
        try:
            queries=generate_queries(question,context,llm)
            prompt1=True
        except Exception:
            errors.append('검색어 모델 호출 실패 · 기존 지역 자료를 사용합니다.')
    if not queries:
        queries=[question.strip()[:200] or region_id+' 상권']
    search_key=hashlib.sha256(json.dumps([sorted(queries),region_id,corpus_signature()],ensure_ascii=True).encode()).hexdigest()
    search_path=cache_dir/('search_'+search_key+'.json')
    search_cache_hit=False
    cached_search=_cached(search_path,settings['cache_ttl_seconds'])
    if cached_search:
        candidates=cached_search['candidates']
        search_cache_hit=True
    if not search_cache_hit:
        documents=pdf_documents()
        candidates=[{'id':i,'title':d['title'],'url':d['url'],'region_id':d['region_id'],
            'snippet':d['text'][:700], 'source':d['source'],'page':d['page']} for i,d in enumerate(documents)]
        cache_dir.mkdir(parents=True,exist_ok=True)
        search_path.write_text(json.dumps({'created_at':time.time(),'candidates':candidates},ensure_ascii=False),encoding='utf-8')
    regional=[d for d in candidates if d['region_id']==region_id]
    if not regional:
        errors.append('선택 지역의 외부 문서 후보가 없습니다. PDF 파일과 지역 설정을 확인해 주세요.')
    selected=[]
    if llm and regional:
        try:
            selected=select_candidates(question,regional,settings['selection_min_score'],llm)
            prompt2=True
        except Exception:
            errors.append('후보 선별 모델 호출 실패 · 지정 지역 문서를 보존합니다.')
    # 선택 항목 자체의 설명·통계 문서는 선별 점수와 무관하게 반드시 포함.
    chosen={d['id']:d for d in selected}
    for item in regional:
        chosen.setdefault(item['id'],dict(item,reason='선택 지역 자체의 설명/통계 · 필수 포함'))
    selected=list(chosen.values())
    rejected=[dict(d,reason='다른 지역 문서') for d in candidates if d['id'] not in chosen]
    result={'created_at':time.time(),'question':question,'region_id':region_id,'queries':queries,
        'candidates':candidates,'selected':selected,'rejected':rejected,'errors':errors,
        'prompt1_executed':prompt1,'prompt2_executed':prompt2,'cache_hit':False,'search_cache_hit':search_cache_hit}
    cache_dir.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result

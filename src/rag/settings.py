"""색인·검색·캐시의 공통 설정. 비밀 키는 저장하지 않는다."""
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]


def load_settings(path=None):
    settings = json.loads(Path(path or BASE_DIR / 'config/rag_settings.json').read_text(encoding='utf-8'))
    for field in ('chunk_size', 'top_k_stores', 'top_k_documents', 'cache_ttl_seconds', 'request_timeout_seconds'):
        if type(settings.get(field)) is not int or settings[field] <= 0:
            raise ValueError('RAG 설정의 양의 정수 값을 확인해 주세요.')
    if not 0 <= settings['chunk_overlap'] < settings['chunk_size']:
        raise ValueError('청크 중복은 청크 크기보다 작아야 합니다.')
    settings['generation_mode'] = os.getenv('SPOTCHECK_RAG_GENERATION', settings['generation_mode'])
    if settings['generation_mode'] not in ('extractive', 'on_demand', 'llm'):
        raise ValueError('지원하지 않는 생성 모드입니다.')
    if not isinstance(settings.get('selection_min_score'),(int,float)) or not 0<=settings['selection_min_score']<=1:
        raise ValueError('문서 선별 점수는 0~1이어야 합니다.')
    return settings

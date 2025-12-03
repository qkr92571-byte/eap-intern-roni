"""
프롬프트 관리 서비스
- Firestore에 프롬프트 저장/조회
"""

from services.firebase_service import get_db
from typing import Optional
from datetime import datetime

PROMPT_DOC_ID = 'eap_review_prompt'

def get_prompt() -> Optional[str]:
    """
    Firestore에서 EAP 검수 프롬프트 조회
    
    Returns:
        프롬프트 텍스트 (없으면 None)
    """
    try:
        db = get_db()
        prompt_doc = db.collection('settings').document(PROMPT_DOC_ID).get()
        
        if prompt_doc.exists:
            data = prompt_doc.to_dict()
            return data.get('content', None)
        else:
            return None
    except Exception as e:
        print(f"⚠️  Firestore 프롬프트 조회 실패: {str(e)}")
        return None

def save_prompt(content: str, updated_by: Optional[str] = None) -> bool:
    """
    Firestore에 EAP 검수 프롬프트 저장
    
    Args:
        content: 프롬프트 텍스트
        updated_by: 수정자 (선택)
    
    Returns:
        저장 성공 여부
    """
    try:
        db = get_db()
        
        prompt_data = {
            'content': content,
            'updated_at': datetime.now().isoformat(),
        }
        
        if updated_by:
            prompt_data['updated_by'] = updated_by
        
        db.collection('settings').document(PROMPT_DOC_ID).set(prompt_data)
        return True
    except Exception as e:
        print(f"❌ Firestore 프롬프트 저장 실패: {str(e)}")
        return False

def get_prompt_metadata() -> Optional[dict]:
    """
    프롬프트 메타데이터 조회 (수정일, 수정자 등)
    
    Returns:
        메타데이터 딕셔너리
    """
    try:
        db = get_db()
        prompt_doc = db.collection('settings').document(PROMPT_DOC_ID).get()
        
        if prompt_doc.exists:
            data = prompt_doc.to_dict()
            return {
                'updated_at': data.get('updated_at'),
                'updated_by': data.get('updated_by'),
            }
        else:
            return None
    except Exception as e:
        print(f"⚠️  Firestore 프롬프트 메타데이터 조회 실패: {str(e)}")
        return None


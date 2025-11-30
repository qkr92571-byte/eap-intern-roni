import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

load_dotenv()

_db = None

def init_firebase():
    """Firebase 초기화"""
    global _db
    
    if not firebase_admin._apps:
        # Firebase 서비스 계정 키 파일 경로
        cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'config/firebase-credentials.json')
        
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            # 환경 변수에서 직접 인증 정보를 가져오는 경우
            firebase_admin.initialize_app()
    
    _db = firestore.client()
    return _db

def get_db():
    """Firestore 데이터베이스 인스턴스 반환"""
    if _db is None:
        init_firebase()
    return _db

def save_announcement(announcement_data):
    """공고 데이터를 Firestore에 저장"""
    db = get_db()
    doc_ref = db.collection('announcements').add(announcement_data)
    return doc_ref[1].id

def check_duplicate_announcement(announcement_number: str) -> bool:
    """
    공고번호로 중복 체크
    
    Args:
        announcement_number: 공고번호
        
    Returns:
        중복이면 True, 없으면 False
    """
    if not announcement_number or not announcement_number.strip():
        return False
    
    db = get_db()
    try:
        # 공고번호로 검색
        query = db.collection('announcements').where('announcement_number', '==', announcement_number.strip()).limit(1)
        docs = list(query.stream())
        is_duplicate = len(docs) > 0
        return is_duplicate
    except Exception as e:
        print(f"중복 체크 중 오류: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False  # 오류 발생 시 저장하도록 함

def get_announcements(filters=None, limit=100):
    """공고 목록 조회"""
    db = get_db()
    query = db.collection('announcements')
    
    if filters:
        for key, value in filters.items():
            query = query.where(key, '==', value)
    
    query = query.order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit)
    docs = query.stream()
    
    announcements = []
    for doc in docs:
        announcement = doc.to_dict()
        announcement['id'] = doc.id
        announcements.append(announcement)
    
    return announcements

def get_announcement_by_id(announcement_id):
    """ID로 공고 조회"""
    db = get_db()
    doc = db.collection('announcements').document(announcement_id).get()
    
    if doc.exists:
        announcement = doc.to_dict()
        announcement['id'] = doc.id
        return announcement
    return None

def update_announcement(announcement_id, update_data):
    """공고 업데이트"""
    db = get_db()
    db.collection('announcements').document(announcement_id).update(update_data)
    return True

def delete_announcement(announcement_id):
    """공고 삭제"""
    db = get_db()
    db.collection('announcements').document(announcement_id).delete()
    return True


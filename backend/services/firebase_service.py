import firebase_admin
from firebase_admin import credentials, firestore
import os
from pathlib import Path
from dotenv import load_dotenv


def _load_env_for_backend():
    """
    backend/.env 또는 프로젝트 루트 .env를 우선적으로 로드
    
    - FIREBASE_CREDENTIALS_PATH 등 백엔드 설정이 backend/.env에 있는 경우
      현재 작업 디렉토리와 상관없이 항상 로드되도록 보장
    """
    backend_dir = Path(__file__).resolve().parent.parent  # .../backend
    project_root = backend_dir.parent                     # .../ (프로젝트 루트)
    
    backend_env = backend_dir / ".env"
    root_env = project_root / ".env"
    
    if backend_env.exists():
        load_dotenv(backend_env)
    elif root_env.exists():
        load_dotenv(root_env)
    else:
        load_dotenv()


_load_env_for_backend()

_db = None


def _resolve_credential_path(raw_path: str) -> str:
    """
    Firebase 서비스 계정 키 파일 경로를 backend 디렉토리 기준으로 안전하게 해석
    
    우선순위:
    1. 절대 경로라면 그대로 사용 (존재 여부만 체크)
    2. 상대 경로라면 backend/ 기준으로 조합
    3. 그래도 없으면 프로젝트 루트 기준으로 한 번 더 시도
    """
    if not raw_path:
        return raw_path
    
    # 절대 경로면 그대로 반환
    if os.path.isabs(raw_path):
        return raw_path
    
    backend_dir = Path(__file__).resolve().parent.parent
    project_root = backend_dir.parent
    
    # 1차 시도: backend/ 기준 상대 경로
    candidate_backend = backend_dir / raw_path
    if candidate_backend.exists():
        return str(candidate_backend)
    
    # 2차 시도: 프로젝트 루트 기준 상대 경로
    candidate_root = project_root / raw_path
    if candidate_root.exists():
        return str(candidate_root)
    
    # 둘 다 없으면 원본 경로 그대로 반환 (에러 메시지에 노출하기 위함)
    return raw_path


def init_firebase():
    """Firebase 초기화"""
    global _db
    
    if not firebase_admin._apps:
        # Firebase 서비스 계정 키 파일 경로 (기본값은 backend 기준 config/firebase-credentials.json)
        raw_cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'config/firebase-credentials.json')
        cred_path = _resolve_credential_path(raw_cred_path)
        
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print(f"✅ Firebase 초기화 성공: {cred_path}")
        else:
            # 키 파일이 없으면 오류 메시지 출력
            print(f"⚠️  Firebase 키 파일을 찾을 수 없습니다: {cred_path}")
            print(f"   Firebase 기능을 사용하려면 키 파일이 필요합니다.")
            raise FileNotFoundError(f"Firebase 키 파일을 찾을 수 없습니다: {cred_path}")
    
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
    # display_status 기본값 설정 (없으면 20으로 설정)
    if 'display_status' not in announcement_data:
        announcement_data['display_status'] = 20  # 20: 노출, 40: 삭제됨
    doc_ref = db.collection('announcements').add(announcement_data)
    return doc_ref[1].id

def get_firestore_announcement_numbers(days: int = 60) -> set:
    """
    Firestore에서 최근 N일 이내 공고번호 목록 조회 (CI 환경 중복 방지용)

    Args:
        days: 조회할 기간 (기본값: 60일)

    Returns:
        공고번호 set
    """
    from datetime import datetime, timedelta, timezone
    db = get_db()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        query = db.collection('announcements') \
            .where('created_at', '>=', cutoff_str) \
            .stream()
        numbers = set()
        for doc in query:
            data = doc.to_dict()
            num = data.get('announcement_number', '').strip()
            if num:
                numbers.add(num)
        return numbers
    except Exception as e:
        print(f"  ⚠️  Firestore 공고번호 조회 실패 (로컬 히스토리만 사용): {e}")
        return set()


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

def get_announcement_by_number(announcement_number: str):
    """
    공고번호로 공고 조회 및 문서 ID 반환
    
    Args:
        announcement_number: 공고번호
        
    Returns:
        (문서 ID, 공고 데이터) 튜플 또는 (None, None)
    """
    if not announcement_number or not announcement_number.strip():
        return None, None
    
    db = get_db()
    try:
        query = db.collection('announcements').where('announcement_number', '==', announcement_number.strip()).limit(1)
        docs = list(query.stream())
        if len(docs) > 0:
            doc = docs[0]
            announcement = doc.to_dict()
            announcement['id'] = doc.id
            return doc.id, announcement
        return None, None
    except Exception as e:
        print(f"공고번호로 조회 중 오류: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None, None

def update_announcement_by_number(announcement_number: str, update_data):
    """
    공고번호로 공고 업데이트
    
    Args:
        announcement_number: 공고번호
        update_data: 업데이트할 데이터 딕셔너리
        
    Returns:
        업데이트 성공 여부
    """
    doc_id, _ = get_announcement_by_number(announcement_number)
    if doc_id:
        return update_announcement(doc_id, update_data)
    return False


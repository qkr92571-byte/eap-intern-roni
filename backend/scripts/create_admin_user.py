"""
초기 admin 계정 생성 스크립트

Firebase Authentication에 hslee@atommerce.com 계정을 생성하고,
Firestore users 컬렉션에 admin 프로필을 등록합니다.

실행 방법:
    cd /path/to/eap-intern-roni
    python -m backend.scripts.create_admin_user
"""

import os
import sys
from datetime import datetime, timezone

# backend 루트를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

import firebase_admin
from firebase_admin import credentials, auth, firestore

# Firebase Admin SDK 초기화
CREDENTIALS_PATH = os.environ.get('FIREBASE_CREDENTIALS_PATH', 'backend/config/firebase-credentials.json')
if not firebase_admin._apps:
    cred = credentials.Certificate(CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()

ADMIN_EMAIL = 'hslee@atommerce.com'
ADMIN_PASSWORD = '111111'


def create_admin_user():
    print(f'admin 계정 생성 시작: {ADMIN_EMAIL}')

    # 1. Firebase Authentication 계정 생성 (이미 존재하면 조회)
    try:
        user = auth.get_user_by_email(ADMIN_EMAIL)
        print(f'  ℹ️  이미 존재하는 계정입니다. UID: {user.uid}')
    except auth.UserNotFoundError:
        user = auth.create_user(
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            email_verified=True,
        )
        print(f'  ✅ Firebase Auth 계정 생성 완료. UID: {user.uid}')

    # 2. Firestore users/{uid} 문서 생성/업데이트
    user_ref = db.collection('users').document(user.uid)
    doc = user_ref.get()

    if doc.exists:
        # 이미 존재하면 role/approved만 보장
        user_ref.update({
            'role': 'admin',
            'approved': True,
        })
        print(f'  ✅ Firestore 프로필 업데이트 완료 (role=admin, approved=True)')
    else:
        user_ref.set({
            'uid': user.uid,
            'email': ADMIN_EMAIL,
            'role': 'admin',
            'approved': True,
            'created_at': datetime.now(timezone.utc).isoformat(),
        })
        print(f'  ✅ Firestore 프로필 생성 완료')

    print(f'\n완료! {ADMIN_EMAIL} 계정으로 로그인하세요.')


if __name__ == '__main__':
    create_admin_user()

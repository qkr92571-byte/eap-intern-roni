#!/usr/bin/env python3
"""
Firestore 인덱스 생성 스크립트

Firebase REST API를 사용하여 Firestore 인덱스를 생성합니다.
"""

import sys
import os
import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# 프로젝트 루트를 Python 경로에 추가 (backend 디렉토리)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv()

def get_access_token():
    """서비스 계정을 사용하여 액세스 토큰 획득"""
    cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'config/firebase-credentials.json')
    
    if not os.path.exists(cred_path):
        # 실제 파일명으로 시도
        cred_path = 'config/eap-intern-roni-firebase-adminsdk-fbsvc-b39ae47a16.json'
    
    if not os.path.exists(cred_path):
        raise FileNotFoundError(f"Firebase 서비스 계정 키 파일을 찾을 수 없습니다: {cred_path}")
    
    credentials = service_account.Credentials.from_service_account_file(
        cred_path,
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    
    credentials.refresh(Request())
    return credentials.token

def create_firestore_index_via_rest_api():
    """
    Firestore Admin REST API를 사용하여 인덱스 생성
    
    참고: Firestore 인덱스는 일반적으로 firestore.indexes.json 파일을 통해 관리됩니다.
    이 스크립트는 REST API를 통해 직접 생성을 시도합니다.
    """
    print("=" * 60)
    print("Firestore 인덱스 생성 (REST API 사용)")
    print("=" * 60)
    
    try:
        # 액세스 토큰 획득
        print("\n1. 액세스 토큰 획득 중...")
        access_token = get_access_token()
        print("   ✅ 액세스 토큰 획득 성공")
        
        project_id = "eap-intern-roni"
        database_id = "(default)"  # 기본 데이터베이스
        
        # Firestore Admin API 엔드포인트
        base_url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/{database_id}"
        
        # 인덱스 정의
        indexes_to_create = [
            {
                "collectionId": "announcements",
                "queryScope": "COLLECTION",
                "fields": [
                    {
                        "fieldPath": "status",
                        "order": "ASCENDING"
                    },
                    {
                        "fieldPath": "created_at",
                        "order": "DESCENDING"
                    }
                ]
            }
        ]
        
        print(f"\n2. 인덱스 생성 시도 중...")
        print(f"   프로젝트: {project_id}")
        print(f"   컬렉션: announcements")
        print(f"   필드: status (ASC), created_at (DESC)")
        
        # Firestore Admin API는 인덱스를 직접 생성하는 엔드포인트를 제공하지 않습니다.
        # 대신 firestore.indexes.json 파일을 생성하고 Firebase CLI를 사용하는 것이 권장됩니다.
        
        print("\n⚠️  참고: Firestore Admin REST API는 인덱스를 직접 생성하는 엔드포인트를 제공하지 않습니다.")
        print("   대신 firestore.indexes.json 파일을 생성하고 Firebase CLI로 배포하는 방법을 사용합니다.")
        
        # firestore.indexes.json 파일 생성
        print("\n3. firestore.indexes.json 파일 생성 중...")
        indexes_config = create_indexes_config_file()
        print(f"   ✅ 파일 생성 완료: {indexes_config}")
        
        # Firebase CLI를 통한 배포 안내
        print("\n" + "=" * 60)
        print("✅ 인덱스 설정 파일 생성 완료!")
        print("=" * 60)
        print("\n다음 단계:")
        print("1. Firebase CLI 설치:")
        print("   npm install -g firebase-tools")
        print("\n2. Firebase 로그인:")
        print("   firebase login")
        print("\n3. 프로젝트 디렉토리에서 Firebase 초기화:")
        print("   firebase init firestore")
        print("   (기존 설정이 있으면 건너뛰기)")
        print("\n4. 인덱스 배포:")
        print("   firebase deploy --only firestore:indexes")
        print("\n또는 Firebase 콘솔에서 수동으로 인덱스를 생성할 수 있습니다:")
        print("https://console.firebase.google.com/project/eap-intern-roni/firestore/indexes")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def create_indexes_config_file():
    """firestore.indexes.json 파일 생성"""
    indexes_config = {
        "indexes": [
            {
                "collectionGroup": "announcements",
                "queryScope": "COLLECTION",
                "fields": [
                    {
                        "fieldPath": "status",
                        "order": "ASCENDING"
                    },
                    {
                        "fieldPath": "created_at",
                        "order": "DESCENDING"
                    }
                ]
            },
            {
                "collectionGroup": "announcements",
                "queryScope": "COLLECTION",
                "fields": [
                    {
                        "fieldPath": "agency",
                        "order": "ASCENDING"
                    },
                    {
                        "fieldPath": "created_at",
                        "order": "DESCENDING"
                    }
                ]
            },
            {
                "collectionGroup": "announcements",
                "queryScope": "COLLECTION",
                "fields": [
                    {
                        "fieldPath": "business_type",
                        "order": "ASCENDING"
                    },
                    {
                        "fieldPath": "created_at",
                        "order": "DESCENDING"
                    }
                ]
            }
        ],
        "fieldOverrides": []
    }
    
    # 프로젝트 루트에 파일 생성
    config_path = os.path.join(os.path.dirname(__file__), '..', 'firestore.indexes.json')
    config_path = os.path.abspath(config_path)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(indexes_config, f, indent=2, ensure_ascii=False)
    
    print(f"   파일 경로: {config_path}")
    return config_path

def create_index_via_query_error():
    """
    쿼리를 실행하여 오류 메시지의 링크를 통해 인덱스 자동 생성
    
    이 방법은 실제로 쿼리를 실행하고, 오류 메시지에 포함된 링크를 출력합니다.
    """
    print("\n" + "=" * 60)
    print("인덱스 자동 생성 링크 생성")
    print("=" * 60)
    
    try:
        from services.firebase_service import init_firebase, get_db
        from firebase_admin import firestore
        
        print("\n1. Firebase 초기화 중...")
        init_firebase()
        print("   ✅ Firebase 초기화 성공")
        
        print("\n2. 인덱스가 필요한 쿼리 실행 중...")
        print("   (인덱스가 없으면 오류 메시지에 생성 링크가 포함됩니다)")
        
        db = get_db()
        
        # 인덱스가 필요한 쿼리 실행
        try:
            query = db.collection('announcements')\
                .where('status', '==', 'pending')\
                .order_by('created_at', direction=firestore.Query.DESCENDING)\
                .limit(1)
            
            results = list(query.stream())
            print("   ✅ 쿼리 성공 (인덱스가 이미 존재하거나 데이터가 없습니다)")
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n   ⚠️  쿼리 오류 발생 (예상된 동작):")
            print(f"   {error_msg}")
            
            # 오류 메시지에서 인덱스 생성 링크 찾기
            if "index" in error_msg.lower() or "인덱스" in error_msg:
                print("\n   📋 오류 메시지에 인덱스 생성 링크가 포함되어 있을 수 있습니다.")
                print("   위의 오류 메시지를 확인하고 링크를 클릭하여 인덱스를 생성하세요.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Firestore 인덱스 생성 방법 선택:")
    print("1. firestore.indexes.json 파일 생성 (권장)")
    print("2. 쿼리 실행하여 자동 생성 링크 확인")
    print("\n방법 1을 실행합니다...\n")
    
    success = create_firestore_index_via_rest_api()
    
    if success:
        print("\n방법 2도 시도합니다...\n")
        create_index_via_query_error()
    
    sys.exit(0 if success else 1)

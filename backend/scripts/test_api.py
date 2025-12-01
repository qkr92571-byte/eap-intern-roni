#!/usr/bin/env python3
"""
API 엔드포인트 테스트 스크립트

백엔드 서버가 실행 중일 때 API를 테스트합니다.
"""

import requests
import json
import sys

API_BASE_URL = "http://localhost:5001/api"

def test_api_endpoints():
    """API 엔드포인트 테스트"""
    print("=" * 60)
    print("API 엔드포인트 테스트")
    print("=" * 60)
    
    # 1. Health check
    print("\n1. Health check 테스트...")
    try:
        response = requests.get("http://localhost:5001/")
        if response.status_code == 200:
            print(f"   ✅ Health check 성공: {response.json()}")
        else:
            print(f"   ❌ Health check 실패: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ⚠️  백엔드 서버가 실행되지 않았습니다.")
        print("   다음 명령어로 서버를 시작하세요:")
        print("   cd backend && source venv/bin/activate && python app.py")
        return False
    
    # 2. 공고 목록 조회
    print("\n2. 공고 목록 조회 테스트...")
    try:
        response = requests.get(f"{API_BASE_URL}/announcements?limit=10")
        if response.status_code == 200:
            data = response.json()
            announcements = data.get('data', [])
            print(f"   ✅ 공고 목록 조회 성공: {len(announcements)}개")
            if announcements:
                first = announcements[0]
                print(f"      첫 번째 공고: {first.get('title', 'N/A')}")
        else:
            print(f"   ❌ 공고 목록 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 오류: {str(e)}")
    
    # 3. 특정 공고 조회 (첫 번째 공고 ID 사용)
    print("\n3. 특정 공고 조회 테스트...")
    try:
        response = requests.get(f"{API_BASE_URL}/announcements")
        if response.status_code == 200:
            data = response.json()
            announcements = data.get('data', [])
            if announcements:
                first_id = announcements[0].get('id')
                response = requests.get(f"{API_BASE_URL}/announcements/{first_id}")
                if response.status_code == 200:
                    announcement = response.json().get('data', {})
                    print(f"   ✅ 공고 상세 조회 성공")
                    print(f"      제목: {announcement.get('title', 'N/A')}")
                    print(f"      공고번호: {announcement.get('announcement_number', 'N/A')}")
                    print(f"      기관: {announcement.get('agency', 'N/A')}")
                else:
                    print(f"   ❌ 공고 상세 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 오류: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ API 테스트 완료!")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    success = test_api_endpoints()
    sys.exit(0 if success else 1)



#!/usr/bin/env python3
"""
초기 프롬프트를 Firestore에 업로드하는 스크립트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가 (backend 디렉토리)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from services.firebase_service import init_firebase
from services.prompt_service import save_prompt, get_prompt

def upload_initial_prompt():
    """
    로컬 프롬프트 파일을 Firestore에 업로드
    """
    print("=" * 60)
    print("초기 프롬프트 Firestore 업로드")
    print("=" * 60)
    print()
    
    # Firebase 초기화
    try:
        init_firebase()
        print("✅ Firebase 초기화 성공")
    except Exception as e:
        print(f"❌ Firebase 초기화 실패: {str(e)}")
        print("   Firebase 키 파일을 확인해주세요.")
        return False
    
    # 로컬 프롬프트 파일 읽기
    prompt_file = Path(backend_dir) / 'prompts' / 'eap_review_prompt.txt'
    
    if not prompt_file.exists():
        print(f"❌ 프롬프트 파일을 찾을 수 없습니다: {prompt_file}")
        return False
    
    print(f"📄 프롬프트 파일 로드 중: {prompt_file}")
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_content = f.read()
    
    print(f"   프롬프트 크기: {len(prompt_content)} 문자")
    print()
    
    # 기존 프롬프트 확인
    existing_prompt = get_prompt()
    if existing_prompt:
        print("⚠️  Firestore에 이미 프롬프트가 존재합니다.")
        user_input = input("   덮어쓰시겠습니까? (yes/no): ").strip().lower()
        if user_input not in ('yes', 'y'):
            print("   업로드가 취소되었습니다.")
            return False
    
    # Firestore에 저장
    print("📤 Firestore에 프롬프트 업로드 중...")
    success = save_prompt(prompt_content)
    
    if success:
        print("✅ 프롬프트 업로드 완료!")
        print()
        print("이제 AI 검수 시 Firestore의 프롬프트가 사용됩니다.")
        return True
    else:
        print("❌ 프롬프트 업로드 실패!")
        return False

if __name__ == "__main__":
    success = upload_initial_prompt()
    sys.exit(0 if success else 1)


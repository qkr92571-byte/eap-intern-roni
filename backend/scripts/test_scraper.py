"""
Playwright 스크래퍼 테스트 스크립트
"""

import sys
import os
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가 (backend 디렉토리)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from services.scraper_service import run_scraper
from services.keyword_service import get_keywords
from services.file_service import load_report, get_history_numbers

def test_scraper():
    """스크래퍼 테스트 실행"""
    print("=" * 60)
    print("Playwright 스크래퍼 테스트 시작")
    print("=" * 60)
    print(f"테스트 날짜: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 키워드 확인
    print("1. 저장된 키워드 확인:")
    keywords = get_keywords()
    print(f"   키워드: {keywords}")
    print(f"   개수: {len(keywords)}개")
    print()
    
    # 히스토리 확인
    print("2. 히스토리 확인:")
    request_date = datetime.now()  # 오늘 날짜
    history_numbers = get_history_numbers(request_date)
    print(f"   요청일: {request_date.strftime('%Y-%m-%d')}")
    print(f"   히스토리 공고번호 개수: {len(history_numbers)}개")
    if len(history_numbers) > 0:
        print(f"   예시 공고번호: {list(history_numbers)[:3]}")
    print()
    
    # 스크래퍼 실행
    print("3. 스크래퍼 실행:")
    print("   (이 작업은 몇 분 정도 소요될 수 있습니다...)")
    print()
    
    try:
        results = run_scraper(keywords=keywords, request_date=request_date)
        
        print()
        print("4. 수집 결과:")
        print(f"   수집된 공고 개수: {len(results)}개")
        
        if results:
            print()
            print("   수집된 공고 예시:")
            for i, announcement in enumerate(results[:3], 1):
                print(f"   [{i}] {announcement.get('title', 'N/A')}")
                print(f"       공고번호: {announcement.get('announcement_number', 'N/A')}")
                print(f"       기관: {announcement.get('agency', 'N/A')}")
                print()
        
        # Report 파일 확인
        print("5. Report 파일 확인:")
        report_data = load_report(request_date)
        print(f"   Report 파일의 공고 개수: {len(report_data)}개")
        
        # History 파일 확인
        print("6. History 파일 확인:")
        history_after = get_history_numbers(request_date)
        print(f"   히스토리 공고번호 개수 (업데이트 후): {len(history_after)}개")
        new_numbers = history_after - history_numbers
        print(f"   새로 추가된 공고번호: {len(new_numbers)}개")
        
        print()
        print("=" * 60)
        print("✅ 테스트 완료!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ 테스트 실패!")
        print("=" * 60)
        print(f"오류: {str(e)}")
        import traceback
        print()
        print("상세 오류:")
        print(traceback.format_exc())
        return False

if __name__ == '__main__':
    success = test_scraper()
    sys.exit(0 if success else 1)



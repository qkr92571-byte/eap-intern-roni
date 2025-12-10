#!/usr/bin/env python3
"""
경쟁사 리포트를 Firestore에 업로드
"""

import json
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.firebase_service import get_db
# 프로젝트 루트의 competitor_reports 폴더 사용
PROJECT_ROOT = BASE_DIR.parent if BASE_DIR.name == 'backend' else BASE_DIR
REPORT_DIR = PROJECT_ROOT / "competitor_reports"


def upload_competitor_reports():
    """경쟁사 리포트를 Firestore에 업로드"""
    db = get_db()
    collection_name = "competitor_awards"
    
    # 모든 리포트 파일 읽기
    report_files = sorted(REPORT_DIR.glob("competitor_awards_*.json"))
    
    if not report_files:
        print("❌ 업로드할 리포트 파일이 없습니다.")
        return
    
    total_uploaded = 0
    total_skipped = 0
    
    for report_file in report_files:
        print(f"\n📄 처리 중: {report_file.name}")
        
        with open(report_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 배열 형태인 경우
        if isinstance(data, list):
            items = data
        # 객체 형태인 경우 (period, items 필드 포함)
        elif isinstance(data, dict) and 'items' in data:
            items = data['items']
            if 'period' in data:
                print(f"   기간: {data['period'].get('start', '')} ~ {data['period'].get('end', '')}")
        else:
            print("   ⚠️  지원하지 않는 파일 형식입니다.")
            continue
        
        for item in items:
            announcement_number = item.get('announcement_number', '')
            if not announcement_number:
                continue
            
            # 중복 체크
            existing = db.collection(collection_name).where(
                'announcement_number', '==', announcement_number
            ).limit(1).stream()
            
            if list(existing):
                total_skipped += 1
                continue
            
            # Firestore에 저장할 데이터 준비
            firestore_data = {
                'announcement_number': announcement_number,
                'title': item.get('title', ''),
                'agency': item.get('agency', ''),
                'publish_date': item.get('publish_date', ''),
                'budget_amount': item.get('budget_amount'),
                'estimated_price': item.get('estimated_price'),
                'business_type': item.get('business_type', ''),
                'final_amount': item.get('final_amount'),
                'winner': item.get('winner', ''),
                'source': item.get('source', '나라장터 낙찰정보'),
                'created_at': item.get('created_at', datetime.now().isoformat()),
            }
            
            # Firestore에 저장
            db.collection(collection_name).add(firestore_data)
            total_uploaded += 1
            print(f"   ✅ 업로드: {announcement_number} - {item.get('title', '')[:30]}...")
    
    print(f"\n{'='*60}")
    print(f"업로드 완료!")
    print(f"  - 업로드: {total_uploaded}건")
    print(f"  - 스킵 (중복): {total_skipped}건")
    print(f"{'='*60}")


if __name__ == "__main__":
    upload_competitor_reports()


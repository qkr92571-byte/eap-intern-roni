"""
공고 상태 업데이트 스크립트
두 공고를 적합으로 변경하고 Firestore에 적용
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.firebase_service import init_firebase, update_announcement_by_number

def main():
    # Firebase 초기화
    init_firebase()
    
    # 업데이트할 공고 목록
    announcements = [
        'R26BK01325805-000',
        'R26BK01318271-000'
    ]
    
    print("=" * 60)
    print("공고 상태 업데이트")
    print("=" * 60)
    
    for ann_number in announcements:
        update_data = {
            'status': 'approved',
            'reviewed': True,
            'reviewed_at': datetime.now().isoformat(),
            'review_result': '- 적합 여부: 적합\n- 이유: 수동 검토 후 적합으로 판단'
        }
        
        result = update_announcement_by_number(ann_number, update_data)
        if result:
            print(f'✅ {ann_number} Firestore 업데이트 완료')
        else:
            print(f'❌ {ann_number} Firestore 업데이트 실패 (공고를 찾을 수 없습니다)')
    
    print("\n업데이트 완료!")

if __name__ == '__main__':
    main()

"""
공고 상태 업데이트 스크립트
두 공고를 적합으로 변경하고 Firestore에 적용
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.firebase_service import init_firebase, update_announcement_by_number

def _candidate_numbers(raw_number: str) -> list[str]:
    raw = (raw_number or "").strip()
    if not raw:
        return []
    # Firestore에는 '-000' 형태로 저장되는 경우가 있어 변형을 함께 시도
    candidates = [raw]
    if "-" not in raw:
        candidates.append(f"{raw}-000")
    # 중복 제거 (순서 유지)
    seen = set()
    uniq: list[str] = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq

def main():
    # Firebase 초기화
    init_firebase()
    
    # 업데이트할 공고 목록
    announcements = [
        'R26BK01388646',
        'R26BK01388592'
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
        
        updated = False
        tried = _candidate_numbers(ann_number)
        for candidate in tried:
            result = update_announcement_by_number(candidate, update_data)
            if result:
                updated = True
                if candidate == ann_number:
                    print(f'✅ {ann_number} Firestore 업데이트 완료')
                else:
                    print(f'✅ {ann_number} (저장값: {candidate}) Firestore 업데이트 완료')
                break
        if not updated:
            print(f'❌ {ann_number} Firestore 업데이트 실패 (공고를 찾을 수 없습니다) - 시도: {", ".join(tried)}')
    
    print("\n업데이트 완료!")

if __name__ == '__main__':
    main()

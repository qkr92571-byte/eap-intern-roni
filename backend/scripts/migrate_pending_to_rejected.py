"""
Firestore 마이그레이션 스크립트: pending → rejected

announcements 컬렉션에서 status='pending' 인 문서를 모두 status='rejected' 로 업데이트합니다.
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv(backend_dir / '.env')

from services.firebase_service import get_db


def migrate_pending_to_rejected(dry_run: bool = False) -> None:
    db = get_db()
    collection = db.collection('announcements')

    # status='pending' 인 문서 조회
    pending_docs = list(collection.where('status', '==', 'pending').stream())

    if not pending_docs:
        print("✅ 마이그레이션 대상 없음 (pending 문서 0개)")
        return

    print(f"📋 마이그레이션 대상: {len(pending_docs)}개 문서")

    if dry_run:
        print("🔍 [DRY RUN] 실제 업데이트는 수행하지 않습니다.")
        for doc in pending_docs:
            data = doc.to_dict()
            print(f"  - {doc.id}: {data.get('title', '')[:50]}")
        return

    # 컨펌
    answer = input(f"\n⚠️  {len(pending_docs)}개 문서의 status를 'rejected'로 변경합니다. 계속하시겠습니까? (yes/no): ")
    if answer.strip().lower() != 'yes':
        print("❌ 마이그레이션이 취소되었습니다.")
        return

    success = 0
    failed = 0

    for doc in pending_docs:
        try:
            doc.reference.update({
                'status': 'rejected',
                'rejection_reason': 'migrated_from_pending',
            })
            success += 1
            print(f"  ✅ {doc.id}")
        except Exception as e:
            failed += 1
            print(f"  ❌ {doc.id}: {e}")

    print(f"\n완료: 성공 {success}개 / 실패 {failed}개")


if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv
    migrate_pending_to_rejected(dry_run=dry_run)

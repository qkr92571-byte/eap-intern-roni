#!/usr/bin/env python3
"""
리포트 파일 기준 GPT 검수(적합/부적합) 후 Firestore 업로드(Upsert)

- 1) report_YYMMDD.json 로드
- 2) ChatGPT로 각 공고 적합/부적합 판정(리포트 파일에 status/review_* 반영)
- 3) Firestore에 공고번호 기준으로 upsert (삭제 없음)

주의:
- 슬랙 전송은 하지 않습니다.
- Firestore에서 "삭제"는 하지 않습니다. (안전)
"""

import sys
import os
from datetime import datetime
from typing import Dict

# 프로젝트 루트를 Python 경로에 추가 (backend 디렉토리)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from services.review_service import review_report_file
from services.file_service import load_report
from services.firebase_service import (
    init_firebase,
    get_db,
    save_announcement,
    update_announcement,
)


def _prepare_firestore_data(announcement: Dict) -> Dict:
    """Firestore 스키마에 맞게 공고 데이터 정리 (None 제거)"""
    firestore_data = {
        "title": announcement.get("title", ""),
        "announcement_number": announcement.get("announcement_number", ""),
        "agency": announcement.get("agency", ""),
        "publish_date": announcement.get("publish_date", ""),
        "budget_amount": announcement.get("budget_amount"),
        "estimated_price": announcement.get("estimated_price"),
        "business_type": announcement.get("business_type", ""),
        "created_at": announcement.get("created_at", datetime.now().isoformat()),
        "source": announcement.get("source", "나라장터"),
        "status": announcement.get("status", "pending"),
        "filtered": announcement.get("filtered", False),
        "reviewed": announcement.get("reviewed", True),
        "review_result": announcement.get("review_result", ""),
        "review_model": announcement.get("review_model", ""),
        "reviewed_at": announcement.get("reviewed_at", ""),
        "service_items": announcement.get("service_items"),
        "service_items_extracted_at": announcement.get("service_items_extracted_at"),
        "display_status": announcement.get("display_status", 20),  # 20: 노출, 40: 삭제됨
    }

    return {k: v for k, v in firestore_data.items() if v is not None}


def review_and_upsert(report_date: datetime) -> None:
    print("=" * 60)
    print("GPT 검수(적합/부적합) → Firestore 업로드(Upsert)")
    print("=" * 60)
    print(f"날짜: {report_date.strftime('%Y-%m-%d')}")
    print()

    # 1) GPT 검수 (사용자 요청으로 컨펌 없이 진행)
    review_result = review_report_file(report_date, confirm_before_review=False)
    if not review_result.get("success", False):
        raise RuntimeError(review_result.get("error", "검수 실패"))

    # 2) 리포트 재로드 (검수 결과 반영된 파일)
    report_data = load_report(report_date)
    if not isinstance(report_data, list) or not report_data:
        raise RuntimeError("검수 후 리포트 데이터가 비어있습니다.")

    # 3) Firestore upsert
    print()
    print("-" * 60)
    print("Firestore 업로드(Upsert) 시작 (삭제 없음)")
    print("-" * 60)

    init_firebase()
    db = get_db()

    # 공고번호 기준으로 기존 문서들을 한 번에 조회(쿼리 최소화)
    numbers = []
    for ann in report_data:
        num = (ann.get("announcement_number") or "").strip()
        if num:
            numbers.append(num)

    existing_by_number: Dict[str, str] = {}
    chunk_size = 30  # Firestore 'in' 쿼리 제한
    for i in range(0, len(numbers), chunk_size):
        chunk = numbers[i : i + chunk_size]
        # 빈 chunk 방지
        if not chunk:
            continue
        docs = db.collection("announcements").where("announcement_number", "in", chunk).stream()
        for doc in docs:
            data = doc.to_dict() or {}
            num = (data.get("announcement_number") or "").strip()
            if num:
                existing_by_number[num] = doc.id

    added = 0
    updated = 0
    skipped = 0
    failed = 0

    for idx, ann in enumerate(report_data, 1):
        try:
            announcement_number = (ann.get("announcement_number") or "").strip()
            if not announcement_number:
                skipped += 1
                continue

            firestore_data = _prepare_firestore_data(ann)

            doc_id = existing_by_number.get(announcement_number)
            if doc_id:
                update_announcement(doc_id, firestore_data)
                updated += 1
            else:
                save_announcement(firestore_data)
                added += 1

            if idx % 10 == 0:
                print(f"진행 중... {idx}/{len(report_data)} (추가 {added}, 업데이트 {updated}, 건너뜀 {skipped}, 실패 {failed})")
        except Exception as e:
            failed += 1
            print(f"  ❌ 업로드 실패: {ann.get('announcement_number', '')} - {e}")

    print()
    print("=" * 60)
    print("완료")
    print("=" * 60)
    print(f"[검수] 검수 {review_result.get('reviewed_count', 0)}개 / 적합 {review_result.get('approved_count', 0)}개 / 부적합 {review_result.get('rejected_count', 0)}개")
    print(f"[업로드] 추가 {added}개 / 업데이트 {updated}개 / 건너뜀 {skipped}개 / 실패 {failed}개")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GPT 검수 후 Firestore 업로드(Upsert)")
    parser.add_argument("--date", required=True, help="날짜 (YYYY-MM-DD)")
    args = parser.parse_args()

    try:
        report_date = datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print("❌ 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해주세요.")
        sys.exit(1)

    review_and_upsert(report_date)


"""
Skills 모듈
- 재사용 가능한 단일 책임 단위
- 각 스킬은 명확한 입력/출력 계약을 가짐
- 부수 효과(파일 쓰기, DB, 슬랙)가 명시된 문서를 가짐
"""

# 순환 import 방지를 위해 __init__에서는 export만 정의
__all__ = [
    'skill_scrape_g2b',
    'skill_review_announcements',
    'skill_upsert_firestore',
    'skill_send_slack_report',
    'skill_collect_service_items',
]

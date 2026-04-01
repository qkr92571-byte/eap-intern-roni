"""
리포트 파일 검수 서비스
- 리포트 파일의 공고들을 ChatGPT API로 검수
- 검수 결과를 리포트 파일에 반영
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from services.file_service import load_report, REPORT_DIR, get_date_string
from orchestration.policies import request_confirmation
from services.prompt_service import get_prompt as get_prompt_from_firestore
from utils.openai_client import get_openai_client
from utils.constants import (
    STATUS_PENDING,
    STATUS_APPROVED,
    STATUS_REJECTED,
    OPENAI_MODEL_REVIEW,
    OPENAI_MAX_TOKENS_REVIEW,
    OPENAI_TEMPERATURE_REVIEW
)

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).parent.parent
PROMPTS_DIR = PROJECT_ROOT / 'prompts'
EAP_REVIEW_PROMPT_PATH = PROMPTS_DIR / 'eap_review_prompt.txt'

def load_eap_review_prompt() -> str:
    """
    EAP 검수 프롬프트 로드
    - 우선순위: Firestore → 로컬 파일 → 기본 프롬프트
    
    Returns:
        프롬프트 텍스트
    """
    # 1. Firestore에서 프롬프트 조회 시도 (네트워크 이슈/지연 시 스킵 가능)
    if os.getenv("SKIP_FIRESTORE_PROMPT", "").strip().lower() not in ("1", "true", "yes"):
        firestore_prompt = get_prompt_from_firestore()
        if firestore_prompt:
            return firestore_prompt
    
    # 2. 로컬 파일에서 로드 시도
    if EAP_REVIEW_PROMPT_PATH.exists():
        with open(EAP_REVIEW_PROMPT_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    
    # 3. 기본 프롬프트 (파일이 없을 경우)
    return """
근로자지원프로그램(EAP, Employee Assistance Program)은 근로자가 직장이나 가정에서 겪는 다양한 문제로 인해 업무 성과에 부정적인 영향을 받지 않도록, 전문가 상담 및 코칭 등 심리 서비스를 무상으로 제공하는 제도입니다.

다음 공고가 EAP에 적합한지 검토해주세요.
"""

# 제외 키워드 목록 (제목에 포함되면 자동으로 부적합 처리)
EXCLUSION_KEYWORDS = [
    # ── 기존 유지 ────────────────────────────────────────
    '콜센터',
    '차량 임차',
    '차량임차',
    '운행',
    '통근버스',
    '통근 버스',
    '버스 운행',
    '버스운행',
    '근로자 파견',
    # '파견 용역', '파견용역'은 제외하지 않음 (필요한 공고가 있을 수 있음)

    # ── 취업/진로/직업 상담 (비심리적) ───────────────────
    '취업상담',
    '취업 상담',
    '직업상담',
    '직업 상담',
    '진로상담',
    '진로 상담',
    '진학상담',
    '진학 상담',
    '취업성공',           # 취업성공디딤돌 등 취업지원 사업

    # ── 세무/법률/금융 상담 (비심리적) ───────────────────
    '세무상담',
    '세무 상담',
    '법률상담',
    '법률 상담',
    '소득세',             # 종합소득세 홈택스 임시상담 등

    # ── 농업/수출/가맹 상담 (비심리적) ───────────────────
    '수출상담',
    '수출 상담',
    '바이어 상담',
    '가맹상담',
    '창업상담',
    '주거상담',
    '주거 상담',

    # ── IT 상담시스템 유지보수 ────────────────────────────
    '상담시스템 유지보수',
    '상담 시스템 유지보수',

    # ── 상담사 자격시험 ───────────────────────────────────
    '자격시험',
    '상담사 자격',

    # ── 고객서비스 품질관리 ───────────────────────────────
    '전화상담 품질',
    '고객만족도 조사',

    # ── 관광/통역 ─────────────────────────────────────────
    '관광통역',
]

# 제목만으로 명확히 적합 판단할 수 있는 키워드 패턴
# keyword: 이 문자열이 제목에 포함되면 적합 가능성 높음
# exceptions: keyword와 함께 있을 때 fast_approve 불가 (시스템 개발 등 제외)
FAST_APPROVE_PATTERNS = [
    # ── 기존 유지 ────────────────────────────────────────────────
    {'keyword': '찾아가는 상담실', 'exceptions': ['개발', '구축', '시스템']},
    {'keyword': '근로자지원프로그램(EAP)', 'exceptions': ['개발', '구축']},
    {'keyword': 'EAP 운영', 'exceptions': ['개발', '구축']},

    # ── EAP 직접 표기 변형 ────────────────────────────────────────
    {'keyword': 'EAP운영', 'exceptions': ['개발', '구축']},
    {'keyword': '근로자지원프로그램 운영', 'exceptions': ['개발', '구축']},

    # ── 심리상담 서비스 직접 표기 ─────────────────────────────────
    # 실제 적합: "대중문화예술인 심리상담 위탁용역", "청년 마음이음 전문심리상담"
    {'keyword': '심리상담 위탁', 'exceptions': ['개발', '구축', '시스템']},
    {'keyword': '심리상담 용역', 'exceptions': ['개발', '구축', '시스템']},
    {'keyword': '심리상담 운영', 'exceptions': ['개발', '구축', '시스템']},
    {'keyword': '전문심리상담', 'exceptions': ['개발', '구축', '시스템']},

    # ── 학생/청소년 정서 관련 ─────────────────────────────────────
    # 실제 적합: "학생정서행동특성검사 상담기관 위탁운영" (세종교육청)
    {'keyword': '정서행동특성검사', 'exceptions': ['개발', '구축', '시스템']},

    # ── 특수 심리지원 ─────────────────────────────────────────────
    # 실제 적합: "펫로스 심리지원 시범사업"
    {'keyword': '심리지원 시범', 'exceptions': ['개발', '구축']},
    # 실제 적합: "청년 마음이음 사업"
    {'keyword': '마음이음', 'exceptions': ['개발', '구축']},

    # ── 인력 파견형 EAP ───────────────────────────────────────────
    {'keyword': '전문상담사 파견', 'exceptions': ['개발', '구축']},
    {'keyword': '심리상담사 파견', 'exceptions': ['개발', '구축']},

    # ── 소방/공무원 심리지원 ──────────────────────────────────────
    # 실제 적합: "전국 소방공무원 마음건강 설문조사 통계 및 분석"
    {'keyword': '소방공무원 마음', 'exceptions': ['개발', '구축']},
    {'keyword': '마음건강 설문', 'exceptions': ['개발', '구축', '시스템']},
]

# 검수용 첨부파일 텍스트 제한
ATTACHMENT_MAX_CHARS_PER_FILE = 2000   # 파일 1개당 최대 문자 수
ATTACHMENT_MAX_TOTAL_CHARS = 4000      # GPT에 전달할 전체 최대 문자 수

def should_exclude_by_keywords(announcement: Dict) -> tuple[bool, str]:
    """
    제외 키워드로 인한 자동 부적합 판단
    
    Args:
        announcement: 공고 데이터 딕셔너리
        
    Returns:
        (제외 여부, 제외 사유) 튜플
    """
    title = announcement.get('title', '').lower()
    
    for keyword in EXCLUSION_KEYWORDS:
        if keyword.lower() in title:
            return True, f"제외 키워드 포함: '{keyword}'"
    
    return False, ""


def classify_by_title(announcement: Dict) -> str:
    """
    제목 기반 빠른 분류 (1단계 필터)

    Returns:
        'rejected'  - 제외 키워드 hit → 첨부파일 불필요
        'approved'  - 명확 EAP 키워드 hit → 첨부파일 불필요
        'uncertain' - 판단 불가 → 2단계(첨부파일 기반 GPT) 필요
    """
    # 제외 키워드 체크
    exclude, _ = should_exclude_by_keywords(announcement)
    if exclude:
        return 'rejected'

    title = announcement.get('title', '')

    # 명확 적합 키워드 체크
    for pattern in FAST_APPROVE_PATTERNS:
        if pattern['keyword'] in title:
            has_exception = any(exc in title for exc in pattern['exceptions'])
            if not has_exception:
                return 'approved'

    return 'uncertain'


def fetch_attachment_text_for_review(
    announcement_number: str,
    title: Optional[str] = None,
    created_at: Optional[str] = None,
) -> Tuple[str, str]:
    """
    검수용 첨부파일 텍스트 추출 (2단계 필터에서 호출)

    Returns:
        (text, method)
        method: 'with_attachment' | 'attachment_failed'
    """
    try:
        from services.attachment_service import analyze_attachments

        print(f"      첨부파일 다운로드 중: {announcement_number}")
        result = analyze_attachments(
            announcement_number,
            bid_ord='000',
            title=title,
            created_at=created_at,
        )

        if not result.get('success'):
            print(f"      ⚠️  첨부파일 다운로드 실패: {result.get('error', '알 수 없는 오류')}")
            return '', 'attachment_failed'

        texts = []
        total_chars = 0

        for att in result.get('attachments', []):
            # zip 압축 해제된 파일 목록 우선 처리
            files_to_check = att.get('extracted_files', []) or [att]
            for f in files_to_check:
                if f.get('extract_status') == 'ok' and total_chars < ATTACHMENT_MAX_TOTAL_CHARS:
                    summary = f.get('summary', '')
                    if summary:
                        chunk = summary[:ATTACHMENT_MAX_CHARS_PER_FILE]
                        filename = f.get('name', '알 수 없는 파일')
                        texts.append(f"[파일명: {filename}]\n{chunk}")
                        total_chars += len(chunk)

        if texts:
            print(f"      ✅ 첨부파일 텍스트 추출 완료 ({total_chars}자, {len(texts)}개 파일)")
            return '\n\n'.join(texts), 'with_attachment'
        else:
            print(f"      ⚠️  첨부파일에서 텍스트를 추출하지 못했습니다.")
            return '', 'attachment_failed'

    except Exception as e:
        print(f"      ❌ 첨부파일 텍스트 추출 중 오류: {e}")
        return '', 'attachment_failed'


def review_report_file(report_date=None, confirm_before_review=True) -> Dict:
    """
    리포트 파일의 모든 공고를 ChatGPT API로 검수하고 리포트 파일을 업데이트
    
    Args:
        report_date: 날짜 (기본값: 오늘)
        confirm_before_review: 검수 전 사용자 컨펌 받기 (기본값: True)
    
    Returns:
        검수 결과 딕셔너리
    """
    if report_date is None:
        report_date = datetime.now()
    
    print("=" * 60)
    print("리포트 파일 검수 시작")
    print("=" * 60)
    print(f"날짜: {report_date.strftime('%Y-%m-%d')}")
    
    # OpenAI API 키 확인
    try:
        get_openai_client()
    except ValueError as e:
        error_msg = f"⚠️  {str(e)}"
        print(error_msg)
        return {
            'success': False,
            'error': error_msg,
            'reviewed_count': 0,
            'approved_count': 0,
            'rejected_count': 0
        }
    
    try:
        # 리포트 파일 로드
        print("\n1. 리포트 파일 로드 중...")
        report_data = load_report(report_date)
        
        if not report_data:
            print("   ⚠️  검수할 데이터가 없습니다.")
            return {
                'success': False,
                'error': '검수할 데이터가 없습니다.',
                'reviewed_count': 0,
                'approved_count': 0,
                'rejected_count': 0
            }
        
        print(f"   ✅ 리포트 파일 로드 완료: {len(report_data)}개 공고")
        
        # 사용자 컨펌 확인
        if confirm_before_review:
            print("\n⚠️  ChatGPT API 사용 시 비용이 발생합니다.")
            print(f"   검수할 공고 수: {len(report_data)}개")
            print(f"   예상 비용: 약 ${len(report_data) * 0.002:.2f} (gpt-3.5-turbo 기준)")
            if not request_confirmation("검수를 진행하시겠습니까? (yes/no): "):
                print("   검수가 취소되었습니다.")
                return {
                    'success': False,
                    'error': '사용자가 검수를 취소했습니다.',
                    'reviewed_count': 0,
                    'approved_count': 0,
                    'rejected_count': 0
                }
            print()
        
        # 각 공고 검수 (2단계 파이프라인)
        print("\n2. 공고 검수 중 (1단계: 키워드 필터 → 2단계: 첨부파일 기반 GPT 검수)...")
        reviewed_count = 0
        approved_count = 0
        rejected_count = 0
        pending_count = 0
        error_count = 0

        for idx, announcement in enumerate(report_data, 1):
            try:
                announcement_number = announcement.get('announcement_number', '')
                title = announcement.get('title', '')

                # 이미 검수된 공고는 건너뛰기
                if announcement.get('reviewed', False) and announcement.get('review_result') and announcement.get('status'):
                    print(f"   [{idx}/{len(report_data)}] 이미 검수됨: {announcement_number}")
                    reviewed_count += 1
                    status = announcement.get('status')
                    if status == STATUS_APPROVED:
                        approved_count += 1
                    elif status == STATUS_REJECTED:
                        rejected_count += 1
                    else:
                        pending_count += 1
                    continue

                # ── 1단계: 제목 기반 빠른 분류 ──────────────────────────────
                title_class = classify_by_title(announcement)

                if title_class == 'rejected':
                    _, exclude_reason = should_exclude_by_keywords(announcement)
                    print(f"   [{idx}/{len(report_data)}] 🚫 [키워드필터] {title[:30]}... ({exclude_reason})")
                    announcement.update({
                        'reviewed': True,
                        'review_method': 'keyword_filter',
                        'rejection_reason': 'keyword_filter',
                        'review_result': json.dumps({
                            'decision': '부적합',
                            'confidence': 100,
                            'reason': exclude_reason,
                            'key_evidence': exclude_reason,
                        }, ensure_ascii=False),
                        'review_model': 'keyword-filter',
                        'reviewed_at': datetime.now().isoformat(),
                        'status': STATUS_REJECTED,
                    })
                    rejected_count += 1
                    reviewed_count += 1
                    continue

                elif title_class == 'approved':
                    matched_keyword = next(
                        (p['keyword'] for p in FAST_APPROVE_PATTERNS if p['keyword'] in title),
                        title[:20]
                    )
                    print(f"   [{idx}/{len(report_data)}] ✅ [제목확정] {title[:30]}...")
                    announcement.update({
                        'reviewed': True,
                        'review_method': 'title_approved',
                        'review_result': json.dumps({
                            'decision': '적합',
                            'confidence': 95,
                            'reason': f'제목에 명확한 EAP 키워드 포함: {matched_keyword}',
                            'key_evidence': matched_keyword,
                        }, ensure_ascii=False),
                        'review_model': 'title-filter',
                        'reviewed_at': datetime.now().isoformat(),
                        'status': STATUS_APPROVED,
                    })
                    approved_count += 1
                    reviewed_count += 1
                    continue

                # ── 2단계: GPT 심층 검수 (첨부파일 다운로드 생략) ─────────────────────
                print(f"   [{idx}/{len(report_data)}] 🔍 [GPT검수] {title[:30]}...")

                # 첨부파일 다운로드 비활성화 (CI 환경에서 타임아웃 발생으로 제외)
                attachment_text, attach_method = '', 'attachment_skipped'

                review_result = review_announcement_with_chatgpt(announcement, attachment_text)

                # 결과 반영
                review_method = attach_method if not review_result.get('error') else 'attachment_failed'
                announcement.update({
                    'reviewed': True,
                    'review_result': review_result.get('result', ''),
                    'review_model': review_result.get('model', OPENAI_MODEL_REVIEW),
                    'reviewed_at': datetime.now().isoformat(),
                    'review_method': review_method,
                })

                if review_result.get('approved') is True:
                    announcement['status'] = STATUS_APPROVED
                    status_icon = '✅'
                    approved_count += 1
                else:
                    announcement['status'] = STATUS_REJECTED
                    announcement['rejection_reason'] = review_result.get('rejection_reason', 'gpt_decision')
                    status_icon = '❌'
                    rejected_count += 1

                reviewed_count += 1
                attach_icon = '📎' if attach_method == 'with_attachment' else '📄'
                print(f"      {status_icon} {attach_icon} {announcement_number[:25]}...")

            except Exception as e:
                print(f"   [{idx}/{len(report_data)}] ❌ 검수 실패: {str(e)}")
                error_count += 1
                announcement.update({
                    'reviewed': True,
                    'review_result': json.dumps({
                        'decision': '불명확',
                        'confidence': 0,
                        'reason': f'검수 중 오류 발생: {str(e)}',
                        'key_evidence': '',
                    }, ensure_ascii=False),
                    'review_method': 'error',
                    'rejection_reason': 'api_error',
                    'status': STATUS_REJECTED,
                })
                rejected_count += 1
                reviewed_count += 1
                continue
        
        # 검수된 리포트 파일 저장
        print("\n3. 검수된 리포트 파일 저장 중...")
        date_str = get_date_string(report_date)
        filename = f'report_{date_str}.json'
        filepath = REPORT_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ 리포트 파일 저장 완료: {filepath}")
        
        # 결과 출력
        print("\n" + "=" * 60)
        print("검수 완료!")
        print("=" * 60)
        print(f"전체 공고: {len(report_data)}개")
        print(f"검수 완료: {reviewed_count}개")
        print(f"  ✅ 적합: {approved_count}개")
        print(f"  ❌ 부적합: {rejected_count}개")
        if error_count > 0:
            print(f"  ⚠️  오류: {error_count}개")

        return {
            'success': True,
            'reviewed_count': reviewed_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'pending_count': pending_count,
            'error_count': error_count,
            'report_path': str(filepath)
        }
        
    except Exception as e:
        error_msg = f"검수 중 오류 발생: {str(e)}"
        print(f"\n❌ {error_msg}")
        import traceback
        print(traceback.format_exc())
        return {
            'success': False,
            'error': error_msg,
            'reviewed_count': 0,
            'approved_count': 0,
            'rejected_count': 0
        }

def review_announcement_with_chatgpt(
    announcement: Dict,
    attachment_text: str = '',
) -> Dict:
    """
    ChatGPT API를 사용하여 개별 공고 검수 (JSON 응답 구조화)

    Args:
        announcement: 공고 데이터 딕셔너리
        attachment_text: 첨부파일에서 추출한 텍스트 (없으면 빈 문자열)

    Returns:
        {
            'approved': True | False | None,  # None = pending
            'result': str,                    # GPT 원본 JSON 응답
            'model': str,
            'rejection_reason': str,          # 부적합/pending 사유 코드
            'key_evidence': str,              # GPT가 근거로 든 원문 구절
            'error': str,                     # 오류 메시지 (있을 경우)
        }
    """
    try:
        client = get_openai_client()

        title = announcement.get('title', '')
        agency = announcement.get('agency', '')
        business_type = announcement.get('business_type', '')
        budget_amount = announcement.get('budget_amount')
        estimated_price = announcement.get('estimated_price')
        publish_date = announcement.get('publish_date', '')

        # 예산 정보 포맷팅
        budget_info = ""
        if budget_amount:
            budget_info += f"배정예산: {format_currency(budget_amount)}원"
        if estimated_price:
            if budget_info:
                budget_info += f"\n추정가격: {format_currency(estimated_price)}원"
            else:
                budget_info = f"추정가격: {format_currency(estimated_price)}원"

        # EAP 검수 프롬프트 로드 후 공고 정보 삽입
        base_prompt = load_eap_review_prompt()
        prompt = base_prompt.format(
            title=title,
            agency=agency,
            business_type=business_type,
            publish_date=publish_date,
            budget_info=budget_info if budget_info else "예산 정보 없음",
            announcement_number=announcement.get('announcement_number', ''),
            attachment_text=attachment_text if attachment_text else '첨부파일 없음 (제목·기관·예산 정보만으로 판단)',
        )

        response = client.chat.completions.create(
            model=OPENAI_MODEL_REVIEW,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 근로자지원프로그램(EAP) 전문가입니다. "
                        "공고가 EAP의 핵심 요소(심리 상담, 코칭, 근로자 지원 서비스 등)와 관련이 있는지 판단합니다. "
                        "반드시 JSON 형식으로만 응답하세요."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=OPENAI_MAX_TOKENS_REVIEW,
            temperature=OPENAI_TEMPERATURE_REVIEW,
        )

        result_text = response.choices[0].message.content

        # JSON 파싱
        try:
            parsed = json.loads(result_text)
        except json.JSONDecodeError:
            print(f"      ⚠️  GPT JSON 파싱 실패: {result_text[:100]}")
            return {
                'approved': False,
                'result': result_text,
                'model': OPENAI_MODEL_REVIEW,
                'rejection_reason': 'parse_error',
                'key_evidence': '',
                'error': 'GPT 응답 JSON 파싱 실패',
            }

        decision = parsed.get('decision', '')
        confidence = int(parsed.get('confidence', 0))
        key_evidence = parsed.get('key_evidence', '')

        # 결정 로직: confidence < 70 또는 '불명확' → 부적합 처리
        if decision == '적합' and confidence >= 70:
            approved = True
            rejection_reason = None
        else:
            # 부적합, 신뢰도 미달, 불명확 응답 모두 부적합으로 처리
            approved = False
            if confidence < 70:
                rejection_reason = 'low_confidence'
            elif decision == '부적합':
                rejection_reason = 'gpt_decision'
            else:
                rejection_reason = 'gpt_uncertain'

        return {
            'approved': approved,
            'result': result_text,
            'model': OPENAI_MODEL_REVIEW,
            'rejection_reason': rejection_reason,
            'key_evidence': key_evidence,
        }

    except Exception as e:
        print(f"      ❌ ChatGPT 검수 중 오류: {str(e)}")
        return {
            'approved': False,
            'result': json.dumps({
                'decision': '부적합',
                'confidence': 0,
                'reason': f'API 오류: {str(e)}',
                'key_evidence': '',
            }, ensure_ascii=False),
            'model': OPENAI_MODEL_REVIEW,
            'rejection_reason': 'api_error',
            'key_evidence': '',
            'error': str(e),
        }

def format_currency(amount: int) -> str:
    """
    금액을 읽기 쉬운 형식으로 포맷팅
    
    Args:
        amount: 금액 (원 단위)
    
    Returns:
        포맷팅된 문자열 (예: "1억 5천만원")
    """
    if amount is None:
        return "0원"
    
    if amount < 10000:
        return f"{amount:,}원"
    
    result = []
    
    # 억 단위
    eok = amount // 100000000
    if eok > 0:
        result.append(f"{eok}억")
        amount = amount % 100000000
    
    # 천만 단위
    cheonman = amount // 10000000
    if cheonman > 0:
        result.append(f"{cheonman}천만")
        amount = amount % 10000000
    
    # 만 단위
    man = amount // 10000
    if man > 0:
        result.append(f"{man}만")
        amount = amount % 10000
    
    # 원 단위
    if amount > 0:
        result.append(f"{amount:,}")
    
    return " ".join(result) + "원"


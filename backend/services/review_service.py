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
# review_filter 모듈로 이전됨 — 하위 호환성을 위해 re-export
from services.review_filter import (
    EXCLUSION_KEYWORDS,
    FAST_APPROVE_PATTERNS,
    should_exclude_by_keywords,
    classify_by_title,
)
from utils.formatters import format_currency
from utils.logger import StepLogger

_logger = StepLogger("ReviewService")

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

# 검수용 첨부파일 텍스트 제한
ATTACHMENT_MAX_CHARS_PER_FILE = 2000   # 파일 1개당 최대 문자 수
ATTACHMENT_MAX_TOTAL_CHARS = 4000      # GPT에 전달할 전체 최대 문자 수

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


def _make_review_result(decision: str, confidence: int, reason: str, key_evidence: str = '') -> str:
    """review_result JSON 문자열 생성 헬퍼"""
    return json.dumps({
        'decision': decision,
        'confidence': confidence,
        'reason': reason,
        'key_evidence': key_evidence,
    }, ensure_ascii=False)


def _process_single_announcement(
    announcement: Dict,
    idx: int,
    total: int,
    cached_prompt: str,
) -> str:
    """
    공고 1개 검수 처리 (review_report_file 루프 body 추출).

    Returns:
        STATUS_APPROVED | STATUS_REJECTED
    """
    announcement_number = announcement.get('announcement_number', '')
    title = announcement.get('title', '')

    # 이미 검수된 공고 건너뛰기 (단, API 오류로 실패한 경우 재검수)
    if (announcement.get('reviewed') and announcement.get('review_result') and announcement.get('status')
            and announcement.get('rejection_reason') != 'api_error'):
        print(f"   [{idx}/{total}] 이미 검수됨: {announcement_number}")
        return announcement.get('status', STATUS_REJECTED)

    # ── 1단계: 제목 기반 빠른 분류 ──────────────────────────────
    title_class = classify_by_title(announcement)

    if title_class == 'rejected':
        _, exclude_reason = should_exclude_by_keywords(announcement)
        print(f"   [{idx}/{total}] 🚫 [키워드필터] {title[:30]}... ({exclude_reason})")
        announcement.update({
            'reviewed': True,
            'review_method': 'keyword_filter',
            'rejection_reason': 'keyword_filter',
            'review_result': _make_review_result('부적합', 100, exclude_reason, exclude_reason),
            'review_model': 'keyword-filter',
            'reviewed_at': datetime.now().isoformat(),
            'status': STATUS_REJECTED,
        })
        return STATUS_REJECTED

    if title_class == 'approved':
        matched_keyword = next(
            (p['keyword'] for p in FAST_APPROVE_PATTERNS if p['keyword'] in title),
            title[:20]
        )
        print(f"   [{idx}/{total}] ✅ [제목확정] {title[:30]}...")
        announcement.update({
            'reviewed': True,
            'review_method': 'title_approved',
            'review_result': _make_review_result(
                '적합', 95, f'제목에 명확한 EAP 키워드 포함: {matched_keyword}', matched_keyword
            ),
            'review_model': 'title-filter',
            'reviewed_at': datetime.now().isoformat(),
            'status': STATUS_APPROVED,
        })
        return STATUS_APPROVED

    # ── 2단계: GPT 심층 검수 ─────────────────────────────────────
    print(f"   [{idx}/{total}] 🔍 [GPT검수] {title[:30]}...")
    # 첨부파일 다운로드 비활성화 (CI 환경에서 타임아웃 발생으로 제외)
    review_result = review_announcement_with_chatgpt(announcement, '', base_prompt=cached_prompt)

    announcement.update({
        'reviewed': True,
        'review_result': review_result.get('result', ''),
        'review_model': review_result.get('model', OPENAI_MODEL_REVIEW),
        'reviewed_at': datetime.now().isoformat(),
        'review_method': 'attachment_skipped',
    })

    if review_result.get('approved') is True:
        announcement['status'] = STATUS_APPROVED
        print(f"      ✅ 📄 {announcement_number[:25]}...")
        return STATUS_APPROVED
    elif review_result.get('approved') is None:
        announcement['status'] = STATUS_PENDING
        announcement['rejection_reason'] = review_result.get('rejection_reason', 'gpt_uncertain')
        print(f"      ⏳ 📄 {announcement_number[:25]}... (수동 검토 필요)")
        return STATUS_PENDING
    else:
        announcement['status'] = STATUS_REJECTED
        announcement['rejection_reason'] = review_result.get('rejection_reason', 'gpt_decision')
        print(f"      ❌ 📄 {announcement_number[:25]}...")
        return STATUS_REJECTED


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
    
    _logger.start()
    _logger.info(f"날짜: {report_date.strftime('%Y-%m-%d')}")
    
    # OpenAI API 키 확인
    try:
        get_openai_client()
    except ValueError as e:
        error_msg = str(e)
        _logger.warning(error_msg)
        return {
            'success': False,
            'error': error_msg,
            'reviewed_count': 0,
            'approved_count': 0,
            'rejected_count': 0
        }
    
    try:
        # 리포트 파일 로드
        _logger.section("1. 리포트 파일 로드 중...")
        report_data = load_report(report_date)

        if not report_data:
            _logger.warning("검수할 데이터가 없습니다.")
            return {
                'success': False,
                'error': '검수할 데이터가 없습니다.',
                'reviewed_count': 0,
                'approved_count': 0,
                'rejected_count': 0
            }

        _logger.success(f"리포트 파일 로드 완료: {len(report_data)}개 공고")
        
        # 사용자 컨펌 확인
        if confirm_before_review:
            _logger.warning("ChatGPT API 사용 시 비용이 발생합니다.")
            _logger.info(f"검수할 공고 수: {len(report_data)}개")
            _logger.info(f"예상 비용: 약 ${len(report_data) * 0.002:.2f} (gpt-3.5-turbo 기준)")
            if not request_confirmation("검수를 진행하시겠습니까? (yes/no): "):
                _logger.warning("검수가 취소되었습니다.")
                return {
                    'success': False,
                    'error': '사용자가 검수를 취소했습니다.',
                    'reviewed_count': 0,
                    'approved_count': 0,
                    'rejected_count': 0
                }
        
        # EAP 검수 프롬프트 1회 로드 (루프 안에서 반복 Firestore 조회 방지)
        _logger.section("1.5. EAP 검수 프롬프트 로드 중...")
        cached_prompt = load_eap_review_prompt()
        _logger.success(f"프롬프트 로드 완료 ({len(cached_prompt)}자)")

        # 각 공고 검수 (2단계 파이프라인)
        _logger.section("2. 공고 검수 중 (1단계: 키워드 필터 → 2단계: GPT 검수)...")
        reviewed_count = 0
        approved_count = 0
        rejected_count = 0
        error_count = 0

        for idx, announcement in enumerate(report_data, 1):
            try:
                status = _process_single_announcement(announcement, idx, len(report_data), cached_prompt)
                reviewed_count += 1
                if status == STATUS_APPROVED:
                    approved_count += 1
                else:
                    rejected_count += 1
            except Exception as e:
                _logger.error(f"[{idx}/{len(report_data)}] 검수 실패: {str(e)}")
                error_count += 1
                announcement.update({
                    'reviewed': True,
                    'review_result': _make_review_result('불명확', 0, f'검수 중 오류 발생: {str(e)}'),
                    'review_method': 'error',
                    'rejection_reason': 'api_error',
                    'status': STATUS_REJECTED,
                })
                rejected_count += 1
                reviewed_count += 1
        
        # 검수된 리포트 파일 저장
        _logger.section("3. 검수된 리포트 파일 저장 중...")
        date_str = get_date_string(report_date)
        filename = f'report_{date_str}.json'
        filepath = REPORT_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        _logger.success(f"리포트 파일 저장 완료: {filepath}")

        # 결과 출력
        _logger.start()
        _logger.info(f"전체 공고: {len(report_data)}개")
        _logger.info(f"검수 완료: {reviewed_count}개")
        _logger.success(f"적합: {approved_count}개")
        _logger.error(f"부적합: {rejected_count}개")
        if error_count > 0:
            _logger.warning(f"오류: {error_count}개")

        return {
            'success': True,
            'reviewed_count': reviewed_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'error_count': error_count,
            'report_path': str(filepath)
        }
        
    except Exception as e:
        import traceback
        error_msg = f"검수 중 오류 발생: {str(e)}"
        _logger.error(error_msg)
        _logger.error(traceback.format_exc())
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
    base_prompt: str = '',
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

        # EAP 검수 프롬프트 로드 (외부에서 전달된 경우 재사용, 없으면 Firestore에서 로드)
        if not base_prompt:
            base_prompt = load_eap_review_prompt()
        prompt = base_prompt
        prompt = prompt.replace('{title}', title)
        prompt = prompt.replace('{agency}', agency)
        prompt = prompt.replace('{business_type}', business_type)
        prompt = prompt.replace('{publish_date}', publish_date)
        prompt = prompt.replace('{budget_info}', budget_info if budget_info else "예산 정보 없음")
        prompt = prompt.replace('{announcement_number}', announcement.get('announcement_number', ''))
        prompt = prompt.replace('{attachment_text}', attachment_text if attachment_text else '첨부파일 없음 (제목·기관·예산 정보만으로 판단)')

        response = client.chat.completions.create(
            model=OPENAI_MODEL_REVIEW,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 근로자지원프로그램(EAP) 전문가입니다. "
                        "공고가 EAP의 핵심 요소(심리 상담, 코칭, 근로자 지원 서비스 등)와 관련이 있는지 판단합니다. "
                        "반드시 다음 JSON 형식으로만 응답하세요 (다른 텍스트 절대 금지): "
                        '{"decision": "적합" 또는 "부적합" 또는 "불명확", '
                        '"confidence": 0~100 사이 정수, '
                        '"reason": "판단 근거 2-3문장", '
                        '"key_evidence": "결정적 원문 구절 (없으면 빈 문자열)"}'
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
            _logger.warning(f"GPT JSON 파싱 실패: {result_text[:100]}")
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

        # 결정 로직
        if decision == '적합' and confidence >= 70:
            approved = True
            rejection_reason = None
        elif decision == '불명확':
            # 불명확 → pending (수동 검토 대기)
            approved = False
            rejection_reason = 'gpt_uncertain'
        else:
            approved = False
            if confidence < 70:
                rejection_reason = 'low_confidence'
            else:
                rejection_reason = 'gpt_decision'

        return {
            'approved': approved,
            'result': result_text,
            'model': OPENAI_MODEL_REVIEW,
            'rejection_reason': rejection_reason,
            'key_evidence': key_evidence,
        }

    except Exception as e:
        _logger.error(f"ChatGPT 검수 중 오류: {str(e)}")
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



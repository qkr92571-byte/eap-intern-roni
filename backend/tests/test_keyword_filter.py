"""
EXCLUSION_KEYWORDS / FAST_APPROVE_PATTERNS 단위 테스트
- mock 없이 실행 가능
- 실제 데이터 기반 케이스
"""
import pytest
from services.review_service import (
    EXCLUSION_KEYWORDS,
    FAST_APPROVE_PATTERNS,
    should_exclude_by_keywords,
    classify_by_title,
)


class TestExclusionKeywords:
    """should_exclude_by_keywords: 제외 키워드 자동 부적합 판단"""

    @pytest.mark.parametrize("title,expected_keyword", [
        ("2026년 취업상담 클리닉 운영 용역", "취업상담"),
        ("종합소득세 홈택스 임시상담 위탁운영", "소득세"),
        ("K-Food+ 바이어 초청 수출상담회 운영", "수출상담"),
        ("고객 콜센터 운영 및 관리 용역", "콜센터"),
        ("노후준비상담사(CSA) 자격시험 운영 용역", "자격시험"),
        ("통근버스 위탁 운영 용역", "통근버스"),
        ("취업성공패키지 위탁 운영", "취업성공"),
        ("취약계층 주거상담 및 지원 사업", "주거상담"),
        ("직업상담사 파견 위탁 운영", "직업상담"),
        ("진로상담 프로그램 운영 용역", "진로상담"),
    ])
    def test_제외키워드_부적합_처리(self, title, expected_keyword):
        announcement = {'title': title}
        excluded, reason = should_exclude_by_keywords(announcement)
        assert excluded is True, f"'{title}'은 부적합이어야 함"
        assert expected_keyword in reason

    @pytest.mark.parametrize("title", [
        "소방공무원 찾아가는 상담실 운영 용역",
        "2026년 근로자지원프로그램(EAP) 위탁 운영 용역",
        "청년 마음이음 사업 전문심리상담(일대일, 집단) 용역",
        "대중문화예술인 심리상담 위탁용역",
        "펫로스 심리지원 시범사업",
        "학생정서행동특성검사 상담기관 위탁운영",
        "소방공무원 마음건강 설문조사 통계 및 분석",
    ])
    def test_적합공고_제외안됨(self, title):
        announcement = {'title': title}
        excluded, _ = should_exclude_by_keywords(announcement)
        assert excluded is False, f"'{title}'은 제외되면 안 됨"


class TestClassifyByTitle:
    """classify_by_title: 1단계 제목 기반 분류 전체 흐름"""

    @pytest.mark.parametrize("title", [
        "소방공무원 찾아가는 상담실 운영 용역",
        "근로자지원프로그램(EAP) 운영 용역",
        "EAP 운영 위탁 용역",
        "청년 마음이음 전문심리상담 용역",
        "심리상담 위탁 운영 용역",
        "2026년 학생정서행동특성검사 기관 위탁운영",
        "소방공무원 마음건강 설문조사",
        "전문상담사 파견 운영",
    ])
    def test_명확_적합_공고_approved(self, title):
        result = classify_by_title({'title': title})
        assert result == 'approved', f"'{title}'은 approved여야 함"

    @pytest.mark.parametrize("title", [
        "찾아가는 상담실 시스템 개발 구축",
        "EAP 운영 플랫폼 개발 용역",
        "심리상담 운영 시스템 구축 사업",
    ])
    def test_예외키워드_있으면_approved_아님(self, title):
        """'개발', '구축', '시스템' 포함 시 fast_approve 불가"""
        result = classify_by_title({'title': title})
        assert result != 'approved', f"'{title}'은 approved면 안 됨 (예외키워드 포함)"

    @pytest.mark.parametrize("title", [
        "2026년 취업상담 클리닉 운영 용역",
        "종합소득세 홈택스 임시상담 위탁운영",
        "관광통역안내 상담시스템 유지보수",
    ])
    def test_제외키워드_공고_rejected(self, title):
        result = classify_by_title({'title': title})
        assert result == 'rejected', f"'{title}'은 rejected여야 함"

    @pytest.mark.parametrize("title", [
        "직원 복리후생 프로그램 운영",
        "청년 일자리 지원 사업 위탁 운영",
    ])
    def test_판단불가_공고_uncertain(self, title):
        """제외 키워드도 없고 명확 EAP 키워드도 없으면 uncertain"""
        result = classify_by_title({'title': title})
        assert result == 'uncertain', f"'{title}'은 uncertain이어야 함"

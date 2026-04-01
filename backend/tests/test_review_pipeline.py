"""
review_report_file 통합 테스트
- fixture 리포트 파일 사용 (실제 파일 I/O 없음)
- OpenAI mock으로 CI 실행 가능
- 1단계 필터(keyword/fast_approve) + 2단계 GPT 결합 검증
"""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock


FIXTURE_REPORT = Path(__file__).parent / 'fixtures' / 'sample_report.json'


@pytest.fixture
def sample_announcements():
    with open(FIXTURE_REPORT, encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def mock_gpt_적합(mocker):
    """GPT → 항상 '적합' 응답 반환"""
    content = json.dumps({
        "decision": "적합",
        "confidence": 88,
        "reason": "심리상담 서비스",
        "key_evidence": "심리상담",
    })
    mock_response = MagicMock()
    mock_response.choices[0].message.content = content
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    mocker.patch('services.review_service.get_openai_client', return_value=mock_client)


class TestReviewPipeline:

    def test_취업상담_키워드필터_rejected(self, sample_announcements):
        """1단계: 제외 키워드로 즉시 rejected"""
        from services.review_service import classify_by_title
        공고 = next(a for a in sample_announcements if '취업상담' in a['title'])
        assert classify_by_title(공고) == 'rejected'

    def test_찾아가는상담실_fast_approved(self, sample_announcements):
        """1단계: 명확 EAP 키워드로 즉시 approved"""
        from services.review_service import classify_by_title
        공고 = next(a for a in sample_announcements if '찾아가는 상담실' in a['title'])
        assert classify_by_title(공고) == 'approved'

    def test_전문심리상담_fast_approved(self, sample_announcements):
        """1단계: 전문심리상담 패턴으로 approved"""
        from services.review_service import classify_by_title
        공고 = next(a for a in sample_announcements if '전문심리상담' in a['title'])
        assert classify_by_title(공고) == 'approved'

    def test_복리후생_uncertain(self, sample_announcements):
        """1단계 판단 불가 → GPT로 넘어가야 함"""
        from services.review_service import classify_by_title
        공고 = next(a for a in sample_announcements if '복리후생' in a['title'])
        assert classify_by_title(공고) == 'uncertain'

    def test_파이프라인_결과_카운트(self, sample_announcements, mock_gpt_적합, mocker, tmp_path):
        """
        전체 파이프라인 실행 시 결과 카운트 검증
        fixture 4개 공고 기준:
        - 찾아가는 상담실 → title_approved (approved)
        - 전문심리상담     → title_approved (approved)
        - 취업상담         → keyword_filter (rejected)
        - 복리후생         → GPT 호출 → mock_gpt_적합 (approved)
        """
        from services.review_service import review_report_file
        from datetime import datetime

        # 파일 I/O를 mock으로 대체
        mocker.patch('services.review_service.load_report', return_value=sample_announcements)
        mocker.patch('services.review_service.REPORT_DIR', tmp_path)
        mocker.patch('services.review_service.get_date_string', return_value='260331')

        result = review_report_file(
            report_date=datetime(2026, 3, 31),
            confirm_before_review=False,
        )

        assert result['success'] is True
        assert result['reviewed_count'] == 4
        assert result['approved_count'] == 3  # 찾아가는상담실 + 전문심리상담 + 복리후생(GPT)
        assert result['rejected_count'] == 1  # 취업상담

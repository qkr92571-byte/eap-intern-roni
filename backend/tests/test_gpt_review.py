"""
review_announcement_with_chatgpt 단위 테스트
- OpenAI API는 mock으로 대체
- JSON 파싱 로직, confidence 판단, 거절 사유 코드 검증
"""
import json
import pytest
from services.review_service import review_announcement_with_chatgpt


SAMPLE_ANNOUNCEMENT = {
    'announcement_number': 'R26BK01313635-000',
    'title': '청년 마음이음 전문심리상담 용역',
    'agency': '서울특별시',
    'business_type': '용역비',
    'publish_date': '2026-03-31',
    'budget_amount': 150_000_000,
    'estimated_price': 145_000_000,
}


_TEST_PROMPT = (
    "공고명: {title}\n발주기관: {agency}\n업무구분: {business_type}\n"
    "게시일: {publish_date}\n예산: {budget_info}\n공고번호: {announcement_number}\n"
    "첨부파일:\n{attachment_text}"
)


def _make_mock_openai(mocker, decision: str, confidence: int, reason: str = "테스트", key_evidence: str = ""):
    """OpenAI 클라이언트와 프롬프트 로더를 mock으로 대체하는 헬퍼"""
    content = json.dumps({
        "decision": decision,
        "confidence": confidence,
        "reason": reason,
        "key_evidence": key_evidence,
    }, ensure_ascii=False)
    mock_response = mocker.MagicMock()
    mock_response.choices[0].message.content = content
    mock_client = mocker.MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    mocker.patch('services.review_service.get_openai_client', return_value=mock_client)
    # 프롬프트 파일의 raw '{' 문자가 str.format() 오류를 일으키지 않도록 mock 처리
    mocker.patch('services.review_service.load_eap_review_prompt', return_value=_TEST_PROMPT)
    return mock_client


class TestGptReviewApproval:

    def test_적합_confidence70이상_approved(self, mocker):
        _make_mock_openai(mocker, "적합", 92, key_evidence="전문심리상담 용역")
        result = review_announcement_with_chatgpt(SAMPLE_ANNOUNCEMENT)
        assert result['approved'] is True
        assert result['rejection_reason'] is None

    def test_적합_confidence70미만_rejected(self, mocker):
        _make_mock_openai(mocker, "적합", 65)
        result = review_announcement_with_chatgpt(SAMPLE_ANNOUNCEMENT)
        assert result['approved'] is False
        assert result['rejection_reason'] == 'low_confidence'

    def test_부적합_rejected(self, mocker):
        _make_mock_openai(mocker, "부적합", 95, key_evidence="취업상담 클리닉")
        result = review_announcement_with_chatgpt(SAMPLE_ANNOUNCEMENT)
        assert result['approved'] is False
        assert result['rejection_reason'] == 'gpt_decision'

    def test_불명확_confidence높아도_rejected(self, mocker):
        """confidence >= 70 이어도 '불명확' 결정이면 gpt_uncertain으로 거절"""
        _make_mock_openai(mocker, "불명확", 80)
        result = review_announcement_with_chatgpt(SAMPLE_ANNOUNCEMENT)
        assert result['approved'] is False
        assert result['rejection_reason'] == 'gpt_uncertain'


class TestGptReviewEdgeCases:

    def test_json_파싱실패_parse_error(self, mocker):
        """GPT가 JSON 아닌 텍스트 반환 시 parse_error 처리"""
        mock_response = mocker.MagicMock()
        mock_response.choices[0].message.content = "죄송합니다, 판단이 어렵습니다."
        mock_client = mocker.MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mocker.patch('services.review_service.get_openai_client', return_value=mock_client)
        mocker.patch('services.review_service.load_eap_review_prompt', return_value=_TEST_PROMPT)

        result = review_announcement_with_chatgpt(SAMPLE_ANNOUNCEMENT)
        assert result['approved'] is False
        assert result['rejection_reason'] == 'parse_error'
        assert 'error' in result

    def test_key_evidence_반환됨(self, mocker):
        _make_mock_openai(mocker, "적합", 88, key_evidence="전문상담사 파견하여 심리상담 제공")
        result = review_announcement_with_chatgpt(SAMPLE_ANNOUNCEMENT)
        assert result['key_evidence'] == "전문상담사 파견하여 심리상담 제공"

    def test_빈_attachment_text_처리됨(self, mocker):
        """첨부파일 없을 때도 정상 실행"""
        _make_mock_openai(mocker, "적합", 75)
        result = review_announcement_with_chatgpt(SAMPLE_ANNOUNCEMENT, attachment_text='')
        assert 'approved' in result

    def test_api_오류_api_error(self, mocker):
        """OpenAI API 호출 실패 시 에러 처리"""
        mock_client = mocker.MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API timeout")
        mocker.patch('services.review_service.get_openai_client', return_value=mock_client)

        result = review_announcement_with_chatgpt(SAMPLE_ANNOUNCEMENT)
        assert result['approved'] is False
        assert 'error' in result

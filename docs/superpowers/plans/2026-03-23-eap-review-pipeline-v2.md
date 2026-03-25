# EAP 검수 파이프라인 v2 구현 플랜

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 나라장터 공고 GPT 검수를 "제목 키워드 필터 → 첨부파일 기반 GPT 심층 검수" 2단계 파이프라인으로 전환하고, JSON 구조화 응답·Audit Trail·downstream 서비스 호환성까지 완전히 통합한다.

**Architecture:** 1단계(키워드 필터/제목 확정)에서 결론이 나면 GPT를 호출하지 않는다. 불명확한 공고만 2단계에서 첨부파일(PDF/HWP/HWPX/DOCX)을 다운로드한 뒤 내용을 포함한 프롬프트로 GPT 검수를 수행한다. GPT 응답은 JSON(`decision`, `confidence`, `reason`, `key_evidence`)으로 강제 구조화하고, `confidence < 70`이면 `pending` 처리한다. Audit Trail 필드(`review_method`, `rejection_reason`)가 Firestore에도 저장된다.

**Tech Stack:** Python 3.11, Flask, OpenAI gpt-4o-mini (JSON mode), pyhwp + olefile (HWP), zipfile+xml.etree (HWPX), pdfplumber, python-docx

---

## 이미 완료된 작업 (컨텍스트용)

아래 변경은 이 플랜 작성 전에 이미 구현되었습니다. 재작업 불필요.

| 파일 | 변경 내용 |
|------|-----------|
| `backend/services/review_service.py` | 2단계 파이프라인, `classify_by_title()`, `fetch_attachment_text_for_review()`, JSON GPT 응답, `pending_count`, Audit Trail 필드 |
| `backend/services/attachment_service.py` | HWPX 지원(`_extract_text_from_hwpx`), HWP fallback 체인(`_extract_text_from_hwp`), `_clean_hwp_text()` |
| `backend/prompts/eap_review_prompt.txt` | `{attachment_text}` 섹션 추가, JSON 응답 형식으로 전면 교체 |
| `backend/utils/constants.py` | `OPENAI_MODEL_REVIEW = 'gpt-4o-mini'`, `OPENAI_MAX_TOKENS_REVIEW = 800` |
| `backend/requirements.txt` | `olefile>=0.47`, `pypdf>=3.0.0`, `python-docx>=1.1.0` 추가 |

---

## 파일 변경 맵 (남은 작업)

| 파일 | 변경 유형 | 내용 |
|------|-----------|------|
| `backend/scripts/review_and_upsert_firestore.py` | Modify | `_prepare_firestore_data()`에 `review_method`, `rejection_reason` 필드 추가 및 완료 통계에 `pending_count` 표시 |
| `backend/services/slack_service.py` | Modify | `pending_count` 집계 로직을 `status == 'pending'` 기준으로 수정, Slack 메시지에 미결 건수 표시 |
| `backend/tests/test_review_pipeline.py` | Create | 파이프라인 단위 테스트 |
| `backend/tests/test_attachment_extraction.py` | Create | HWP/HWPX/PDF 텍스트 추출 단위 테스트 |

---

## Task 1: 새 의존성 설치 확인

**Files:**
- Read: `backend/requirements.txt`

- [ ] **Step 1: 의존성 설치**

```bash
cd backend
pip install olefile python-docx pypdf
```

Expected: 3개 패키지 설치 (이미 있으면 "already satisfied")

- [ ] **Step 2: import 검증**

```bash
python3 -c "import olefile; import docx; import pypdf; print('✅ 의존성 OK')"
```

Expected: `✅ 의존성 OK`

---

## Task 2: review_and_upsert_firestore.py — 신규 필드 반영

**Files:**
- Modify: `backend/scripts/review_and_upsert_firestore.py:33-56`

신규 필드(`review_method`, `rejection_reason`)를 Firestore에도 저장하고, 완료 로그에 `pending_count`를 표시해야 한다.

- [ ] **Step 1: `_prepare_firestore_data()`에 신규 필드 추가**

`backend/scripts/review_and_upsert_firestore.py`의 `firestore_data` 딕셔너리에 아래 두 줄 추가:

```python
"review_method": announcement.get("review_method", ""),
"rejection_reason": announcement.get("rejection_reason"),
```

(`rejected_count` 아래 줄, `service_items` 위에 위치)

- [ ] **Step 2: 완료 통계 로그에 pending_count 추가**

```python
# 기존
print(f"[검수] 검수 {review_result.get('reviewed_count', 0)}개 / 적합 {review_result.get('approved_count', 0)}개 / 부적합 {review_result.get('rejected_count', 0)}개")

# 변경 후
print(
    f"[검수] 검수 {review_result.get('reviewed_count', 0)}개"
    f" / 적합 {review_result.get('approved_count', 0)}개"
    f" / 부적합 {review_result.get('rejected_count', 0)}개"
    f" / 미결 {review_result.get('pending_count', 0)}개"
)
```

- [ ] **Step 3: 변경 확인**

```bash
cd backend
python3 -c "
from scripts.review_and_upsert_firestore import _prepare_firestore_data
data = _prepare_firestore_data({'announcement_number': 'TEST', 'review_method': 'with_attachment', 'rejection_reason': 'gpt_decision'})
assert 'review_method' in data
assert 'rejection_reason' in data
print('✅ _prepare_firestore_data 필드 확인 완료')
"
```

- [ ] **Step 4: 커밋**

```bash
git add backend/scripts/review_and_upsert_firestore.py
git commit -m "feat: Firestore upsert에 review_method, rejection_reason 필드 추가"
```

---

## Task 3: slack_service.py — pending_count 집계 로직 수정

**Files:**
- Modify: `backend/services/slack_service.py:143`

현재 `pending_count = sum(1 for a in announcements if not a.get('reviewed', False))` 는 새 파이프라인에서 `reviewed=True` + `status=pending`인 공고를 놓친다.

- [ ] **Step 1: pending_count 집계 기준 수정**

```python
# 기존 (reviewed=False인 것만 카운트)
pending_count = sum(1 for a in announcements if not a.get('reviewed', False))

# 변경 후 (status='pending'인 것을 카운트)
pending_count = sum(1 for a in announcements if a.get('status') == 'pending')
```

- [ ] **Step 2: Slack 통계 메시지에 pending 표시 추가**

`stats_text` 구성 부분을 찾아 아래처럼 수정:

```python
stats_text = f":clipboard: *신규 공고*\n총 {total_count}개"
if approved_count > 0 or rejected_count > 0 or pending_count > 0:
    stats_text += f"\n  • ✅ 적합: {approved_count}개"
    stats_text += f"\n  • ❌ 부적합: {rejected_count}개"
    if pending_count > 0:
        stats_text += f"\n  • ⏸️ 미결(검토 필요): {pending_count}개"
```

- [ ] **Step 3: 집계 로직 단위 검증**

```bash
python3 -c "
announcements = [
    {'status': 'approved', 'reviewed': True},
    {'status': 'rejected', 'reviewed': True},
    {'status': 'pending', 'reviewed': True},   # 새 케이스: reviewed지만 pending
    {'status': 'pending', 'reviewed': False},  # 기존 케이스
]
pending_count = sum(1 for a in announcements if a.get('status') == 'pending')
assert pending_count == 2, f'expected 2, got {pending_count}'
print('✅ pending_count 집계 로직 확인 완료')
"
```

- [ ] **Step 4: 커밋**

```bash
git add backend/services/slack_service.py
git commit -m "fix: Slack pending_count 집계 기준을 status=='pending'으로 변경"
```

---

## Task 4: 단위 테스트 — 파이프라인 핵심 로직

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_review_pipeline.py`

GPT/Firestore/Slack 의존성 없이 순수 로직만 테스트한다.

- [ ] **Step 1: tests 패키지 초기화**

```bash
mkdir -p backend/tests
touch backend/tests/__init__.py
```

- [ ] **Step 2: 테스트 파일 작성**

`backend/tests/test_review_pipeline.py`:

```python
"""
review_service.py 파이프라인 핵심 로직 단위 테스트
외부 의존성(OpenAI, Playwright) 없이 실행 가능
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.review_service import (
    classify_by_title,
    FAST_APPROVE_PATTERNS,
    EXCLUSION_KEYWORDS,
)


class TestClassifyByTitle:
    """classify_by_title() 함수 테스트"""

    def test_rejected_by_exclusion_keyword(self):
        assert classify_by_title({'title': '통근버스 운행 용역'}) == 'rejected'

    def test_rejected_콜센터(self):
        assert classify_by_title({'title': '고객 콜센터 운영 용역'}) == 'rejected'

    def test_approved_찾아가는_상담실(self):
        assert classify_by_title({'title': '소방공무원 찾아가는 상담실 운영 용역'}) == 'approved'

    def test_approved_EAP_운영(self):
        assert classify_by_title({'title': 'EAP 운영 지원 용역'}) == 'approved'

    def test_uncertain_when_exception_keyword_present(self):
        # '찾아가는 상담실'이지만 '시스템 개발'이 함께 있으면 uncertain
        assert classify_by_title({'title': '찾아가는 상담실 시스템 개발'}) == 'uncertain'

    def test_uncertain_ambiguous_title(self):
        assert classify_by_title({'title': '직원 심리상담 지원 프로그램'}) == 'uncertain'

    def test_uncertain_empty_title(self):
        assert classify_by_title({'title': ''}) == 'uncertain'


class TestGptResponseParsing:
    """GPT JSON 응답 파싱 로직 테스트"""

    def _parse(self, result_text: str) -> dict:
        """review_announcement_with_chatgpt 내부 파싱 로직 재현"""
        try:
            parsed = json.loads(result_text)
        except json.JSONDecodeError:
            return {'approved': None, 'rejection_reason': 'parse_error'}

        decision = parsed.get('decision', '')
        confidence = int(parsed.get('confidence', 0))

        if decision == '적합' and confidence >= 70:
            return {'approved': True, 'rejection_reason': None}
        elif decision == '부적합' and confidence >= 70:
            return {'approved': False, 'rejection_reason': 'gpt_decision'}
        else:
            reason = 'low_confidence' if confidence < 70 else 'gpt_uncertain'
            return {'approved': None, 'rejection_reason': reason}

    def test_approved_high_confidence(self):
        resp = json.dumps({'decision': '적합', 'confidence': 90, 'reason': 'x', 'key_evidence': 'y'})
        result = self._parse(resp)
        assert result['approved'] is True

    def test_rejected_high_confidence(self):
        resp = json.dumps({'decision': '부적합', 'confidence': 85, 'reason': 'x', 'key_evidence': ''})
        result = self._parse(resp)
        assert result['approved'] is False
        assert result['rejection_reason'] == 'gpt_decision'

    def test_pending_low_confidence(self):
        resp = json.dumps({'decision': '적합', 'confidence': 55, 'reason': 'x', 'key_evidence': ''})
        result = self._parse(resp)
        assert result['approved'] is None
        assert result['rejection_reason'] == 'low_confidence'

    def test_pending_uncertain_decision(self):
        resp = json.dumps({'decision': '불명확', 'confidence': 80, 'reason': 'x', 'key_evidence': ''})
        result = self._parse(resp)
        assert result['approved'] is None

    def test_pending_json_parse_error(self):
        result = self._parse("이것은 JSON이 아닙니다")
        assert result['approved'] is None
        assert result['rejection_reason'] == 'parse_error'


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
```

- [ ] **Step 3: 테스트 실행 및 통과 확인**

```bash
cd backend
python3 -m pytest tests/test_review_pipeline.py -v
```

Expected: 12 passed

- [ ] **Step 4: 커밋**

```bash
git add backend/tests/__init__.py backend/tests/test_review_pipeline.py
git commit -m "test: GPT 검수 파이프라인 핵심 로직 단위 테스트 추가"
```

---

## Task 5: 단위 테스트 — 텍스트 추출 로직

**Files:**
- Create: `backend/tests/test_attachment_extraction.py`
- Create: `backend/tests/fixtures/sample.hwpx` (스텁)

- [ ] **Step 1: 텍스트 추출 테스트 파일 작성**

`backend/tests/test_attachment_extraction.py`:

```python
"""
attachment_service.py 텍스트 추출 함수 단위 테스트
실제 파일 I/O가 필요한 테스트는 fixture 파일로 대체
"""
import sys, os, zipfile, io
from pathlib import Path
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.attachment_service import _clean_hwp_text, _extract_text_from_hwpx


class TestCleanHwpText:
    """_clean_hwp_text() 함수 테스트"""

    def test_removes_null_bytes(self):
        result = _clean_hwp_text("안녕\x00하세요")
        assert '\x00' not in result
        assert '안녕' in result

    def test_keeps_korean_and_alphanumeric(self):
        result = _clean_hwp_text("EAP 찾아가는 상담실 운영")
        assert 'EAP' in result
        assert '찾아가는' in result

    def test_collapses_multiple_spaces(self):
        result = _clean_hwp_text("텍스트   여러   공백")
        assert '   ' not in result

    def test_empty_string(self):
        assert _clean_hwp_text("") == ""


class TestExtractTextFromHwpx:
    """_extract_text_from_hwpx() 함수 테스트 (인메모리 ZIP 생성)"""

    def _make_hwpx(self, section_xml: str, tmp_path: Path) -> Path:
        """테스트용 HWPX 파일 생성 (ZIP + XML)"""
        hwpx_path = tmp_path / "test.hwpx"
        with zipfile.ZipFile(str(hwpx_path), 'w') as zf:
            zf.writestr("Contents/section0.xml", section_xml)
        return hwpx_path

    def test_extracts_text_from_xml(self, tmp_path):
        xml = '<root><p>찾아가는 상담실 운영</p><p>EAP 서비스 제공</p></root>'
        hwpx_path = self._make_hwpx(xml, tmp_path)
        status, text = _extract_text_from_hwpx(hwpx_path)
        assert status == 'ok'
        assert '찾아가는 상담실' in text

    def test_returns_error_for_empty_zip(self, tmp_path):
        hwpx_path = tmp_path / "empty.hwpx"
        with zipfile.ZipFile(str(hwpx_path), 'w'):
            pass
        status, _ = _extract_text_from_hwpx(hwpx_path)
        assert status == 'error'

    def test_returns_error_for_invalid_file(self, tmp_path):
        bad_path = tmp_path / "bad.hwpx"
        bad_path.write_bytes(b"not a zip file")
        status, _ = _extract_text_from_hwpx(bad_path)
        assert status == 'error'
```

- [ ] **Step 2: 테스트 실행**

```bash
cd backend
python3 -m pytest tests/test_attachment_extraction.py -v
```

Expected: 7 passed

- [ ] **Step 3: 커밋**

```bash
git add backend/tests/test_attachment_extraction.py
git commit -m "test: HWP/HWPX 텍스트 추출 함수 단위 테스트 추가"
```

---

## Task 6: 전체 파이프라인 smoke test (로컬 dry-run)

실제 OpenAI/Playwright 호출 없이 전체 파이프라인 코드 경로가 오류 없이 실행되는지 확인한다.

- [ ] **Step 1: review_service.py import 체인 검증**

```bash
cd backend
python3 -c "
from services.review_service import (
    FAST_APPROVE_PATTERNS, EXCLUSION_KEYWORDS,
    ATTACHMENT_MAX_CHARS_PER_FILE, ATTACHMENT_MAX_TOTAL_CHARS,
    classify_by_title, fetch_attachment_text_for_review,
    review_announcement_with_chatgpt, review_report_file,
)
print('✅ review_service 전체 import 성공')
"
```

- [ ] **Step 2: attachment_service.py import 체인 검증**

```bash
python3 -c "
from services.attachment_service import (
    extract_text_from_file,
    _extract_text_from_hwpx,
    _extract_text_from_hwp,
    _clean_hwp_text,
    analyze_attachments,
)
print('✅ attachment_service 전체 import 성공')
"
```

- [ ] **Step 3: review_and_upsert_firestore.py import 검증**

```bash
python3 -c "
from scripts.review_and_upsert_firestore import _prepare_firestore_data
result = _prepare_firestore_data({
    'title': '테스트 공고',
    'announcement_number': 'TEST-001',
    'status': 'pending',
    'review_method': 'with_attachment',
    'rejection_reason': 'low_confidence',
})
assert 'review_method' in result
assert 'rejection_reason' in result
print('✅ _prepare_firestore_data 신규 필드 확인 완료')
"
```

- [ ] **Step 4: 전체 테스트 수트 실행**

```bash
cd backend
python3 -m pytest tests/ -v --tb=short
```

Expected: 모든 테스트 통과

- [ ] **Step 5: 최종 커밋**

```bash
git add -A
git commit -m "feat: EAP 검수 파이프라인 v2 - 첨부파일 기반 2단계 GPT 검수 + Audit Trail 통합"
```

---

## 검증 체크리스트

실제 운영 전 수동 확인 항목:

- [ ] `python -m backend.entrypoints.daily_report --skip-slack --date YYYY-MM-DD` 로 전체 파이프라인 실행
- [ ] 결과 리포트에서 `review_method` 값 확인 (`keyword_filter` / `title_approved` / `with_attachment` / `attachment_failed`)
- [ ] GPT 응답 JSON이 정상 파싱되는지 확인 (`review_result` 필드)
- [ ] `status=pending` 공고가 Slack 메시지에 ⏸️ 미결로 표시되는지 확인
- [ ] Firestore에 `review_method`, `rejection_reason` 필드가 저장되는지 확인

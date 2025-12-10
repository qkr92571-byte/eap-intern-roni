# RFP 상세 분석 기능 구현 제안서

## 배경
적합 공고들의 RFP(제안요청서)를 분석하기 위해서는 공고의 표면적인 정보 외에도:
1. **공고 상세 페이지의 전체 내용** 수집
2. **첨부파일 내용 분석** (PDF, HWP 등)

이 필요합니다.

## 현재 시스템 상태

### ✅ 현재 수집하는 정보
- 공고명, 발주기관, 게시일, 공고번호
- 업무구분, 예산 정보 (기본 정보만)
- 목록 페이지에서 추출 가능한 정보

### ❌ 현재 미수집 정보
- 상세 페이지의 전체 내용 (업무 개요, 세부 요구사항, 평가 기준 등)
- 첨부파일 (RFP 문서, 제안서 양식, 계약서 초안 등)
- 상세 페이지 내부의 구조화된 데이터

## 구현 방안

### 1. 상세 페이지 내용 수집

#### 1.1 접근 방법
```python
# 공고번호로 상세 페이지 URL 생성 (이미 구현됨)
url = f"https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo={bidPbancNo}&bidPbancOrd={bidPbancOrd}"

# Playwright로 상세 페이지 접근
page.goto(url)
page.wait_for_load_state('networkidle')
```

#### 1.2 수집할 정보
- **기본 정보**: 이미 수집 중
- **업무 개요**: 상세 페이지의 "업무 개요" 섹션
- **세부 요구사항**: "용역 내용", "제공 서비스" 등
- **평가 기준**: "평가 방법", "평가 항목" 등
- **일정 정보**: "용역 기간", "착수 시기" 등
- **제출 서류**: "제출 서류 목록"
- **기타 조건**: "계약 조건", "지급 조건" 등

#### 1.3 구현 전략
```python
def scrape_detail_page(page, announcement_number: str) -> dict:
    """
    공고 상세 페이지에서 추가 정보 수집
    """
    # URL 생성
    url = get_nara_jangteo_url(announcement_number)
    page.goto(url)
    page.wait_for_load_state('networkidle')
    
    # 상세 정보 추출 (JavaScript로 DOM 파싱)
    detail_info = page.evaluate("""
        () => {
            // 나라장터 상세 페이지 구조 분석 필요
            // 각 섹션별로 정보 추출
            return {
                'work_overview': extract_section('업무개요'),
                'requirements': extract_section('용역내용'),
                'evaluation_criteria': extract_section('평가기준'),
                'schedule': extract_section('일정'),
                'submission_docs': extract_section('제출서류'),
                // ...
            }
        }
    """)
    
    return detail_info
```

**고려사항:**
- 나라장터 상세 페이지는 SPA(Single Page Application) 구조일 수 있음
- 동적 로딩되는 콘텐츠를 위해 적절한 대기 시간 필요
- 페이지 구조 변경에 대비한 유연한 파싱 로직 필요

---

### 2. 첨부파일 다운로드 및 파싱

#### 2.1 첨부파일 다운로드

```python
def download_attachments(page, announcement_number: str) -> List[dict]:
    """
    상세 페이지에서 첨부파일 링크 찾아서 다운로드
    """
    # 첨부파일 링크 찾기
    attachment_links = page.evaluate("""
        () => {
            const links = Array.from(document.querySelectorAll(
                'a[href*="download"], a[href*="file"], a[href*="attach"]'
            ));
            return links.map(link => ({
                name: link.textContent.trim(),
                url: link.href,
                type: detect_file_type(link.href) // .pdf, .hwp 등
            }));
        }
    """)
    
    downloaded_files = []
    for attachment in attachment_links:
        # Playwright로 파일 다운로드
        with page.expect_download() as download_info:
            page.click(f'a[href="{attachment["url"]}"]')
        download = download_info.value
        
        # 파일 저장
        file_path = save_path / f"{announcement_number}_{attachment['name']}"
        download.save_as(file_path)
        
        downloaded_files.append({
            'name': attachment['name'],
            'path': str(file_path),
            'type': attachment['type']
        })
    
    return downloaded_files
```

#### 2.2 PDF 파일 파싱

**라이브러리**: `pdfplumber` (이미 프로젝트에 사용 중)

```python
import pdfplumber

def parse_pdf(file_path: str) -> dict:
    """
    PDF 파일에서 텍스트 및 표 추출
    """
    text_content = []
    tables = []
    
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            # 텍스트 추출
            text = page.extract_text()
            if text:
                text_content.append(text)
            
            # 표 추출
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
    
    return {
        'text': '\n\n'.join(text_content),
        'tables': tables,
        'page_count': len(pdf.pages)
    }
```

**장점:**
- 이미 프로젝트에 설치되어 있음
- 텍스트와 표 모두 추출 가능
- 안정적이고 널리 사용됨

---

#### 2.3 HWP 파일 파싱 ⚠️ **핵심 과제**

HWP 파일은 한국 특화 형식이라 파싱이 복잡합니다.

##### 옵션 1: `pyhwp` 라이브러리 (Python) ✅ **선택됨**

```python
# 설치: pip install pyhwp
from pyhwp import hwp5

def parse_hwp(file_path: str) -> dict:
    """
    HWP 파일에서 텍스트 추출 (HWP5 형식)
    """
    try:
        hwp_file = hwp5.open(file_path)
        text_content = []
        
        # 본문 텍스트 추출
        if hasattr(hwp_file, 'bodytext') and hwp_file.bodytext:
            for section in hwp_file.bodytext.sections:
                if hasattr(section, 'paragraphs'):
                    for paragraph in section.paragraphs:
                        # char_list에서 텍스트 추출
                        if hasattr(paragraph, 'char_list'):
                            chars = []
                            for char in paragraph.char_list:
                                if hasattr(char, 'char') and char.char:
                                    chars.append(char.char)
                            if chars:
                                text_content.append(''.join(chars))
        
        return {
            'text': '\n\n'.join(text_content),
            'success': len(text_content) > 0,
            'format': 'hwp5'
        }
    except Exception as e:
        return {
            'text': '',
            'error': str(e),
            'success': False,
            'format': 'unknown'
        }
```

**장단점:**
- ✅ 순수 Python 라이브러리
- ✅ HWP5 형식 지원 (대부분의 최신 HWP 파일)
- ✅ 구현 간단
- ❌ 구버전 HWP는 미지원 (HWP5 이전 버전)
- ❌ 표, 이미지 추출 제한적

**구현 상태:**
- ✅ `file_parser_service.py`에 구현 완료
- ✅ `requirements.txt`에 `pyhwp==0.1b12` 추가
- ✅ 테스트 스크립트 제공 (`test_file_parser.py`)

##### 옵션 2: `olefile` + 수동 파싱

```python
import olefile

def parse_hwp_ole(file_path: str) -> dict:
    """
    HWP를 OLE 파일로 파싱 (HWP5 이전 버전)
    """
    if not olefile.isOleFile(file_path):
        return {'error': 'Not an OLE file'}
    
    ole = olefile.OleFileIO(file_path)
    # HWP 내부 구조 파싱 (복잡함)
    # ...
```

**장단점:**
- ✅ 구버전 HWP 지원 가능
- ❌ 매우 복잡한 구현 필요
- ❌ HWP 내부 구조 이해 필요

##### 옵션 3: **LibreOffice/OpenOffice 변환** (추천)

```python
import subprocess
import os

def convert_hwp_to_pdf(hwp_path: str, output_dir: str) -> str:
    """
    LibreOffice를 사용하여 HWP를 PDF로 변환 후 파싱
    """
    pdf_path = os.path.join(output_dir, os.path.basename(hwp_path).replace('.hwp', '.pdf'))
    
    # LibreOffice 명령어 실행
    subprocess.run([
        'libreoffice',
        '--headless',
        '--convert-to', 'pdf',
        '--outdir', output_dir,
        hwp_path
    ], check=True)
    
    # 변환된 PDF 파싱
    return parse_pdf(pdf_path)
```

**장단점:**
- ✅ 가장 안정적이고 호환성 높음
- ✅ HWP 모든 버전 지원
- ✅ 표, 이미지도 잘 보존됨
- ❌ LibreOffice 설치 필요 (서버 환경)
- ❌ 변환 시간 소요

##### 옵션 4: **외부 API 서비스 활용**

```python
# 예: 한글과컴퓨터 API, 또는 클라우드 변환 서비스
def convert_hwp_via_api(hwp_path: str) -> dict:
    """
    외부 API를 통한 HWP 변환
    """
    # API 호출하여 PDF 또는 텍스트로 변환
    # ...
```

**장단점:**
- ✅ 구현 간단
- ✅ 안정적
- ❌ 비용 발생 가능
- ❌ 외부 의존성

##### 옵션 5: **한글 뷰어 자동화** (Playwright 활용)

```python
def parse_hwp_with_viewer(hwp_path: str) -> dict:
    """
    웹 기반 한글 뷰어를 통해 HWP 내용 추출
    """
    # 한글과컴퓨터 웹 뷰어 또는 다른 온라인 뷰어 사용
    # Playwright로 뷰어 페이지 접근하여 텍스트 추출
    # ...
```

**장단점:**
- ✅ 추가 소프트웨어 설치 불필요
- ❌ 웹 뷰어 의존성
- ❌ 안정성 낮을 수 있음

---

### 3. 데이터 저장 구조

#### 3.1 Firestore 스키마 확장

```typescript
interface Announcement {
  // 기존 필드
  id: string;
  title: string;
  agency: string;
  // ...
  
  // 새로 추가할 필드
  detail_content?: {
    work_overview?: string;
    requirements?: string;
    evaluation_criteria?: string;
    schedule?: string;
    submission_docs?: string[];
    // ...
  };
  
  attachments?: {
    name: string;
    file_path: string; // Firebase Storage 경로 또는 로컬 경로
    file_type: 'pdf' | 'hwp' | 'doc' | 'docx' | 'xls' | 'xlsx';
    parsed_content?: {
      text?: string;
      tables?: any[];
      page_count?: number;
    };
    download_date: string;
  }[];
  
  detail_scraped_at?: string; // 상세 정보 수집 일시
  detail_scrape_status?: 'pending' | 'success' | 'failed';
}
```

#### 3.2 파일 저장 전략

**옵션 A: Firebase Storage**
- ✅ 클라우드 저장, 접근 용이
- ✅ 프론트엔드에서 직접 접근 가능
- ❌ 저장 비용 발생
- ❌ 대용량 파일 처리 시 비용 증가

**옵션 B: 로컬 파일 시스템**
- ✅ 비용 없음
- ✅ 빠른 접근
- ❌ 서버 확장성 문제
- ❌ 백업 필요

**옵션 C: 하이브리드**
- 원본 파일: 로컬 저장
- 파싱된 텍스트: Firestore에 저장
- 필요시 Firebase Storage에 업로드

---

### 4. 구현 단계별 제안

#### Phase 1: 상세 페이지 수집 (우선순위 높음)
1. 상세 페이지 접근 로직 구현
2. 기본 섹션 정보 추출 (업무 개요, 요구사항 등)
3. Firestore 스키마 확장
4. 수집된 정보 저장

**예상 소요 시간**: 2-3일

#### Phase 2: PDF 첨부파일 파싱
1. 첨부파일 링크 탐지
2. PDF 다운로드 로직
3. PDF 파싱 (pdfplumber 활용)
4. 파싱 결과 저장

**예상 소요 시간**: 1-2일

#### Phase 3: HWP 파일 파싱 (가장 복잡)
1. HWP 파싱 방법 결정 (LibreOffice 변환 추천)
2. 변환 파이프라인 구현
3. 에러 처리 및 폴백 로직
4. 테스트 및 최적화

**예상 소요 시간**: 3-5일

---

### 5. 기술적 고려사항

#### 5.1 성능
- **대량 처리**: 수백 개 공고의 상세 정보 수집 시 시간 소요
- **해결책**: 
  - 비동기 처리 (asyncio)
  - 배치 처리
  - 적합 공고만 선별적으로 수집

#### 5.2 안정성
- **페이지 구조 변경**: 나라장터 사이트 구조 변경 시 파싱 실패
- **해결책**:
  - 유연한 파싱 로직 (여러 선택자 시도)
  - 에러 로깅 및 알림
  - 수동 검수 프로세스

#### 5.3 비용
- **Firebase Storage**: 파일 저장 비용
- **API 호출**: 외부 변환 서비스 사용 시
- **해결책**: 
  - 적합 공고만 수집
  - 파싱된 텍스트만 저장 (원본 파일은 선택적)

#### 5.4 법적/윤리적 고려
- 나라장터 이용약관 준수
- 과도한 요청 방지 (Rate Limiting)
- 수집된 데이터의 사용 목적 명확화

---

### 6. 추천 구현 순서

1. **상세 페이지 수집** (Phase 1)
   - 가장 중요하고 구현이 상대적으로 간단
   - RFP 분석에 핵심적인 정보 제공

2. **PDF 파싱** (Phase 2)
   - 이미 인프라 준비됨 (pdfplumber)
   - 빠르게 구현 가능

3. **HWP 파싱** (Phase 3)
   - LibreOffice 변환 방식 추천
   - 서버 환경에 LibreOffice 설치 필요

---

### 7. 예상 도전 과제

1. **나라장터 상세 페이지 구조 파악**
   - 실제 페이지 구조 분석 필요
   - 동적 콘텐츠 로딩 대응

2. **HWP 파일 호환성**
   - 다양한 HWP 버전 지원
   - 깨진 파일 처리

3. **대용량 파일 처리**
   - 수십 MB 크기의 첨부파일
   - 메모리 관리

4. **파싱 품질**
   - 표, 이미지 등 복잡한 구조 추출
   - 한글 인코딩 문제

---

## 결론

RFP 상세 분석 기능은 **구현 가능**하며, 단계적 접근이 필요합니다.

**즉시 시작 가능한 작업:**
- 상세 페이지 수집 로직 개발
- PDF 첨부파일 파싱

**추가 검토 필요:**
- HWP 파싱 방법 최종 결정 (LibreOffice 변환 추천)
- 파일 저장 전략 (로컬 vs Firebase Storage)
- 대량 처리 시 성능 최적화

**다음 단계 제안:**
1. 나라장터 상세 페이지 구조 분석 (실제 페이지 접근하여 DOM 구조 파악)
2. 샘플 공고 1-2개로 상세 페이지 수집 프로토타입 개발
3. 첨부파일 다운로드 테스트
4. HWP 파싱 방법 POC (Proof of Concept) 개발

이 순서로 진행하면 단계적으로 기능을 확장할 수 있습니다.


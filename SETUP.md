# 설치 및 설정 가이드

## 사전 요구사항

- Python 3.8 이상
- Node.js 16 이상 및 npm
- Firebase 프로젝트 및 서비스 계정 키
- OpenAI API 키

## 1. 백엔드 설정

### 1.1 Python 가상환경 생성 및 활성화

```bash
cd backend
python -m venv venv

# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 1.2 의존성 설치

```bash
pip install -r requirements.txt
```

### 1.3 Playwright 브라우저 설치

```bash
playwright install chromium
```

### 1.4 Firebase 설정

1. Firebase 콘솔에서 서비스 계정 키 다운로드
2. `backend/config/firebase-credentials.json`에 저장
3. 또는 환경 변수로 설정 가능

### 1.5 환경 변수 설정

`backend/.env` 파일 생성:

```env
# Firebase 설정
FIREBASE_CREDENTIALS_PATH=config/firebase-credentials.json

# OpenAI API 설정
OPENAI_API_KEY=your_openai_api_key_here

# 스케줄러 설정
SCHEDULE_HOUR=9
SCHEDULE_MINUTE=0
SCRAPE_KEYWORDS=소프트웨어,개발,IT

# Flask 설정
PORT=5000
```

### 1.6 백엔드 실행

```bash
python app.py
```

## 2. 프론트엔드 설정

### 2.1 의존성 설치

```bash
cd frontend
npm install
```

### 2.2 환경 변수 설정 (선택사항)

`frontend/.env` 파일 생성:

```env
REACT_APP_API_URL=http://localhost:5000/api
```

### 2.3 프론트엔드 실행

```bash
npm start
```

프론트엔드는 기본적으로 `http://localhost:3000`에서 실행됩니다.

## 3. 스케줄러 설정 (선택사항)

스케줄러를 사용하려면 `backend/app.py`에 다음 코드를 추가하세요:

```python
from services.scheduler_service import start_scheduler

# 앱 시작 시 스케줄러 시작
if __name__ == '__main__':
    start_scheduler()
    # ... 기존 코드
```

## 4. 나라장터 스크래퍼 설정

`backend/services/scraper_service.py`의 xpath는 실제 나라장터 사이트 구조에 맞게 수정해야 합니다.

현재 코드는 예시이며, 실제 사이트 구조를 확인하여 다음 부분을 수정하세요:

- 검색 입력 필드 xpath
- 검색 버튼 xpath
- 공고 목록 테이블 xpath
- 상세 페이지 정보 추출 xpath

## 5. 필터링 로직 커스터마이징

`backend/services/filter_service.py`의 다음 함수들을 회사 요구사항에 맞게 수정하세요:

- `keyword_filter()`: 키워드 필터링 로직
- `internal_filter()`: 내부 비즈니스 로직 필터링
- `review_with_chatgpt()`: ChatGPT 검수 프롬프트

## 문제 해결

### Playwright 오류
- 브라우저가 설치되지 않은 경우: `playwright install chromium` 실행

### Firebase 연결 오류
- 서비스 계정 키 파일 경로 확인
- Firebase 프로젝트 설정 확인

### CORS 오류
- 백엔드의 Flask-CORS가 올바르게 설정되어 있는지 확인
- 프론트엔드의 API URL이 올바른지 확인



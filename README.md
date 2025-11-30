# 나라장터 사업 공고 수집 시스템

나라장터 사업 공고를 자동으로 수집하고 관리하는 시스템입니다.

## 기술 스택

- **프론트엔드**: React + TypeScript
- **백엔드**: Python Flask
- **데이터베이스**: Firebase (NoSQL)
- **웹 스크래핑**: Playwright
- **스케줄러**: Cron (추후 적용 예정)
- **AI 검수**: ChatGPT API

## 프로젝트 구조

```
eap_intern_roni/
├── frontend/                    # React + TypeScript 프론트엔드
│   ├── src/
│   │   ├── components/          # 공통 컴포넌트
│   │   ├── pages/               # 페이지 컴포넌트
│   │   └── services/            # API 서비스
│   └── package.json
├── backend/                     # Flask 백엔드
│   ├── routes/                  # API 라우트
│   ├── services/                # 비즈니스 로직
│   │   ├── scraper_service.py   # Playwright 스크래퍼
│   │   ├── filter_service.py    # 필터링 및 ChatGPT 검수
│   │   ├── firebase_service.py  # Firebase 연동
│   │   └── scheduler_service.py # Cron 스케줄러
│   ├── app.py                   # Flask 앱 진입점
│   └── requirements.txt
├── SETUP.md                     # 상세 설치 가이드
└── README.md
```

## 빠른 시작

자세한 설치 가이드는 [SETUP.md](./SETUP.md)를 참고하세요.

### 백엔드 설정
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# .env 파일 생성 및 설정 필요
python app.py
```

### 프론트엔드 설정
```bash
cd frontend
npm install
npm start
```

프론트엔드는 `http://localhost:3000`에서 실행됩니다.

## 주요 기능

1. **나라장터 사업 공고 자동 수집**
   - Playwright를 사용한 웹 스크래핑
   - 키워드 기반 검색 지원
   - 상세 페이지 정보 수집

2. **스마트 필터링 시스템**
   - 1차: 키워드 기반 필터링
   - 2차: 내부 비즈니스 로직 필터링 (예산, 기관 등)
   - 3차: ChatGPT API를 통한 AI 검수

3. **관리자 대시보드**
   - 공고 목록 조회 및 검색
   - 공고 상세 정보 확인
   - 수집 상태 모니터링 (승인/대기/거부)
   - 수동 수집 실행

4. **자동화 스케줄러**
   - Cron 기반 자동 수집 (APScheduler)
   - 환경 변수로 실행 시간 설정 가능
   - 수집 후 자동 필터링 및 검수

## API 엔드포인트

- `GET /api/announcements` - 공고 목록 조회
- `GET /api/announcements/:id` - 공고 상세 조회
- `POST /api/announcements/scrape` - 공고 수집 실행
- `POST /api/announcements/filter` - 공고 필터링 및 검수
- `PUT /api/announcements/:id` - 공고 업데이트
- `DELETE /api/announcements/:id` - 공고 삭제

## 주의사항

1. **나라장터 사이트 구조 변경 대응**: `backend/services/scraper_service.py`의 xpath는 실제 사이트 구조에 맞게 수정이 필요합니다.

2. **Firebase 설정**: Firebase 서비스 계정 키 파일이 필요합니다.

3. **OpenAI API 키**: ChatGPT 검수 기능을 사용하려면 OpenAI API 키가 필요합니다.

4. **법적 고지**: 웹 스크래핑 시 나라장터의 이용약관을 준수해야 합니다.


# Firebase 설정 가이드

나라장터 공고 수집 시스템에서 Firebase를 사용하기 위한 설정 가이드입니다.

## 1. Firebase 프로젝트 생성

1. [Firebase 콘솔](https://console.firebase.google.com)에 접속
2. "프로젝트 추가" 클릭
3. 프로젝트 이름 입력 (예: `eap-intern-roni`)
4. Google Analytics 설정 (선택사항)
5. 프로젝트 생성 완료

## 2. Firestore 데이터베이스 생성

1. Firebase 콘솔에서 생성한 프로젝트 선택
2. 왼쪽 메뉴에서 "Firestore Database" 클릭
3. "데이터베이스 만들기" 클릭
4. **프로덕션 모드** 또는 **테스트 모드** 선택
   - 테스트 모드: 30일간 무제한 읽기/쓰기 (개발용)
   - 프로덕션 모드: 보안 규칙 설정 필요 (운영용)
5. 위치 선택 (가장 가까운 리전 선택, 예: `asia-northeast3` - 서울)
6. "사용 설정" 클릭

## 3. 서비스 계정 키 생성

1. Firebase 콘솔에서 프로젝트 설정(톱니바퀴 아이콘) 클릭
2. "서비스 계정" 탭 선택
3. "Firebase Admin SDK" 섹션에서 "새 비공개 키 생성" 클릭
4. 경고 메시지 확인 후 "키 생성" 클릭
5. JSON 파일이 자동으로 다운로드됩니다

## 4. 서비스 계정 키 파일 저장

1. 다운로드한 JSON 파일을 `backend/config/` 디렉토리에 복사
2. 파일명을 `firebase-credentials.json`으로 변경

```
backend/
└── config/
    └── firebase-credentials.json  # 다운로드한 파일을 여기에 저장
```

## 5. 환경 변수 설정

`backend/.env` 파일이 이미 생성되어 있습니다. 다음 항목을 확인하세요:

```env
FIREBASE_CREDENTIALS_PATH=config/firebase-credentials.json
```

파일 경로가 올바른지 확인하세요. 상대 경로는 `backend/` 디렉토리 기준입니다.

## 6. Firestore 보안 규칙 설정 (프로덕션 모드인 경우)

Firebase 콘솔 > Firestore Database > 규칙 탭에서 다음 규칙을 설정하세요:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // announcements 컬렉션에 대한 규칙
    match /announcements/{announcementId} {
      // 서버(백엔드)에서만 읽기/쓰기 가능
      allow read, write: if request.auth != null || request.auth == null;
      // 또는 더 엄격하게: 서버에서만 접근 가능하도록 설정
    }
  }
}
```

⚠️ **주의**: 위 규칙은 개발용입니다. 프로덕션 환경에서는 더 엄격한 규칙을 설정해야 합니다.

## 7. 연결 테스트

백엔드 서버를 실행하여 Firebase 연결을 테스트하세요:

```bash
cd backend
python app.py
```

서버가 정상적으로 시작되면 Firebase 연결이 성공한 것입니다.

## 8. 데이터 구조

시스템은 다음 컬렉션을 사용합니다:

- **announcements**: 수집된 공고 정보
  - `title`: 공고 제목
  - `agency`: 발주 기관
  - `deadline`: 마감일
  - `status`: 상태 (pending, approved, rejected)
  - `content`: 공고 내용
  - `budget`: 예산
  - `category`: 카테고리
  - `url`: 원본 링크
  - `created_at`: 수집일시
  - `filtered`: 필터링 여부
  - `reviewed`: 검수 여부
  - `review_result`: 검수 결과 (ChatGPT)

## 문제 해결

### 오류: "Could not find the default credentials"
- `FIREBASE_CREDENTIALS_PATH` 환경 변수가 올바른지 확인
- 파일 경로가 정확한지 확인 (상대 경로는 `backend/` 기준)
- 파일이 실제로 존재하는지 확인

### 오류: "Permission denied"
- Firestore 보안 규칙 확인
- 서비스 계정에 적절한 권한이 있는지 확인

### 오류: "Project not found"
- Firebase 프로젝트 ID가 올바른지 확인
- 서비스 계정 키 파일이 올바른 프로젝트의 것인지 확인

## 보안 체크리스트

- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는지 확인
- [ ] `firebase-credentials.json` 파일이 Git에 커밋되지 않았는지 확인
- [ ] 서비스 계정 키 파일을 안전한 위치에 보관
- [ ] 프로덕션 환경에서는 Firestore 보안 규칙을 엄격하게 설정
- [ ] 환경 변수를 통해 민감한 정보 관리



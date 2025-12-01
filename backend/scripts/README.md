# 스크립트 디렉토리

이 디렉토리는 일회성 작업, 테스트, 유틸리티 스크립트를 포함합니다.

## 스크립트 목록

### 일회성 작업 스크립트

#### `upload_report_to_firestore.py`
오늘 수집된 리포트를 Firestore에 업로드하는 스크립트

**사용법:**
```bash
cd backend
python3 scripts/upload_report_to_firestore.py
```

#### `delete_old_firestore_data.py`
Firestore에서 오늘이 아닌 샘플 데이터를 삭제하는 스크립트

**사용법:**
```bash
cd backend
python3 scripts/delete_old_firestore_data.py
```

⚠️ **주의**: 이 스크립트는 오늘이 아닌 모든 데이터를 삭제합니다.

#### `create_firestore_index.py`
Firestore 인덱스를 생성하는 스크립트

**사용법:**
```bash
cd backend
python3 scripts/create_firestore_index.py
```

### 테스트 스크립트

#### `test_scraper.py`
스크래퍼 서비스를 테스트하는 스크립트

**사용법:**
```bash
cd backend
python3 scripts/test_scraper.py
```

#### `test_firebase.py`
Firebase 연결 및 기본 기능을 테스트하는 스크립트

**사용법:**
```bash
cd backend
python3 scripts/test_firebase.py
```

#### `test_db_insert.py`
Firestore 데이터 삽입 및 조회를 테스트하는 스크립트

**사용법:**
```bash
cd backend
python3 scripts/test_db_insert.py
```

#### `test_api.py`
백엔드 API 엔드포인트를 테스트하는 스크립트

**사용법:**
```bash
cd backend
python3 scripts/test_api.py
```

## 실행 방법

모든 스크립트는 `backend` 디렉토리에서 실행해야 합니다:

```bash
cd backend
python3 scripts/<스크립트명>.py
```

스크립트들은 자동으로 `backend` 디렉토리를 Python 경로에 추가하므로, `services`, `models` 등의 모듈을 정상적으로 import할 수 있습니다.


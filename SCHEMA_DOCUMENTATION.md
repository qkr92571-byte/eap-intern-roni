# 나라장터 공고 데이터 스키마 문서

## 개요

이 문서는 Firestore에 저장되는 나라장터 공고 데이터의 구조를 정의합니다.

## 데이터 모델

### 컬렉션명
- `announcements`

### 문서 구조

#### 필수 필드

| 필드명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| `title` | string | 공고명 | "2026년 찾아가는 상담실 운영" |
| `announcement_number` | string | 공고번호 | "R25BK01187770" |
| `agency` | string | 공고기관 | "제주특별자치도 소방안전본부" |
| `created_at` | string | 수집일시 (ISO 8601 형식) | "2024-11-30T09:00:00Z" |

#### 선택 필드

| 필드명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| `budget_amount` | number | 예산금액 (원 단위 숫자) | 150704000 |
| `estimated_price` | number | 추정가격 (원 단위 숫자) | 137003636 |
| `business_type` | string | 사업구분 | "일반용역" |
| `announcement_status` | string | 공고상태 (나라장터 원본 상태) | "입찰_낙찰제안평가" |
| `deadline` | string | 마감일 | "2024-12-31" |
| `url` | string | 원본 링크 | "https://www.g2b.go.kr/..." |
| `content` | string | 공고 내용 | "상세 내용..." |
| `category` | string | 카테고리 | "소방안전" |

#### 시스템 필드

| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `status` | string | 시스템 내부 상태 | "pending" |
| `filtered` | boolean | 필터링 여부 | false |
| `reviewed` | boolean | 검수 여부 | false |
| `review_result` | string | 검수 결과 (ChatGPT) | null |
| `source` | string | 출처 | "나라장터" |

### 상태 값

#### `status` 필드
- `pending`: 대기 중 (수집 후 필터링/검수 전)
- `approved`: 승인됨 (필터링 및 검수 통과)
- `rejected`: 거부됨 (필터링 또는 검수 실패)

## 데이터 예시

```json
{
  "title": "2026년 찾아가는 상담실 운영",
  "announcement_number": "R25BK01187770",
  "agency": "제주특별자치도 소방안전본부",
  "budget_amount": 150704000,
  "estimated_price": 137003636,
  "business_type": "일반용역",
  "announcement_status": "입찰_낙찰제안평가",
  "deadline": "2024-12-31",
  "url": "https://www.g2b.go.kr/ep/co/co020/co02010/co02010/selectDetail.do?bidId=R25BK01187770",
  "content": "상세 공고 내용...",
  "category": "소방안전",
  "status": "pending",
  "filtered": false,
  "reviewed": false,
  "created_at": "2024-11-30T09:00:00Z",
  "source": "나라장터"
}
```

## 사용 방법

### 백엔드에서 공고 생성

```python
from models.announcement_schema import AnnouncementSchema

# 공고 데이터 생성
announcement = AnnouncementSchema.create_announcement(
    title="2026년 찾아가는 상담실 운영",
    announcement_number="R25BK01187770",
    agency="제주특별자치도 소방안전본부",
    budget_amount=150704000,
    estimated_price=137003636,
    business_type="일반용역",
    announcement_status="입찰_낙찰제안평가"
)

# 유효성 검사
is_valid, error = AnnouncementSchema.validate_announcement(announcement)
if is_valid:
    # Firestore에 저장
    from services.firebase_service import save_announcement
    announcement_id = save_announcement(announcement)
```

### 예산 문자열 파싱

```python
from models.announcement_schema import AnnouncementSchema

# "150,704,000원" -> 150704000
budget = AnnouncementSchema.parse_budget_string("150,704,000원")
print(budget)  # 150704000
```

## Firestore 인덱스

다음 쿼리를 사용하려면 Firestore에서 복합 인덱스를 생성해야 합니다:

1. `status` + `created_at` (내림차순)
2. `agency` + `created_at` (내림차순)
3. `business_type` + `created_at` (내림차순)

### 인덱스 생성 방법

1. Firebase 콘솔 접속
2. Firestore Database > 인덱스 탭
3. "인덱스 만들기" 클릭
4. 컬렉션 ID: `announcements`
5. 필드 추가:
   - 필드: `status`, 정렬: 오름차순
   - 필드: `created_at`, 정렬: 내림차순
6. "만들기" 클릭

## 주의사항

1. **예산 금액**: 숫자 타입으로 저장 (문자열이 아닌 원 단위 숫자)
2. **날짜 형식**: ISO 8601 형식 사용 (예: "2024-11-30T09:00:00Z")
3. **공고번호**: 중복 방지를 위해 인덱스 생성 권장
4. **데이터 검증**: 저장 전 `AnnouncementSchema.validate_announcement()` 사용 권장

## 마이그레이션

기존 데이터가 있는 경우, 다음 스크립트로 마이그레이션할 수 있습니다:

```python
from services.firebase_service import get_db, get_announcements
from models.announcement_schema import AnnouncementSchema

db = get_db()
announcements = get_announcements(limit=1000)

for announcement in announcements:
    # 기존 데이터를 새 스키마로 변환
    updated_data = {}
    
    # 필수 필드 확인 및 추가
    if 'announcement_number' not in announcement:
        updated_data['announcement_number'] = ''  # 또는 기존 데이터에서 추출
    
    # 예산 금액 파싱
    if 'budget' in announcement and isinstance(announcement['budget'], str):
        updated_data['budget_amount'] = AnnouncementSchema.parse_budget_string(announcement['budget'])
    
    # 업데이트
    if updated_data:
        db.collection('announcements').document(announcement['id']).update(updated_data)
```



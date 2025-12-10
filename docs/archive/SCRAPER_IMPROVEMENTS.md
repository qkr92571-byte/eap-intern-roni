# 스크래퍼 브라우저 크래시 방지 개선 사항

## 개선 일자
2025-12-04

## 문제점
리포트 생성 시마다 브라우저 크래시가 계속 발생하여 데이터 수집이 실패하는 문제가 발생했습니다.

## 분석 결과

### 다른 프로젝트 (naramarket-mcp-slack)와의 차이점

1. **브라우저 실행 방식**
   - **기존**: Chromium만 사용, 크래시 방지 옵션 없음
   - **개선**: Firefox를 먼저 시도하고, 실패 시 Chromium with 크래시 방지 옵션 사용

2. **헤드리스 모드 기본값**
   - **기존**: `PLAYWRIGHT_HEADLESS` 환경변수가 없으면 `false` (headless=False)
   - **개선**: `PLAYWRIGHT_HEADLESS` 환경변수가 없으면 `true` (headless=True)

3. **브라우저 실행 옵션**
   - **기존**: 옵션 없음
   - **개선**: macOS 크래시 방지를 위한 다음 옵션 추가:
     - `--disable-gpu`
     - `--disable-software-rasterizer`
     - `--disable-dev-shm-usage`
     - `--no-sandbox`
     - `--disable-setuid-sandbox`

## 적용된 개선 사항

### 1. 헤드리스 모드 기본값 변경
```python
# 변경 전
headless_env = os.getenv('PLAYWRIGHT_HEADLESS', 'false').lower()

# 변경 후
headless_env = os.getenv('PLAYWRIGHT_HEADLESS', 'true').lower()
```

### 2. 브라우저 실행 로직 개선
```python
# Firefox 먼저 시도
try:
    browser = p.firefox.launch(headless=headless)
    print("  ✅ Firefox 브라우저로 실행")
except Exception as e:
    print(f"  ⚠️  Firefox 실행 실패, Chromium 재시도: {e}")
    # macOS 크래시 방지를 위한 추가 옵션
    browser = p.chromium.launch(
        headless=headless,
        args=[
            '--disable-gpu',
            '--disable-software-rasterizer',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox'
        ]
    )
```

## 변경 사항 요약

1. ✅ 헤드리스 모드를 기본값으로 변경 (기본값: `true`)
2. ✅ Firefox 브라우저 우선 사용 (크래시 방지)
3. ✅ Chromium 크래시 방지 옵션 추가
4. ✅ 다른 프로젝트의 검증된 로직 적용

## 주의사항

- **이 로직은 앞으로의 작업으로 인해 변경되어서는 안 됩니다.**
- 브라우저 크래시 문제가 지속되면 브라우저 재설치를 고려해야 합니다.
- 환경변수 `PLAYWRIGHT_HEADLESS=false`로 설정하면 헤드리스 모드를 비활성화할 수 있습니다.

## 브라우저 재설치 방법 (필요시)

```bash
# Playwright 브라우저 재설치
cd backend
playwright install --force chromium
playwright install --force firefox
```

## 테스트 방법

```bash
# 헤드리스 모드로 테스트 (기본값)
cd backend
python3 scripts/test_scraper.py

# 헤드리스 모드 비활성화하여 테스트
PLAYWRIGHT_HEADLESS=false python3 scripts/test_scraper.py
```






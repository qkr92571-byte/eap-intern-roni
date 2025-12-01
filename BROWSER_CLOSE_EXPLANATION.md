# 브라우저 종료 방식 차이점 분석

## 질문
왜 한 프로젝트에서는 `context.close()`를 사용하고, 다른 프로젝트에서는 `browser.close()`를 사용했는가?

## Playwright의 브라우저 종료 방식

### 1. `context.close()` vs `browser.close()` 차이점

**Playwright의 계층 구조**:
```
Browser (브라우저 인스턴스)
  └── Context (브라우저 컨텍스트 - 쿠키, 세션 등)
      └── Page (페이지/탭)
```

**`context.close()`**:
- 브라우저 컨텍스트만 닫음
- 해당 컨텍스트의 모든 페이지가 닫힘
- 브라우저 인스턴스는 여전히 실행 중
- 다른 컨텍스트가 있으면 브라우저는 계속 실행됨

**`browser.close()`**:
- 브라우저 인스턴스 전체를 닫음
- 모든 컨텍스트와 페이지가 자동으로 닫힘
- 브라우저 프로세스가 완전히 종료됨

### 2. 두 프로젝트의 실제 사용 방식

#### naramarket-mcp-slack 프로젝트
```python
with sync_playwright() as p:
    browser = p.chromium.launch(headless=headless)
    context = browser.new_context(...)
    page = context.new_page()
    
    try:
        # 스크래핑 작업...
    finally:
        browser.close()  # ✅ 브라우저 전체 종료
```

#### eap-intern-roni 프로젝트 (수정 전)
```python
with sync_playwright() as p:
    browser = p.chromium.launch(headless=headless)
    context = browser.new_context(...)
    page = context.new_page()
    
    try:
        # 스크래핑 작업...
    finally:
        context.close()  # ❌ 컨텍스트만 닫음
        browser.close()  # 브라우저도 닫음 (중복)
```

### 3. 문제점 분석

**`context.close()`를 먼저 호출하면**:
1. 컨텍스트가 닫히면서 모든 페이지가 닫힘
2. 이후 `browser.close()`를 호출할 때 이미 닫힌 컨텍스트를 참조하려고 시도
3. `TargetClosedError` 발생 가능성

**올바른 방식**:
- `browser.close()`만 호출하면 됨
- 브라우저를 닫으면 모든 컨텍스트와 페이지가 자동으로 정리됨
- `context.close()`는 불필요함 (중복)

### 4. 왜 처음에 발견하지 못했는가?

#### 원인 분석

1. **코드 비교 시점의 문제**
   - 처음 비교할 때는 전체적인 로직 흐름에 집중
   - 브라우저 종료 부분은 "finally 블록에서 정리하는 것"으로만 인식
   - 세부적인 메서드 호출 순서까지 비교하지 않음

2. **에러 발생 전까지 문제 인식 불가**
   - `context.close()` + `browser.close()` 조합이 문법적으로는 문제없음
   - 실제 실행 시에만 `TargetClosedError` 발생
   - 정적 분석만으로는 문제를 발견하기 어려움

3. **Playwright 문서의 모호함**
   - 공식 문서에서도 두 방법 모두 언급됨
   - "언제 어떤 것을 사용해야 하는가"에 대한 명확한 가이드 부족
   - 일반적으로 `browser.close()`만 사용하는 것이 안전하다는 점이 명시되지 않음

4. **코드 복사/붙여넣기 과정**
   - 다른 프로젝트에서 코드를 가져올 때
   - "안전하게 보이면" 두 개 다 호출하는 것이 좋을 것 같다는 착각
   - 실제로는 중복이고 오히려 문제를 일으킬 수 있음

5. **테스트 환경의 차이**
   - 개발 환경에서는 문제가 드러나지 않을 수 있음
   - 특정 타이밍이나 조건에서만 발생하는 경쟁 조건(race condition)
   - 실제 운영 환경에서만 문제가 발생할 수 있음

### 5. 올바른 해결 방법

**권장 방식**:
```python
with sync_playwright() as p:
    browser = p.chromium.launch(headless=headless)
    context = browser.new_context(...)
    page = context.new_page()
    
    try:
        # 스크래핑 작업...
    finally:
        # browser.close()만 호출하면 됨
        # context와 page는 자동으로 정리됨
        browser.close()
```

**또는 Context Manager 사용**:
```python
with sync_playwright() as p:
    browser = p.chromium.launch(headless=headless)
    with browser.new_context(...) as context:
        page = context.new_page()
        # 스크래핑 작업...
        # context는 자동으로 닫힘
    # browser는 여전히 열려있음
    browser.close()  # 명시적으로 브라우저 닫기
```

### 6. 교훈

1. **리소스 정리 시 단일 책임 원칙**
   - 하나의 리소스는 하나의 방법으로만 정리
   - 중복 호출은 오히려 문제를 일으킬 수 있음

2. **에러 메시지에 주의**
   - `TargetClosedError`는 리소스가 이미 닫혔다는 신호
   - 종료 순서나 중복 호출을 의심해야 함

3. **작동하는 코드와 비교할 때**
   - 전체 흐름뿐만 아니라 세부 구현까지 비교
   - 특히 리소스 정리 부분은 주의 깊게 확인

4. **공식 문서와 베스트 프랙티스 확인**
   - 단순히 "작동하는 것 같다"가 아니라
   - 공식 문서의 권장 사항 확인

## 결론

- **올바른 방법**: `browser.close()`만 사용
- **문제가 있던 방법**: `context.close()` + `browser.close()` (중복)
- **발견하지 못한 이유**: 
  1. 코드 비교 시 세부 구현까지 비교하지 않음
  2. 에러 발생 전까지 문제 인식 불가
  3. Playwright의 리소스 관리 방식에 대한 이해 부족



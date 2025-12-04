from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import time
import os
import re
from dotenv import load_dotenv

from services.keyword_service import get_keywords
from services.file_service import (
    save_report,
    save_history,
    get_history_numbers
)
from models.announcement_schema import AnnouncementSchema

# 환경변수 로드
load_dotenv()

def run_scraper(keywords=None, request_date=None):
    """
    나라장터 입찰공고 수집 (로컬 파일 저장)
    
    Args:
        keywords: 검색할 키워드 리스트 (없으면 저장된 키워드 사용)
        request_date: 요청일 (기본값: 오늘)
    
    Returns:
        수집된 공고 리스트 (파일로 저장됨)
    """
    if keywords is None or len(keywords) == 0:
        keywords = get_keywords()
    
    if request_date is None:
        request_date = datetime.now()
    
    print(f"총 {len(keywords)}개의 키워드로 수집 시작: {keywords}")
    print(f"요청일: {request_date.strftime('%Y-%m-%d')}")
    
    # 히스토리에서 중복 체크용 공고번호 조회 (요청일 -1일까지)
    print("히스토리 파일에서 중복 체크용 공고번호 조회 중...")
    history_numbers = get_history_numbers(request_date)
    print(f"  히스토리에서 {len(history_numbers)}개의 공고번호 발견")
    
    results = []
    total_saved = 0
    total_duplicates = 0
    
    # 브라우저 실행 및 스크래핑
    with sync_playwright() as p:
        try:
            # 헤드리스 모드 설정 (환경변수 또는 기본값 True)
            # 기본값을 True로 변경하여 브라우저 크래시 방지
            headless_env = os.getenv('PLAYWRIGHT_HEADLESS', 'true').lower()
            headless = headless_env in ('true', '1', 'yes')
            
            print(f"브라우저 실행 중... (Playwright, headless={headless})")
            
            # 다른 프로젝트 로직 적용: Firefox 먼저 시도, 실패 시 Chromium with 크래시 방지 옵션
            try:
                browser = p.firefox.launch(headless=headless)
                print("  ✅ Firefox 브라우저로 실행")
            except Exception as e:
                print(f"  ⚠️  Firefox 실행 실패, Chromium 재시도: {e}")
                # macOS 크래시 방지를 위한 추가 옵션 (다른 프로젝트 로직 적용)
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
                print("  ✅ Chromium 브라우저로 실행 (크래시 방지 옵션 적용)")
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            print("  ✅ 브라우저 컨텍스트 생성 완료")
            
            page = context.new_page()
            print("  ✅ 페이지 생성 완료")
            
            # 1. 나라장터 메인 페이지 접속
            print("\n[1단계] 나라장터 메인 페이지 접속 중...")
            url = "https://www.g2b.go.kr/"
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(3)
            print("  ✅ 메인 페이지 접속 완료")
            
            # 1-1. 팝업 닫기
            print("\n[1-1단계] 팝업 닫기 중...")
            popup_selector = 'div[role="dialog"][aria-modal="true"]'
            if page.locator(popup_selector).count() > 0:
                close_button = page.locator('.w2window_close').first
                if close_button.count() > 0:
                    try:
                        close_button.click(timeout=3000)
                        time.sleep(1)
                    except:
                        page.evaluate("() => { const btn = document.querySelector('.w2window_close'); if (btn) btn.click(); }")
                        time.sleep(1)
            
            # 2. "입찰" 메뉴 클릭
            print("\n[2단계] '입찰' 메뉴 클릭 중...")
            menu_bid_id = 'mf_wfm_gnb_wfm_gnbMenu_wq_uuid_567'
            
            # 페이지 상태 확인
            if page.is_closed():
                raise Exception("페이지가 메뉴 클릭 전에 닫혔습니다")
            
            # 메뉴 요소 존재 확인
            menu_exists = page.evaluate(f"""
                () => {{
                    const el = document.getElementById('{menu_bid_id}');
                    return el !== null;
                }}
            """)
            
            if not menu_exists:
                print("  ⚠️  입찰 메뉴 요소를 찾을 수 없습니다. 페이지 구조가 변경되었을 수 있습니다.")
                # 현재 URL 확인
                current_url = page.url
                print(f"  현재 URL: {current_url}")
            
            page.evaluate(f"""
                () => {{
                    const el = document.getElementById('{menu_bid_id}');
                    if (el) {{
                        el.click();
                    }}
                }}
            """)
            
            # 페이지 로딩 대기
            try:
                page.wait_for_load_state('networkidle', timeout=10000)
            except:
                print("  ⚠️  네트워크 대기 시간 초과 (계속 진행)")
            
            time.sleep(2)
            
            # 페이지 상태 재확인
            if page.is_closed():
                raise Exception("페이지가 입찰 메뉴 클릭 후 닫혔습니다")
            
            print("  ✅ 입찰 메뉴 클릭 완료")
            
            # 3. "입찰공고목록" 서브메뉴 클릭
            print("\n[3단계] '입찰공고목록' 서브메뉴 클릭 중...")
            menu_bid_list_id = 'mf_wfm_gnb_wfm_gnbMenu_genDepth1_1_genDepth2_0_genDepth3_0_btn_menuLvl3'
            
            # 페이지 상태 확인
            if page.is_closed():
                raise Exception("페이지가 서브메뉴 클릭 전에 닫혔습니다")
            
            # 서브메뉴 요소 확인 및 클릭 (다른 프로젝트 방식 적용)
            # JavaScript로 먼저 요소 존재 확인
            menu_info = page.evaluate(f"""
                () => {{
                    const el = document.getElementById('{menu_bid_list_id}');
                    if (el) {{
                        return {{
                            exists: true,
                            tagName: el.tagName,
                            text: el.innerText.trim(),
                            visible: el.offsetParent !== null
                        }};
                    }}
                    return {{ exists: false }};
                }}
            """)
            
            if menu_info and menu_info.get('exists'):
                print(f"  ✅ 입찰공고목록 메뉴 발견!")
                print(f"      태그: {menu_info.get('tagName', 'N/A')}")
                print(f"      텍스트: {menu_info.get('text', 'N/A')[:50]}")
                print(f"      표시 여부: {menu_info.get('visible', False)}")
                
                # 클릭 전 URL 저장
                url_before = page.url
                print(f"  📍 클릭 전 URL: {url_before}")
                
                # 페이지 상태 재확인
                if page.is_closed():
                    raise Exception("페이지가 클릭 전에 닫혔습니다")
                
                # JavaScript로 직접 클릭 (더 안정적)
                js_clicked = page.evaluate(f"""
                    () => {{
                        const el = document.getElementById('{menu_bid_list_id}');
                        if (el) {{
                            el.click();
                            return true;
                        }}
                        return false;
                    }}
                """)
                
                if js_clicked:
                    print(f"  ✅ JavaScript 클릭 성공!")
                    time.sleep(3)  # 페이지 이동 대기
                else:
                    raise Exception(f"입찰공고목록 메뉴 클릭 실패 (ID: {menu_bid_list_id})")
            else:
                print("  ⚠️  입찰공고목록 서브메뉴 요소를 찾을 수 없습니다.")
                print("  ⚠️  페이지 구조가 변경되었거나, 메뉴가 아직 로드되지 않았을 수 있습니다.")
                # 현재 URL 및 페이지 상태 확인
                current_url = page.url
                page_title = page.title()
                print(f"  현재 URL: {current_url}")
                print(f"  페이지 제목: {page_title}")
                print("  ⚠️  추가 대기 후 재시도...")
                time.sleep(5)
                
                # 재확인
                menu_bid_list = page.locator(f'#{menu_bid_list_id}')
                if menu_bid_list.count() > 0:
                    try:
                        menu_bid_list.click(timeout=5000)
                        print(f"  ✅ 재시도 클릭 성공!")
                        time.sleep(3)
                    except:
                        page.evaluate(f"""
                            () => {{
                                const el = document.getElementById('{menu_bid_list_id}');
                                if (el) el.click();
                            }}
                        """)
                        time.sleep(3)
                else:
                    raise Exception(f"입찰공고목록 서브메뉴를 찾을 수 없습니다. 메뉴 ID: {menu_bid_list_id}")
            
            # 페이지 로딩 대기 (중요: 메뉴 클릭 후 페이지 이동 대기)
            try:
                page.wait_for_load_state('networkidle', timeout=20000)
                print("  ✅ 네트워크 로딩 완료")
            except Exception as e:
                print(f"  ⚠️  네트워크 대기 시간 초과: {str(e)}")
                print("  ⚠️  계속 진행하지만 페이지가 완전히 로드되지 않았을 수 있습니다.")
            
            # 페이지 상태 최종 확인
            if page.is_closed():
                raise Exception("페이지가 서브메뉴 클릭 후 닫혔습니다")
            
            # 현재 URL 확인 (페이지 이동 확인)
            current_url = page.url
            print(f"  📍 클릭 후 URL: {current_url}")
            
            if url_before != current_url:
                print("  ✅ URL이 변경되었습니다!")
            else:
                print("  ⚠️ URL이 변경되지 않았습니다. (SPA일 수 있음)")
            
            print("  ✅ 입찰공고목록 메뉴 클릭 완료")
            print("  ✅ 입찰공고목록 페이지 이동 완료!")
            
            # 키워드별로 검색 수행
            for idx, keyword in enumerate(keywords, 1):
                print(f"\n[{idx}/{len(keywords)}] 키워드 '{keyword}'로 검색 중...")
                try:
                    # 첫 번째 키워드에서만 날짜 범위 설정
                    is_first_keyword = (idx == 1)
                    search_results = search_by_keyword(page, keyword, request_date, is_first_keyword=is_first_keyword)
                    print(f"  키워드 '{keyword}' 검색 결과: {len(search_results)}개 공고 발견")
                    
                    keyword_saved = 0
                    keyword_duplicates = 0
                    
                    for announcement in search_results:
                        announcement_number = announcement.get('announcement_number', '')
                        
                        if announcement_number and announcement_number.strip():
                            if announcement_number.strip() in history_numbers:
                                keyword_duplicates += 1
                                continue
                        
                        results.append(announcement)
                        keyword_saved += 1
                        total_saved += 1
                        
                        if announcement_number:
                            history_numbers.add(announcement_number.strip())
                    
                    print(f"  키워드 '{keyword}' 완료: 저장 {keyword_saved}개, 중복 {keyword_duplicates}개")
                    total_duplicates += keyword_duplicates
                    
                except Exception as e:
                    print(f"키워드 '{keyword}' 검색 중 오류: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue
        
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            print(traceback.format_exc())
        finally:
            # 헤드리스 모드가 아닐 때만 브라우저를 열어둠
            if not headless:
                print("\n⏳ 브라우저를 15초간 열어둡니다. 확인해보세요...")
                time.sleep(15)
            browser.close()
            print("\n✅ 브라우저 종료 완료")
    
    # 업무구분 필터링: "일반용역"만 남기기
    print("\n[필터링] 업무구분이 '일반용역'인 공고만 필터링 중...")
    filtered_results = []
    filtered_out_by_business_type = 0
    
    for announcement in results:
        business_type = announcement.get('business_type', '').strip()
        if business_type == '일반용역':
            filtered_results.append(announcement)
        else:
            filtered_out_by_business_type += 1
    
    print(f"  필터링 전: {len(results)}개")
    print(f"  필터링 후: {len(filtered_results)}개 (일반용역만)")
    print(f"  제외된 공고: {filtered_out_by_business_type}개")
    
    # 결과 요약 출력
    print(f"\n=== 수집 완료 ===")
    print(f"총 키워드: {len(keywords)}개")
    print(f"수집된 공고: {total_saved}개")
    print(f"중복 제외: {total_duplicates}개")
    print(f"업무구분 필터링 후: {len(filtered_results)}개")
    
    # 파일로 저장 (필터링된 결과만)
    if filtered_results:
        try:
            report_path = save_report(filtered_results, request_date)
            print(f"  Report 파일 저장: {report_path}")
            
            history_path = save_history(filtered_results, request_date)
            print(f"  History 파일 저장: {history_path}")
        except Exception as e:
            print(f"  파일 저장 중 오류: {str(e)}")
            import traceback
            print(traceback.format_exc())
    return filtered_results

def search_by_keyword(page, keyword, request_date=None, is_first_keyword=False):
    """키워드로 검색하여 공고 수집"""
    results = []
    
    try:
        if page.is_closed():
            raise Exception("페이지가 닫혔습니다")
        
        # 0. 첫 번째 키워드에서만 날짜 범위 설정
        if is_first_keyword:
            print("  날짜 범위 설정 중...")
            
            # 페이지 상태 재확인
            if page.is_closed():
                raise Exception("페이지가 날짜 범위 설정 전에 닫혔습니다")
            
            date_range_id = 'wq_uuid_2223_grpCalRoot'
            
            # JavaScript로 요소 존재 확인 (다른 프로젝트 방식)
            date_range_exists = page.evaluate(f"""
                () => {{
                    const el = document.getElementById('{date_range_id}');
                    return el !== null;
                }}
            """)
            
            if date_range_exists:
                date_range_element = page.locator(f'#{date_range_id}')
                
                try:
                    if date_range_element.count() > 0:
                        # 날짜 범위 계산 (14일 전 ~ 오늘)
                        if request_date is None:
                            request_date = datetime.now()
                        end_date = request_date
                        start_date = end_date - timedelta(days=14)
                        
                        start_date_str = start_date.strftime('%Y%m%d')
                        end_date_str = end_date.strftime('%Y%m%d')
                        
                        # 내부 input 요소 찾기
                        date_inputs = page.evaluate(f"""
                            () => {{
                                const container = document.getElementById('{date_range_id}');
                                if (container) {{
                                    const inputs = container.querySelectorAll('input[type="text"], input[type="date"]');
                                    return Array.from(inputs).map(inp => ({{
                                        id: inp.id || '',
                                        name: inp.name || '',
                                        value: inp.value || ''
                                    }}));
                                }}
                                return [];
                            }}
                        """)
                        
                        if len(date_inputs) >= 1:
                            start_input = page.locator(f'#{date_inputs[0]["id"]}')
                            start_input.fill(start_date_str)
                            time.sleep(0.5)
                        
                        if len(date_inputs) >= 2:
                            end_input = page.locator(f'#{date_inputs[1]["id"]}')
                            end_input.fill(end_date_str)
                            time.sleep(0.5)
                        
                        print(f"  ✅ 날짜 범위 설정 완료: {start_date_str} ~ {end_date_str}")
                    else:
                        print("  ⚠️  날짜 범위 컨테이너를 찾지 못함 (계속 진행)")
                except Exception as e:
                    print(f"  ⚠️  날짜 범위 설정 중 오류: {e} (계속 진행)")
            else:
                print("  ⚠️  날짜 범위 컨테이너를 찾지 못함 (계속 진행)")
        
        # 1. "공고명" 입력 필드에 키워드 입력
        print(f"  공고명 입력 필드에 '{keyword}' 입력 중...")
        time.sleep(2)
        
        # 1-1. 키워드 입력 (Playwright Locator 사용)
        keyword_input_id = 'mf_wfm_container_tacBidPbancLst_contents_tab2_body_bidPbancNm'
        keyword_input = page.locator(f'#{keyword_input_id}')
        
        if keyword_input.count() > 0:
            keyword_input.clear()
            keyword_input.fill(keyword)
            time.sleep(0.5)
            print(f"  ✅ 키워드 '{keyword}' 입력 완료 (Playwright)")
        else:
            # JavaScript fallback
            input_success = page.evaluate("""
                (keyword) => {
                    const input = document.getElementById('mf_wfm_container_tacBidPbancLst_contents_tab2_body_bidPbancNm');
                    if (input) {
                        input.value = '';
                        input.value = keyword;
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                        return input.value === keyword;
                    }
                    return false;
                }
            """, keyword)
            
            if not input_success:
                print(f"  ❌ 검색 입력 필드를 찾을 수 없습니다!")
                return results
            print(f"  ✅ 키워드 '{keyword}' 입력 완료 (JavaScript fallback)")
            time.sleep(0.5)
        
        # 1-2. 결과 개수를 100으로 설정 (검색 전에 설정)
        print("  결과 개수 100으로 설정 중...")
        record_count_select_id = 'mf_wfm_container_tacBidPbancLst_contents_tab2_body_sbxRecordCountPerPage1'
        record_count_select = page.locator(f'#{record_count_select_id}')
        
        if record_count_select.count() > 0:
            record_count_select.select_option("100")
            time.sleep(1)
            print("  ✅ 결과 개수 100으로 설정 완료")
        else:
            # JavaScript fallback
            select_result = page.evaluate("""
                () => {
                    const el = document.getElementById('mf_wfm_container_tacBidPbancLst_contents_tab2_body_sbxRecordCountPerPage1');
                    if (el) {
                        if (el.tagName === 'SELECT') {
                            el.value = '100';
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    }
                }
            """)
            print("  ⚠️  결과 개수 선택 필드를 찾지 못함 (계속 진행)")
        
        # 2. "검색" 버튼 클릭
        print("  검색 버튼 클릭 중...")
        search_button_id = 'mf_wfm_container_tacBidPbancLst_contents_tab2_body_btnS0004'
        search_button = page.locator(f'#{search_button_id}')
        
        if search_button.count() > 0:
            search_button.click(timeout=5000)
            time.sleep(5)
            print("  ✅ 검색 버튼 클릭 완료")
        else:
            # JavaScript fallback
            page.evaluate("""
                () => {
                    const el = document.getElementById('mf_wfm_container_tacBidPbancLst_contents_tab2_body_btnS0004');
                    if (el && !el.disabled) el.click();
                }
            """)
            time.sleep(5)
            print("  ✅ 검색 버튼 클릭 완료 (JavaScript fallback)")
        
        # 3. 검색 결과 로딩 대기
        print("  검색 결과 로딩 대기 중...")
        page.wait_for_load_state('networkidle', timeout=60000)
        time.sleep(5)
        print("  ✅ 검색 결과 로딩 완료")
        
        # 4. 적용 버튼 클릭 (리스트 갱신)
        print("  적용 버튼 클릭 중...")
        apply_button_id = 'mf_wfm_container_tacBidPbancLst_contents_tab2_body_btnAplcn1'
        apply_button = page.locator(f'#{apply_button_id}')
        
        if apply_button.count() > 0:
            apply_button.click()
            page.wait_for_load_state('networkidle', timeout=60000)
            time.sleep(3)
            print("  ✅ 적용 버튼 클릭 완료")
        else:
            # JavaScript fallback
            page.evaluate("""
                () => {
                    const el = document.getElementById('mf_wfm_container_tacBidPbancLst_contents_tab2_body_btnAplcn1');
                    if (el) el.click();
                }
            """)
            page.wait_for_load_state('networkidle', timeout=60000)
            time.sleep(3)
            print("  ✅ 적용 버튼 클릭 완료 (JavaScript fallback)")
        
        # 5. 공고 정보 수집 (링크 기반 추출 시도, 실패 시 테이블 기반)
        print("  공고 정보 수집 중...")
        results = scrape_announcements_from_page(page, request_date)
        print(f"  수집 완료: {len(results)}개 공고")
        
    except Exception as e:
        print(f"키워드 검색 중 오류 발생 ({keyword}): {str(e)}")
        import traceback
        traceback.print_exc()
    
    return results

def parse_publish_date(date_str):
    """
    게시일시 문자열에서 괄호 밖의 날짜만 추출
    
    예: "2025.11.30 10:00 (2025.12.15 18:00)" -> "2025.11.30 10:00"
    """
    if not date_str:
        return None
    
    # 괄호가 있으면 괄호 앞부분만 추출
    if '(' in date_str:
        date_str = date_str.split('(')[0].strip()
    
    # 날짜 파싱 시도 (여러 형식 지원)
    date_formats = [
        '%Y/%m/%d %H:%M',  # "2025/11/28 14:37" 형식 추가
        '%Y/%m/%d',        # "2025/11/28" 형식 추가
        '%Y.%m.%d %H:%M',
        '%Y.%m.%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except:
            continue
    
    return None

def scrape_announcements_from_page(page, request_date=None):
    """
    현재 페이지에서 공고 목록 추출 
    - 업무구분이 '일반용역'인 것만
    - 게시일시가 리포트 생성일 기준 7일 내인 것만
    
    추출 방법:
    1. 링크 기반 추출 (주요 방법)
    2. 테이블 기반 추출 (보조 방법)
    """
    if request_date is None:
        request_date = datetime.now()
    
    announcements = []
    
    try:
        # 방법 1: 링크 기반 추출 (주요 방법)
        print("  링크 기반 추출 시도 중...")
        bids_from_links = page.evaluate("""
            () => {
                const bidNoPattern = /R\\d{2}[A-Z]{2}\\d{8}/;
                const links = Array.from(document.querySelectorAll(
                    'a[href*="bidno"], a[href*="bidPbancNo"], a[href*="coDetail"]'
                ));
                
                const bids = [];
                const seenBidNos = new Set();
                
                // 업무구분 컬럼 인덱스 찾기
                let businessTypeColumnIndex = -1;
                const gridView = document.querySelector('[id*="gridView1"]');
                if (gridView) {
                    const headers = gridView.querySelectorAll('th, .w2grid_header');
                    for (let i = 0; i < headers.length; i++) {
                        const headerText = headers[i].innerText.trim();
                        if (headerText === '업무구분' || headers[i].id && headers[i].id.includes('column27')) {
                            businessTypeColumnIndex = i;
                            break;
                        }
                    }
                }
                
                for (let link of links) {
                    const href = link.getAttribute('href') || '';
                    const match = href.match(bidNoPattern);
                    
                    if (match) {
                        const bidNo = match[0];
                        
                        if (seenBidNos.has(bidNo)) continue;
                        seenBidNos.add(bidNo);
                        
                        // 부모 행 찾기
                        let row = link.closest('tr');
                        if (!row) {
                            row = link.parentElement;
                            while (row && row.tagName !== 'TR') {
                                row = row.parentElement;
                            }
                        }
                        
                        if (!row) continue;
                        
                        // 달력 데이터가 아닌지 확인
                        const rowText = row.innerText.trim();
                        if (rowText.length <= 20 || rowText.match(/\\d{1,2}\\s+\\d{1,2}\\s+\\d{1,2}/)) {
                            continue; // 달력 데이터 제외
                        }
                        
                        const cells = row.querySelectorAll('td');
                        
                        // 업무구분 필터링
                        if (businessTypeColumnIndex >= 0 && businessTypeColumnIndex < cells.length) {
                            const businessTypeCell = cells[businessTypeColumnIndex];
                            const businessType = businessTypeCell ? businessTypeCell.innerText.trim() : '';
                            if (businessType !== '일반용역') {
                                continue; // 일반용역이 아니면 제외
                            }
                        }
                        
                        // 공고 정보 추출
                        let title = '';
                        let agency = '';
                        let publishDate = '';
                        
                        // 공고명 찾기 (보통 링크 텍스트 또는 인접 셀)
                        title = link.innerText.trim() || link.textContent.trim();
                        if (!title || title.length < 5) {
                            // 인접 셀에서 찾기
                            for (let cell of cells) {
                                const cellText = cell.innerText.trim();
                                if (cellText.length > 10 && cellText.length < 200) {
                                    title = cellText;
                                    break;
                                }
                            }
                        }
                        
                        // 기관 정보 찾기
                        for (let i = 0; i < cells.length; i++) {
                            const cellText = cells[i].innerText.trim();
                            if (cellText.length > 5 && cellText.length < 50 && 
                                !cellText.match(/^\\d+$/) && 
                                !cellText.match(/^R\\d{2}[A-Z]{2}\\d{8}$/)) {
                                if (i !== businessTypeColumnIndex) {
                                    agency = cellText;
                                    break;
                                }
                            }
                        }
                        
                        // 게시일시 찾기
                        for (let cell of cells) {
                            const cellText = cell.innerText.trim();
                            if (cellText.match(/\\d{4}\\.\\d{2}\\.\\d{2}/)) {
                                publishDate = cellText.split('(')[0].trim();
                                break;
                            }
                        }
                        
                        if (bidNo && title) {
                            bids.push({
                                '공고번호': bidNo,
                                '공고명': title,
                                '공고일': publishDate,
                                '기관': agency,
                                'link': link.href || ''
                            });
                        }
                    }
                }
                
                return bids;
            }
        """)
        
        if bids_from_links and len(bids_from_links) > 0:
            print(f"  ✅ 링크 기반 추출 성공: {len(bids_from_links)}개 공고 발견")
            # 날짜 필터링 기준 (7일 전)
            date_threshold = request_date - timedelta(days=7)
            filtered_by_date = 0
            
            # 링크 기반 추출 결과를 announcements 형식으로 변환
            for bid in bids_from_links:
                publish_date_str = bid.get('공고일', '')
                publish_date = parse_publish_date(publish_date_str)
                
                # 날짜 필터링 (7일 내 공고만)
                if publish_date:
                    if publish_date < date_threshold:
                        filtered_by_date += 1
                        continue
                
                    # publish_date를 YYYY/MM/DD 형식으로 변환
                    formatted_publish_date = publish_date_str
                    if publish_date:
                        formatted_publish_date = publish_date.strftime('%Y/%m/%d')
                    elif publish_date_str:
                        # 날짜 파싱 실패 시 원본 문자열에서 날짜 부분만 추출
                        date_part = publish_date_str.split()[0] if ' ' in publish_date_str else publish_date_str
                        formatted_publish_date = date_part.split('(')[0].strip()
                    
                    announcement = {
                        'announcement_number': bid.get('공고번호', ''),
                        'title': bid.get('공고명', ''),
                        'agency': bid.get('기관', ''),
                        'publish_date': formatted_publish_date,
                        'business_type': '일반용역',  # 이미 필터링됨
                        'created_at': datetime.now().isoformat(),
                        'source': '나라장터'
                    }
                announcements.append(announcement)
            
            if filtered_by_date > 0:
                print(f"  날짜 필터링으로 제외: {filtered_by_date}개")
        else:
            print("  ⚠️  링크 기반 추출 실패, 테이블 기반 추출 시도 중...")
        
        # 방법 2: 테이블 기반 추출 (보조 방법 또는 링크 기반이 실패한 경우)
        if len(announcements) == 0:
            print("  테이블 기반 추출 시도 중...")
            # 테이블 찾기
            table = page.locator('xpath=//*[@id="mf_wfm_container_tacBidPbancLst_contents_tab2_body_gridView1_body_table"]')
            
            if table.count() == 0:
                print("  경고: 공고 테이블을 찾을 수 없습니다")
                return announcements
            
            rows = table.locator('tbody tr')
            row_count = rows.count()
            print(f"  테이블에서 {row_count}개 행 발견")
            
            # 날짜 필터링 기준 (7일 전)
            date_threshold = request_date - timedelta(days=7)
            print(f"  날짜 필터링 기준: {date_threshold.strftime('%Y-%m-%d')} 이후 공고만 수집")
            
            filtered_by_date = 0
            filtered_by_business_type = 0
            
            for i in range(row_count):
                try:
                    row = rows.nth(i)
                    row_cells = row.locator('td')
                    cell_count = row_cells.count()
                    
                    # 필요한 컬럼만 추출
                    col_2 = ''  # 업무구분
                    col_6 = ''  # 공고번호
                    col_7 = ''  # 공고명
                    col_8 = ''  # 공고기관
                    col_9 = ''  # 게시일시
                    col_16 = ''  # 상세정보 (배정예산, 추정가격 추출용)
                    
                    # 각 컬럼 값 추출
                    if cell_count >= 2:
                        col_2 = row_cells.nth(1).inner_text().strip()  # 업무구분
                    
                    # 업무구분 필터링: "일반용역"만 유지
                    if col_2 != '일반용역':
                        filtered_by_business_type += 1
                        continue
                    
                    if cell_count >= 6:
                        col_6 = row_cells.nth(5).inner_text().strip()  # 공고번호
                    if cell_count >= 7:
                        col_7 = row_cells.nth(6).inner_text().strip()  # 공고명
                    if cell_count >= 8:
                        col_8 = row_cells.nth(7).inner_text().strip()  # 공고기관
                    if cell_count >= 10:
                        col_9 = row_cells.nth(9).inner_text().strip()  # 게시일시 (col_10이 실제 게시일시)
                    if cell_count >= 16:
                        col_16 = row_cells.nth(15).inner_text().strip()  # 상세정보
                    
                    # col_9에서 괄호 밖 날짜만 추출 (게시일시)
                    publish_date_str = col_9
                    if '(' in publish_date_str:
                        publish_date_str = publish_date_str.split('(')[0].strip()
                    
                    publish_date = parse_publish_date(publish_date_str)
                    
                    # 날짜 필터링 (7일 내 공고만)
                    if publish_date:
                        if publish_date < date_threshold:
                            filtered_by_date += 1
                            continue
                    else:
                        print(f"    경고: 행 {i+1}의 게시일시 파싱 실패: '{col_9}'")
                    
                    # col_16에서 배정예산, 추정가격 추출
                    budget_amount = None
                    estimated_price = None
                    
                    if col_16:
                        # 배정예산 추출
                        if '배정예산' in col_16 or '배정 예산' in col_16:
                            budget_match = re.search(r'배정\s*예산\s*:\s*([0-9,]+원)', col_16)
                            if budget_match:
                                budget_str = budget_match.group(1)
                                budget_amount = AnnouncementSchema.parse_budget_string(budget_str)
                        
                        # 추정가격 추출
                        if '추정가격' in col_16 or '추정 가격' in col_16:
                            price_match = re.search(r'추정\s*가격\s*:\s*([0-9,]+원)', col_16)
                            if price_match:
                                price_str = price_match.group(1)
                                estimated_price = AnnouncementSchema.parse_budget_string(price_str)
                    
                    # publish_date를 YYYY/MM/DD 형식으로 변환
                    formatted_publish_date = publish_date_str
                    if publish_date:
                        formatted_publish_date = publish_date.strftime('%Y/%m/%d')
                    elif publish_date_str:
                        # 날짜 파싱 실패 시 원본 문자열에서 날짜 부분만 추출
                        date_part = publish_date_str.split()[0] if ' ' in publish_date_str else publish_date_str
                        formatted_publish_date = date_part.split('(')[0].strip()
                    
                    # 공고 데이터 생성
                    announcement = {
                        'announcement_number': col_6,
                        'title': col_7,
                        'agency': col_8,
                        'publish_date': formatted_publish_date,  # YYYY/MM/DD 형식
                        'budget_amount': budget_amount,
                        'estimated_price': estimated_price,
                        'business_type': col_2,
                        'created_at': datetime.now().isoformat(),
                        'source': '나라장터'
                    }
                    
                    announcements.append(announcement)
                    
                except Exception as e:
                    print(f"  공고 {i+1} 추출 중 오류: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                    continue
            
            print(f"  전체 공고 수집: {len(announcements)}개")
            print(f"  날짜 필터링으로 제외: {filtered_by_date}개")
        
    except Exception as e:
        print(f"페이지에서 공고 추출 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return announcements


from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
from services.keyword_service import get_keywords
from services.file_service import (
    save_report,
    save_history,
    check_duplicate_from_history,
    load_report
)
from models.announcement_schema import AnnouncementSchema
import time

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
    from services.file_service import get_history_numbers
    history_numbers = get_history_numbers(request_date)
    print(f"  히스토리에서 {len(history_numbers)}개의 공고번호 발견")
    
    results = []
    total_saved = 0
    total_duplicates = 0
    
    # 브라우저 실행 및 스크래핑
    with sync_playwright() as p:
        try:
            # 시스템 Chrome 사용 (화면에 표시)
            print("브라우저 실행 중... (시스템 Chrome, 화면에 표시됩니다)")
            browser = p.chromium.launch(
                headless=False,
                channel="chrome",
                slow_mo=50,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                ]
            )
            print("  ✅ 브라우저 실행 성공")
            time.sleep(2)
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                ignore_https_errors=True
            )
            print("  ✅ 브라우저 컨텍스트 생성 완료")
            time.sleep(1)
            
            page = context.new_page()
            print("  ✅ 페이지 생성 완료")
            time.sleep(1)
            
            # 1. 나라장터 메인 페이지 접속
            print("\n[1단계] 나라장터 메인 페이지 접속 중...")
            page.goto('https://www.g2b.go.kr/', timeout=90000, wait_until='domcontentloaded')
            page.wait_for_load_state('networkidle', timeout=60000)
            time.sleep(10)
            print("  ✅ 메인 페이지 접속 완료")
            
            # 2. "입찰" 버튼 클릭 (재시도 로직 포함)
            print("\n[2단계] '입찰' 메뉴 클릭 중...")
            clicked = False
            for retry in range(5):
                clicked = page.evaluate("""
                    () => {
                        const element = document.getElementById('mf_wfm_gnb_wfm_gnbMenu_wq_uuid_570');
                        if (element) {
                            const parent = element.closest('li, a, button');
                            if (parent) {
                                parent.click();
                                return true;
                            }
                            element.click();
                            return true;
                        }
                        return false;
                    }
                """)
                if clicked:
                    break
                if retry < 4:
                    print(f"    재시도 중... ({retry + 1}/5)")
                    time.sleep(2)
            
            if not clicked:
                raise Exception("입찰 메뉴를 찾을 수 없습니다")
            print("  ✅ 입찰 메뉴 클릭 완료")
            time.sleep(3)
            
            # 3. "입찰공고목록" 서브메뉴 클릭
            print("\n[3단계] '입찰공고목록' 서브메뉴 클릭 중...")
            clicked_submenu = page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a'));
                    for (let link of links) {
                        const text = (link.textContent || link.innerText || '').trim();
                        if (text === '입찰공고목록' || (text.includes('입찰공고목록') && text.length < 30)) {
                            link.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            if not clicked_submenu:
                raise Exception("입찰공고목록 메뉴를 찾을 수 없습니다")
            print("  ✅ 입찰공고목록 메뉴 클릭 완료")
            page.wait_for_load_state('networkidle', timeout=60000)
            time.sleep(10)
            print("  ✅ 입찰공고목록 페이지 이동 완료")
            
            # 키워드별로 검색 수행
            for idx, keyword in enumerate(keywords, 1):
                print(f"\n[{idx}/{len(keywords)}] 키워드 '{keyword}'로 검색 중...")
                try:
                    search_results = search_by_keyword(page, keyword, request_date)
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
            error_msg = f"스크래핑 중 오류 발생: {str(e)}"
            print(error_msg)
            import traceback
            print(traceback.format_exc())
            raise Exception(error_msg)
        finally:
            try:
                if context:
                    context.close()
                if browser:
                    browser.close()
            except:
                pass
    
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
    else:
        # 필터링된 결과가 없으면 전체 데이터를 저장 (디버깅용)
        print("\n[디버깅] 필터링된 결과가 없어 전체 데이터를 저장합니다.")
        try:
            report_path = save_report(results, request_date)
            print(f"  Report 파일 저장 (전체 데이터): {report_path}")
        except Exception as e:
            print(f"  파일 저장 중 오류: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    return filtered_results if filtered_results else results

def search_by_keyword(page, keyword, request_date=None):
    """키워드로 검색하여 공고 수집"""
    results = []
    
    try:
        if page.is_closed():
            raise Exception("페이지가 닫혔습니다")
        
        # 1. "공고명" 입력 필드에 키워드 입력
        print(f"  공고명 입력 필드에 '{keyword}' 입력 중...")
        time.sleep(2)
        
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
            raise Exception("공고명 입력 필드를 찾을 수 없습니다")
        print(f"  ✅ 키워드 '{keyword}' 입력 완료")
        time.sleep(2)
        
        # 2. "검색" 버튼 클릭
        # XPath: //*[@id="mf_wfm_container_tacBidPbancLst_contents_tab2_body_btnS0004"]
        print("  검색 버튼 클릭 중...")
        search_button = page.locator('xpath=//*[@id="mf_wfm_container_tacBidPbancLst_contents_tab2_body_btnS0004"]')
        search_button.wait_for(state='visible', timeout=10000)
        search_button.click(timeout=10000)
        print("  ✅ 검색 버튼 클릭 완료")
        
        # 3. 검색 결과가 나타날 때까지 충분히 대기
        print("  검색 결과 로딩 대기 중...")
        
        # 네트워크가 안정될 때까지 대기
        page.wait_for_load_state('networkidle', timeout=60000)
        time.sleep(5)
        
        # 테이블이 업데이트될 때까지 대기
        try:
            page.wait_for_selector('#mf_wfm_container_tacBidPbancLst_contents_tab2_body_gridView1_body_table', timeout=60000, state='attached')
        except:
            pass
        
        # 검색 결과가 완전히 로드될 때까지 충분히 대기 (최소 20초)
        for wait_attempt in range(10):
            time.sleep(2)
            page.wait_for_load_state('networkidle', timeout=30000)
            if wait_attempt % 2 == 0:
                print(f"  검색 결과 대기 중... ({wait_attempt * 2}초 경과)")
        
        print("  ✅ 검색 결과 로딩 완료")
        
        # 7. 결과 개수를 100으로 설정
        print("  결과 개수 100으로 설정 중...")
        select_result = page.evaluate("""
            () => {
                const select = document.getElementById('mf_wfm_container_tacBidPbancLst_contents_tab2_body_sbxRecordCountPerPage1');
                if (select) {
                    select.value = '100';
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                }
                return false;
            }
        """)
        if select_result:
            print("  ✅ 결과 개수 100으로 설정 완료")
            time.sleep(1)
        else:
            print("  ⚠️  결과 개수 선택 필드를 찾지 못함 (계속 진행)")
        
        # 8. "적용" 버튼 클릭
        print("  적용 버튼 클릭 중...")
        apply_clicked = page.evaluate("""
            () => {
                const applyButton = document.getElementById('mf_wfm_container_tacBidPbancLst_contents_tab2_body_btnAplcn1');
                if (applyButton) {
                    applyButton.click();
                    return true;
                }
                return false;
            }
        """)
        if apply_clicked:
            print("  ✅ 적용 버튼 클릭 완료")
            page.wait_for_load_state('networkidle', timeout=60000)
            time.sleep(3)
        else:
            print("  ⚠️  적용 버튼을 찾지 못함 (계속 진행)")
        
        # 9. 테이블에서 공고 정보 수집
        print("  테이블에서 공고 정보 수집 중...")
        
        # 디버깅: 검색 후 입력 필드 값과 첫 번째 공고명 확인
        debug_info = page.evaluate("""
            () => {
                const input = document.getElementById('mf_wfm_container_tacBidPbancLst_contents_tab2_body_bidPbancNm');
                const table = document.getElementById('mf_wfm_container_tacBidPbancLst_contents_tab2_body_gridView1_body_table');
                let firstTitle = '';
                if (table) {
                    const firstRow = table.querySelector('tbody tr');
                    if (firstRow) {
                        const cells = firstRow.querySelectorAll('td');
                        if (cells.length >= 7) {
                            firstTitle = cells[6].innerText.trim();
                        }
                    }
                }
                return {
                    inputValue: input ? input.value : '',
                    firstTitle: firstTitle,
                    rowCount: table ? table.querySelectorAll('tbody tr').length : 0
                };
            }
        """)
        print(f"  [디버깅] 검색 후 상태 - 입력 필드: '{debug_info['inputValue']}', 첫 공고명: '{debug_info['firstTitle'][:50]}', 행 수: {debug_info['rowCount']}")
        
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
    """
    if request_date is None:
        request_date = datetime.now()
    
    announcements = []
    
    try:
        # 테이블 찾기
        table = page.locator('xpath=//*[@id="mf_wfm_container_tacBidPbancLst_contents_tab2_body_gridView1_body_table"]')
        
        if table.count() == 0:
            print("  경고: 공고 테이블을 찾을 수 없습니다")
            return announcements
        
        rows = table.locator('tbody tr')
        row_count = rows.count()
        print(f"  테이블에서 {row_count}개 행 발견")
        
        # 디버깅: 첫 번째 행의 컬럼 수와 각 컬럼 내용 확인
        if row_count > 0:
            first_row = rows.nth(0)
            first_row_cells = first_row.locator('td')
            cell_count = first_row_cells.count()
            print(f"  [디버깅] 첫 번째 행의 컬럼 수: {cell_count}개")
            print(f"  [디버깅] 처음 5개 컬럼 내용:")
            for debug_col in range(min(5, cell_count)):
                try:
                    cell_text = first_row_cells.nth(debug_col).inner_text().strip()
                    print(f"    컬럼 {debug_col+1}: '{cell_text[:30]}'")
                except:
                    pass
            print(f"  [디버깅] 모든 컬럼의 ID 확인:")
            for debug_col in range(min(16, cell_count)):
                try:
                    cell = first_row_cells.nth(debug_col)
                    cell_id = cell.get_attribute('id') or ''
                    cell_text = cell.inner_text().strip()
                    if 'column' in cell_id.lower():
                        print(f"    컬럼 {debug_col+1}: ID='{cell_id}', 텍스트='{cell_text[:30]}'")
                except:
                    pass
        
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
                        import re
                        budget_match = re.search(r'배정\s*예산\s*:\s*([0-9,]+원)', col_16)
                        if budget_match:
                            budget_str = budget_match.group(1)
                            budget_amount = AnnouncementSchema.parse_budget_string(budget_str)
                    
                    # 추정가격 추출
                    if '추정가격' in col_16 or '추정 가격' in col_16:
                        import re
                        price_match = re.search(r'추정\s*가격\s*:\s*([0-9,]+원)', col_16)
                        if price_match:
                            price_str = price_match.group(1)
                            estimated_price = AnnouncementSchema.parse_budget_string(price_str)
                
                # 공고 데이터 생성
                announcement = {
                    'announcement_number': col_6,
                    'title': col_7,
                    'agency': col_8,
                    'publish_date': publish_date_str,  # 괄호 밖 날짜만
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

def extract_text_by_xpath_pattern(row, page, row_index, column_id):
    """
    XPath 패턴을 사용하여 특정 컬럼의 텍스트 추출
    column_id 예: 'column23', 'column21', 'column19'
    """
    try:
        # 방법 1: JavaScript로 직접 XPath 패턴 사용
        text = page.evaluate(f"""
            (rowIndex) => {{
                const table = document.getElementById('mf_wfm_container_tacBidPbancLst_contents_tab2_body_gridView1_body_table');
                if (table) {{
                    const rows = table.querySelectorAll('tbody tr');
                    if (rows[rowIndex]) {{
                        // columnId에 해당하는 요소 찾기 (예: column23)
                        const columnId = '{column_id}';
                        const cellId = `mf_wfm_container_tacBidPbancLst_contents_tab2_body_gridView1_${{columnId}}`;
                        const cell = rows[rowIndex].querySelector(`[id*="${{columnId}}"]`);
                        if (cell) {{
                            return cell.innerText.trim();
                        }}
                        // 또는 td 요소들 중에서 찾기
                        const cells = rows[rowIndex].querySelectorAll('td');
                        for (let cell of cells) {{
                            if (cell.id && cell.id.includes(columnId)) {{
                                return cell.innerText.trim();
                            }}
                        }}
                    }}
                }}
                return '';
            }}
        """, row_index)
        
        if text:
            return text
        
        # 방법 2: 컬럼 인덱스로 시도 (column23이면 23번째 컬럼)
        # 하지만 실제 테이블은 16개 컬럼만 있으므로 이 방법은 작동하지 않을 수 있음
        column_num = int(column_id.replace('column', ''))
        if column_num <= 16:  # 실제 컬럼 수 확인
            cell = row.locator('td').nth(column_num - 1)  # 0-based index
            if cell.count() > 0:
                text = cell.inner_text().strip()
                if text:
                    return text
                
    except Exception as e:
        print(f"    {column_id} 추출 실패: {str(e)}")
    return ''

def extract_text_from_row(row, column_index):
    """테이블 행에서 특정 컬럼의 텍스트 추출"""
    try:
        cell = row.locator('td').nth(column_index - 1)  # 0-based index
        if cell.count() > 0:
            text = cell.inner_text().strip()
            return text
    except Exception as e:
        print(f"    컬럼 {column_index} 추출 실패: {str(e)}")
    return ''

def extract_business_type_from_row(row, page, row_index):
    """
    업무구분 컬럼 추출 (XPath 사용)
    XPath: //*[@id="mf_wfm_container_tacBidPbancLst_contents_tab2_body_gridView1_column27"]
    """
    try:
        # 방법 1: 행 내에서 컬럼 인덱스로 찾기 (27번째 컬럼)
        cell = row.locator('td').nth(26)  # 0-based index (27-1=26)
        if cell.count() > 0:
            text = cell.inner_text().strip()
            if text:
                return text
        
        # 방법 2: XPath로 직접 찾기 (각 행의 해당 컬럼)
        # 테이블 내에서 해당 행의 업무구분 컬럼 찾기
        business_type_element = page.locator(f'xpath=//*[@id="mf_wfm_container_tacBidPbancLst_contents_tab2_body_gridView1_body_table"]/tbody/tr[{row_index + 1}]/td[27]')
        if business_type_element.count() > 0:
            text = business_type_element.first.inner_text().strip()
            if text:
                return text
        
        # 방법 3: JavaScript로 찾기
        business_type_text = page.evaluate("""
            (rowIndex) => {
                const table = document.getElementById('mf_wfm_container_tacBidPbancLst_contents_tab2_body_gridView1_body_table');
                if (table) {
                    const rows = table.querySelectorAll('tbody tr');
                    if (rows[rowIndex]) {
                        const cells = rows[rowIndex].querySelectorAll('td');
                        if (cells[26]) { // 27번째 컬럼 (0-based index 26)
                            return cells[26].innerText.trim();
                        }
                    }
                }
                return '';
            }
        """, row_index)
        
        if business_type_text:
            return business_type_text
            
    except Exception as e:
        print(f"    업무구분 추출 실패 (행 {row_index + 1}): {str(e)}")
    return ''

def extract_text_from_row_with_xpath(row, page, column_index):
    """
    테이블 행에서 특정 컬럼의 텍스트 추출 (XPath 사용)
    게시일시 컬럼의 경우 /div/div 구조를 고려
    """
    try:
        # 먼저 일반적인 방법으로 시도
        cell = row.locator('td').nth(column_index - 1)
        if cell.count() > 0:
            # 게시일시 컬럼(15)의 경우 div/div 구조 확인
            if column_index == 15:
                div_elements = cell.locator('div div')
                if div_elements.count() > 0:
                    text = div_elements.first.inner_text().strip()
                    if text:
                        return text
            # 일반적인 경우
            text = cell.inner_text().strip()
            return text
    except Exception as e:
        print(f"    컬럼 {column_index} 추출 실패: {str(e)}")
    return ''

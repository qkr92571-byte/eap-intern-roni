"""
나라장터 공공데이터개방표준서비스 API 클라이언트
낙찰정보 조회 및 경쟁사 동향 분석
"""

import requests
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# API 기본 설정
BASE_URL = "https://apis.data.go.kr/1230000/ao/PubDataOpnStdService"
API_KEY = os.getenv('NARA_API_KEY', '87a54a268c537024c6f623556aa7c98ed85e81021d6442d64fc90ff91071f568')

class NaraAPIService:
    """나라장터 Open API 서비스 클래스"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        초기화
        
        Args:
            api_key: API 인증키 (없으면 환경변수에서 가져옴)
        """
        self.api_key = api_key or API_KEY
        self.base_url = BASE_URL
    
    def _make_request(self, operation: str, params: Dict) -> Dict:
        """
        API 요청 실행
        
        Args:
            operation: 서비스명 (예: getBidPblancListInfo)
            params: 요청 파라미터
            
        Returns:
            API 응답 데이터
        """
        # 공공데이터포털 표준 구조: base_url/operation
        url = f"{self.base_url}/{operation}"
        
        # 기본 파라미터 설정
        request_params = {
            'serviceKey': self.api_key,
            'numOfRows': params.get('numOfRows', 100),
            'pageNo': params.get('pageNo', 1),
            'type': params.get('type', 'json')  # 공공데이터포털 표준: 'type' 파라미터 사용
        }
        
        # 추가 파라미터 병합 (기본 파라미터와 중복되지 않도록)
        for key, value in params.items():
            if key not in ['numOfRows', 'pageNo', 'type']:
                request_params[key] = value
        
        try:
            response = requests.get(url, params=request_params, timeout=30)
            
            # 디버깅: 응답 상태 및 내용 확인
            print(f"[DEBUG] API 요청 URL: {url}")
            print(f"[DEBUG] 요청 파라미터: {request_params}")
            print(f"[DEBUG] 응답 상태 코드: {response.status_code}")
            
            if response.status_code != 200:
                print(f"[DEBUG] 응답 내용: {response.text[:500]}")
                raise Exception(f"API 요청 실패: HTTP {response.status_code} - {response.text[:200]}")
            
            data = response.json()
            print(f"[DEBUG] 응답 데이터 키: {list(data.keys())}")
            
            # 응답 구조 확인 및 반환
            if 'response' in data:
                if 'body' in data['response']:
                    body = data['response']['body']
                    # items 또는 item 필드 확인
                    if 'items' in body:
                        print(f"[DEBUG] items 타입: {type(body['items'])}, 개수: {len(body['items']) if isinstance(body['items'], list) else 'N/A'}")
                    elif 'item' in body:
                        print(f"[DEBUG] item 타입: {type(body['item'])}, 개수: {len(body['item']) if isinstance(body['item'], list) else 1}")
                    return body
                return data['response']
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"API 요청 오류: {str(e)}")
            raise Exception(f"API 요청 실패: {str(e)}")
    
    def get_award_info(self, 
                      start_datetime: Optional[str] = None,
                      end_datetime: Optional[str] = None,
                      business_div_code: Optional[str] = None,
                      num_of_rows: int = 100,
                      page_no: int = 1) -> Dict:
        """
        낙찰정보 조회 (개찰일시 기준)
        
        Args:
            start_datetime: 시작일시 (YYYYMMDDHHMM 형식, 예: 202412010000)
            end_datetime: 종료일시 (YYYYMMDDHHMM 형식, 예: 202412072359)
            business_div_code: 업무구분코드 (1: 물품, 2: 외자, 3: 공사, 5: 용역)
            num_of_rows: 한 페이지 결과 수
            page_no: 페이지 번호
            
        Returns:
            낙찰정보 리스트
            
        Note:
            개찰일시 범위는 1주일로 제한됨
        """
        # 날짜 기본값 설정 (최근 1주일)
        if not end_datetime:
            end_datetime = datetime.now().strftime('%Y%m%d2359')
        if not start_datetime:
            start_datetime = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d0000')
        
        params = {
            'numOfRows': num_of_rows,
            'pageNo': page_no,
            'type': 'json',
            'opengBgnDt': start_datetime,
            'opengEndDt': end_datetime
        }
        
        # 업무구분코드가 있으면 추가 (없으면 전체)
        if business_div_code:
            params['bsnsDivCd'] = business_div_code
        
        # 낙찰정보 조회 API 호출
        # operation명: getDataSetOpnStdScsbidInfo (데이터셋 개방표준에 따른 낙찰정보)
        result = self._make_request('getDataSetOpnStdScsbidInfo', params)
        return result
    
    def get_award_info_by_keyword(self, 
                                  keyword: str,
                                  days: int = 30,
                                  business_div_code: Optional[str] = None) -> List[Dict]:
        """
        키워드로 낙찰정보 조회 (여러 주차 자동 처리)
        
        Args:
            keyword: 검색 키워드 (낙찰자명, 공고명 등)
            days: 조회할 일수
            business_div_code: 업무구분코드 (1: 물품, 2: 외자, 3: 공사, 5: 용역, None: 전체)
            
        Returns:
            낙찰정보 리스트 (키워드로 필터링된 결과)
            
        Note:
            개찰일시 범위가 1주일로 제한되어 있어, 여러 주차로 나누어 조회함
        """
        all_results = []
        
        # 시작일과 종료일 계산
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 1주일씩 나누어 조회 (개찰일시 범위 제한)
        current_start = start_date
        week_count = 0
        
        while current_start < end_date:
            week_count += 1
            # 현재 주차의 종료일 (1주일 후 또는 전체 종료일 중 작은 값)
            current_end = min(current_start + timedelta(days=7), end_date)
            
            # 개찰일시 형식으로 변환 (YYYYMMDDHHMM)
            start_datetime = current_start.strftime('%Y%m%d0000')
            end_datetime = current_end.strftime('%Y%m%d2359')
            
            print(f"[{week_count}주차] {start_datetime} ~ {end_datetime} 조회 중...")
            
            page_no = 1
            week_results = []
            
            while True:
                try:
                    result = self.get_award_info(
                        start_datetime=start_datetime,
                        end_datetime=end_datetime,
                        business_div_code=business_div_code,
                        num_of_rows=100,
                        page_no=page_no
                    )
                    
                    # 결과 추출 (응답 구조: response.body.items는 배열)
                    items = []
                    if 'items' in result:
                        items = result['items'] if isinstance(result['items'], list) else [result['items']]
                    elif isinstance(result, list):
                        items = result
                    elif 'item' in result:
                        items = [result['item']] if isinstance(result['item'], dict) else result['item']
                    
                    if not items or len(items) == 0:
                        break
                    
                    # 키워드로 필터링 (낙찰자명, 공고명 등에 포함되는지 확인)
                    filtered_items = []
                    for item in items:
                        # 다양한 필드에서 키워드 검색
                        search_fields = [
                            item.get('bidNtceNm', ''),  # 입찰공고명
                            item.get('ntceInsttNm', ''),  # 공고기관명
                            item.get('fnlSucsfCorpNm', ''),  # 최종낙찰자명
                            item.get('bidprcCorpNm', ''),  # 입찰가 제시 업체명
                            item.get('bidNtceNo', ''),  # 입찰공고번호
                        ]
                        
                        # 키워드가 어느 필드에든 포함되어 있으면 포함
                        if any(keyword.lower() in str(field).lower() for field in search_fields if field):
                            filtered_items.append(item)
                    
                    week_results.extend(filtered_items)
                    
                    # 전체 결과 수 확인
                    total_count = result.get('totalCount', 0)
                    if len(week_results) >= total_count or page_no * 100 >= total_count:
                        break
                    
                    page_no += 1
                    
                except Exception as e:
                    print(f"  페이지 {page_no} 조회 중 오류: {str(e)}")
                    break
            
            all_results.extend(week_results)
            print(f"  [{week_count}주차] {len(week_results)}건 발견 (누적: {len(all_results)}건)")
            
            # 다음 주차로 이동
            current_start = current_end
        
        print(f"\n총 {week_count}주차 조회 완료: {len(all_results)}건")
        return all_results
    
    def analyze_competitor_trends(self, 
                                 keywords: List[str],
                                 days: int = 30) -> Dict:
        """
        경쟁사 동향 분석
        
        Args:
            keywords: 분석할 키워드 리스트 (예: ['EAP', '직원지원프로그램', '상담'])
            days: 분석 기간 (일수)
            
        Returns:
            분석 결과 딕셔너리
        """
        analysis_result = {
            'period': {
                'start_date': (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                'end_date': datetime.now().strftime('%Y-%m-%d'),
                'days': days
            },
            'keywords': keywords,
            'total_awards': 0,
            'awards_by_keyword': {},
            'top_agencies': {},
            'top_companies': {},
            'awards': []
        }
        
        for keyword in keywords:
            print(f"키워드 '{keyword}'로 낙찰정보 조회 중...")
            awards = self.get_award_info_by_keyword(keyword, days=days)
            
            analysis_result['awards_by_keyword'][keyword] = len(awards)
            analysis_result['total_awards'] += len(awards)
            analysis_result['awards'].extend(awards)
            
            # 기관별 통계
            for award in awards:
                agency = award.get('ntceInsttNm', '') or award.get('orgNm', '')
                company = award.get('bidNtceNm', '') or award.get('bidNtceNm', '')
                
                if agency:
                    analysis_result['top_agencies'][agency] = analysis_result['top_agencies'].get(agency, 0) + 1
                
                if company:
                    analysis_result['top_companies'][company] = analysis_result['top_companies'].get(company, 0) + 1
        
        # 상위 기관 및 업체 정렬
        analysis_result['top_agencies'] = dict(
            sorted(analysis_result['top_agencies'].items(), 
                  key=lambda x: x[1], reverse=True)[:10]
        )
        analysis_result['top_companies'] = dict(
            sorted(analysis_result['top_companies'].items(), 
                  key=lambda x: x[1], reverse=True)[:10]
        )
        
        return analysis_result


def get_nara_api_service() -> NaraAPIService:
    """NaraAPIService 인스턴스 반환"""
    return NaraAPIService()


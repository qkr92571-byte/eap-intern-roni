#!/usr/bin/env python3
"""
경쟁사 동향 파악용 낙찰정보 수집 스크립트

- 나라장터 데이터셋 개방표준 낙찰정보 Open API(getDataSetOpnStdScsbidInfo) 사용
- 1주일 단위로 끊어서 2025-11-01 ~ 2025-11-30 구간의 데이터를 수집
- fnlSucsfCorpNm(최종낙찰자명)에 특정 키워드가 포함된 공고만 필터링
- 결과는 backend/competitor_reports 폴더에 JSON 파일로 저장
"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

# 나라장터 Open API 기본 설정
BASE_URL = "https://apis.data.go.kr/1230000/ao/PubDataOpnStdService"
OPERATION = "getDataSetOpnStdScsbidInfo"

# 환경변수에서 인증키 로드 (필수)
API_KEY = os.getenv("NARA_API_KEY")

# 업무구분코드: 5 = 용역
BSNS_DIV_CD = "5"

# 리포트 저장 디렉토리
BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "competitor_reports"

# 진행 상황 저장 디렉토리
PROGRESS_DIR = REPORT_DIR / ".progress"

# 대상 기간
START_DATE_STR = "2025-11-01"
END_DATE_STR = "2025-11-30"

# 필터링할 경쟁사 키워드 목록 (fnlSucsfCorpNm 에 포함 여부로 판단)
# 주의: "다인"은 자주 쓰이는 단어라 수동 검수 필요 (다인피아이디, 다인씨엠건축사사무소, 다인시스 등 제외 필요)
COMPETITOR_KEYWORDS = ["휴노", "다인", "마음의 숲", "이지앤"]

# 제외할 회사명 키워드 (경쟁사 키워드에 매칭되지만 실제 경쟁사가 아닌 경우)
EXCLUDED_COMPANIES = ["다인시스", "다인피아이디", "다인씨엠건축사사무소"]


def ensure_report_dir() -> None:
    """리포트 저장 디렉토리 생성"""
    if not REPORT_DIR.exists():
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if not PROGRESS_DIR.exists():
        PROGRESS_DIR.mkdir(parents=True, exist_ok=True)


def build_datetime_range(start_date: datetime, end_date: datetime) -> (str, str):
    """
    날짜를 Open API 개찰일시 형식(YYYYMMDDHHMM)으로 변환
    - 시작: 00:00
    - 종료: 23:59
    """
    openg_bgn = start_date.strftime("%Y%m%d") + "0000"
    openg_end = end_date.strftime("%Y%m%d") + "2359"
    return openg_bgn, openg_end


def save_progress(start_date: datetime, end_date: datetime, page_no: int, items: List[Dict[str, Any]]) -> None:
    """진행 상황 저장"""
    ensure_report_dir()
    progress_file = PROGRESS_DIR / f"progress_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
    
    progress_data = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "last_page": page_no,
        "collected_count": len(items),
        "last_updated": datetime.now().isoformat(),
    }
    
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(progress_data, f, ensure_ascii=False, indent=2)


def load_progress(start_date: datetime, end_date: datetime) -> Optional[int]:
    """진행 상황 로드 (마지막 페이지 번호 반환)"""
    progress_file = PROGRESS_DIR / f"progress_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
    
    if not progress_file.exists():
        return None
    
    try:
        with open(progress_file, "r", encoding="utf-8") as f:
            progress_data = json.load(f)
        return progress_data.get("last_page")
    except:
        return None


def clear_progress(start_date: datetime, end_date: datetime) -> None:
    """진행 상황 파일 삭제"""
    progress_file = PROGRESS_DIR / f"progress_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
    if progress_file.exists():
        progress_file.unlink()


def fetch_awards_for_range(
    start_date: datetime, 
    end_date: datetime, 
    resume: bool = True,
    max_retries: int = 3,
    timeout: int = 60,
    request_delay: float = 0.5
) -> List[Dict[str, Any]]:
    """
    주어진 기간(최대 7일)에 대한 낙찰정보 전체 조회
    
    Args:
        start_date: 시작 날짜
        end_date: 종료 날짜
        resume: 이전 진행 상황부터 이어서 진행할지 여부
        max_retries: 최대 재시도 횟수
        timeout: 타임아웃 시간 (초)
        request_delay: 요청 간 딜레이 (초)
    """
    if not API_KEY:
        raise RuntimeError("NARA_API_KEY 환경변수가 설정되어 있지 않습니다.")

    openg_bgn, openg_end = build_datetime_range(start_date, end_date)

    print(f"\n📅 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    print(f"   개찰일시 범위: {openg_bgn} ~ {openg_end}")

    url = f"{BASE_URL}/{OPERATION}"

    all_items: List[Dict[str, Any]] = []
    page_no = 1
    page_size = 100
    
    # 이어서 진행하기
    if resume:
        last_page = load_progress(start_date, end_date)
        if last_page:
            page_no = last_page + 1
            print(f"   🔄 이전 진행 상황 발견: {last_page}페이지까지 완료, {page_no}페이지부터 재개")

    while True:
        params = {
            "serviceKey": API_KEY,
            "numOfRows": page_size,
            "pageNo": page_no,
            "type": "json",
            "bsnsDivCd": BSNS_DIV_CD,
            "opengBgnDt": openg_bgn,
            "opengEndDt": openg_end,
        }

        retry_count = 0
        success = False
        
        while retry_count < max_retries:
            try:
                # 요청 간 딜레이 (첫 요청 제외)
                if page_no > 1 or retry_count > 0:
                    time.sleep(request_delay)
                
                resp = requests.get(url, params=params, timeout=timeout)
                
                if resp.status_code != 200:
                    print(f"   ⚠️  HTTP {resp.status_code} 오류: {resp.text[:200]}")
                    break

                data = resp.json()

                # 에러 응답 처리
                if "nkoneps.com.response.ResponseError" in data:
                    err = data["nkoneps.com.response.ResponseError"]["header"]
                    print(f"   ⚠️  API 오류: {err.get('resultMsg')} (코드: {err.get('resultCode')})")
                    break

                if "response" not in data or "body" not in data["response"]:
                    print("   ⚠️  응답 구조가 예상과 다릅니다.")
                    break

                body = data["response"]["body"]
                total_count = int(body.get("totalCount", 0) or 0)

                items: List[Dict[str, Any]] = []
                raw_items = body.get("items")

                # 샘플 응답 기준: items는 리스트
                if isinstance(raw_items, list):
                    items = raw_items
                elif isinstance(raw_items, dict):
                    # 문서 상 예시: items: { item: {...} }
                    item = raw_items.get("item")
                    if isinstance(item, list):
                        items = item
                    elif isinstance(item, dict):
                        items = [item]

                if not items:
                    print("   ℹ️  더 이상 데이터가 없습니다.")
                    success = True
                    break

                all_items.extend(items)

                # 진행 상황 저장 (매 10페이지마다)
                if page_no % 10 == 0:
                    save_progress(start_date, end_date, page_no, all_items)

                print(
                    f"   페이지 {page_no} 처리: {len(items)}건 (누적 {len(all_items)} / 총 {total_count}건)"
                )

                if len(all_items) >= total_count:
                    success = True
                    # 완료 시 진행 상황 파일 삭제
                    clear_progress(start_date, end_date)
                    break

                success = True
                break

            except requests.exceptions.Timeout:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"   ⚠️  타임아웃 발생 (재시도 {retry_count}/{max_retries})...")
                    time.sleep(2 * retry_count)  # 재시도 간 대기 시간 증가
                else:
                    print(f"   ❌ 타임아웃: {max_retries}회 재시도 후 실패")
                    # 진행 상황 저장
                    save_progress(start_date, end_date, page_no - 1, all_items)
                    print(f"   💾 진행 상황 저장: {page_no - 1}페이지까지 완료")
                    return all_items
                    
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"   ⚠️  오류 발생 (재시도 {retry_count}/{max_retries}): {str(e)}")
                    time.sleep(2 * retry_count)
                else:
                    print(f"   ❌ 요청 중 오류: {str(e)}")
                    # 진행 상황 저장
                    save_progress(start_date, end_date, page_no - 1, all_items)
                    print(f"   💾 진행 상황 저장: {page_no - 1}페이지까지 완료")
                    return all_items
        
        if not success:
            break

        page_no += 1

    # 최종 진행 상황 저장
    if all_items:
        save_progress(start_date, end_date, page_no - 1, all_items)

    return all_items


def filter_competitor_awards(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    fnlSucsfCorpNm 에 경쟁사 키워드가 포함된
    "최종 낙찰자(Y)" 정보만 간단한 형태로 필터링

    - 한 공고에 여러 입찰자가 있을 수 있지만,
      여기서는 최종 낙찰 정보(수의 'Y')만 사용
    - 결과 스키마는 report_YYMMDD.json 과 비슷한 단순 구조로 정리
    """
    filtered: List[Dict[str, Any]] = []

    for item in items:
        corp_name = (item.get("fnlSucsfCorpNm") or "").strip()
        if not corp_name:
            continue

        # 최종 낙찰 건만 사용 (sucsfYn == 'Y' 또는 opengRank == '1')
        sucsf_yn = (item.get("sucsfYn") or "").upper()
        openg_rank = (item.get("opengRank") or "").strip()
        if sucsf_yn != "Y" and openg_rank not in ("1", "01"):
            continue

        # 경쟁사 키워드 포함 여부
        if not any(keyword in corp_name for keyword in COMPETITOR_KEYWORDS):
            continue
        
        # 제외할 회사명 필터링 (다인시스 등)
        if any(excluded in corp_name for excluded in EXCLUDED_COMPANIES):
            continue

        # report_YYMMDD.json 과 비슷한 단순 스키마로 매핑
        # (필요한 정보만 추출)
        simplified = {
            "announcement_number": item.get("bidNtceNo", ""),   # 입찰공고번호
            "title": item.get("bidNtceNm", ""),                 # 입찰공고명
            "agency": item.get("ntceInsttNm", ""),              # 공고기관명
            "business_type": item.get("bsnsDivNm", ""),         # 업무구분명
            "publish_date": item.get("fnlSucsfDate") or item.get("opengDate", ""),  # 최종낙찰일 또는 개찰일
            "final_amount": item.get("fnlSucsfAmt", ""),        # 최종낙찰금액
            "winner": corp_name,                                # 최종낙찰자명
        }

        filtered.append(simplified)

    return filtered


def save_weekly_report(
    start_date: datetime, end_date: datetime, items: List[Dict[str, Any]]
) -> None:
    """
    주차별 리포트를 JSON 파일로 저장
    """
    ensure_report_dir()

    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")

    filename = f"competitor_awards_{start_str}_{end_str}.json"
    filepath = REPORT_DIR / filename

    report = {
        "period": {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
        },
        "generated_at": datetime.now().isoformat(),
        "keywords": COMPETITOR_KEYWORDS,
        "total_awards": len(items),
        "items": items,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"   💾 리포트 저장 완료: {filepath}")


def collect_competitor_awards(resume: bool = True) -> None:
    """
    2025-11-01 ~ 2025-11-30 구간을 1주일 단위로 끊어서
    경쟁사 키워드가 포함된 낙찰정보 리포트 생성
    
    Args:
        resume: 이전 진행 상황부터 이어서 진행할지 여부
    """
    if not API_KEY:
        print("❌ NARA_API_KEY 환경변수가 설정되어 있지 않습니다.")
        print("   .env 파일 또는 환경변수에 NARA_API_KEY를 설정해주세요.")
        return

    print("=" * 80)
    print("경쟁사 동향 파악용 낙찰정보 수집")
    print("=" * 80)
    if resume:
        print("   🔄 이어서 진행 모드: 이전 진행 상황부터 재개합니다")
    print()

    start_date = datetime.strptime(START_DATE_STR, "%Y-%m-%d")
    end_date = datetime.strptime(END_DATE_STR, "%Y-%m-%d")

    current_start = start_date
    week_index = 0

    while current_start <= end_date:
        week_index += 1
        current_end = current_start + timedelta(days=6)
        if current_end > end_date:
            current_end = end_date

        print(f"\n[{week_index}주차] {current_start.strftime('%Y-%m-%d')} ~ {current_end.strftime('%Y-%m-%d')}")

        # 1주일 데이터 수집
        all_items = fetch_awards_for_range(current_start, current_end, resume=resume)
        print(f"   전체 낙찰정보: {len(all_items)}건")

        # 경쟁사 키워드 필터링
        competitor_items = filter_competitor_awards(all_items)
        print(f"   경쟁사 키워드 매칭: {len(competitor_items)}건")

        # 리포트 저장
        save_weekly_report(current_start, current_end, competitor_items)
        
        # 완료 시 진행 상황 파일 삭제
        clear_progress(current_start, current_end)

        # 다음 주차로 이동
        current_start = current_end + timedelta(days=1)

    print("\n" + "=" * 80)
    print("전체 기간 수집 및 리포트 생성 완료")
    print("=" * 80)


if __name__ == "__main__":
    collect_competitor_awards()



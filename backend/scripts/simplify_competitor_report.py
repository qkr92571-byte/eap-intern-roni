#!/usr/bin/env python3
"""
경쟁사 리포트를 간단한 양식으로 변환
- 한 공고에 여러 입찰자가 있어도 최종 낙찰자만 남김
- report_YYMMDD.json 형태로 정리
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "competitor_reports"


def simplify_competitor_report(input_file: Path) -> List[Dict[str, Any]]:
    """
    경쟁사 리포트를 간단한 양식으로 변환
    
    Args:
        input_file: 원본 리포트 JSON 파일 경로
        
    Returns:
        간단한 양식의 공고 목록 (배열)
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    items = data.get('items', [])
    
    # 공고번호별로 그룹화 (같은 공고의 여러 입찰자 row를 묶음)
    grouped_by_notice = {}
    
    for item in items:
        notice_no = item.get('bidNtceNo', '')
        if not notice_no:
            continue
        
        # 최종 낙찰자만 필터링
        sucsf_yn = (item.get('sucsfYn') or '').upper()
        openg_rank = str(item.get('opengRank', '')).strip()
        fnl_corp = (item.get('fnlSucsfCorpNm') or '').strip()
        
        # 최종 낙찰 조건: sucsfYn == 'Y' 또는 opengRank == '1'
        is_final_winner = (sucsf_yn == 'Y') or (openg_rank in ('1', '01'))
        
        if not is_final_winner or not fnl_corp:
            continue
        
        # 같은 공고번호가 이미 있으면 스킵 (중복 제거)
        # 단, 이미 저장된 것보다 더 확실한 낙찰 정보가 있으면 교체
        if notice_no not in grouped_by_notice:
            grouped_by_notice[notice_no] = item
        else:
            # 기존 항목과 비교하여 더 확실한 낙찰 정보 선택
            existing = grouped_by_notice[notice_no]
            existing_sucsf = (existing.get('sucsfYn') or '').upper()
            existing_rank = str(existing.get('opengRank', '')).strip()
            
            # 현재 항목이 더 확실한 낙찰 정보인 경우 교체
            if (sucsf_yn == 'Y' and existing_sucsf != 'Y') or \
               (openg_rank in ('1', '01') and existing_rank not in ('1', '01')):
                grouped_by_notice[notice_no] = item
    
    # 간단한 양식으로 변환
    simplified = []
    
    for item in grouped_by_notice.values():
        # 날짜 형식 변환 (YYYY-MM-DD -> YYYY/MM/DD)
        fnl_date = item.get('fnlSucsfDate', '')
        openg_date = item.get('opengDate', '')
        
        publish_date = fnl_date if fnl_date else openg_date
        if publish_date and '-' in publish_date:
            publish_date = publish_date.replace('-', '/')
        
        # 금액 변환 (문자열 -> 숫자)
        def parse_amount(value):
            if not value:
                return None
            try:
                return int(str(value).replace(',', ''))
            except (ValueError, TypeError):
                return None
        
        simplified_item = {
            "announcement_number": item.get('bidNtceNo', ''),
            "title": item.get('bidNtceNm', ''),
            "agency": item.get('ntceInsttNm', ''),
            "publish_date": publish_date or '',
            "budget_amount": parse_amount(item.get('bssAmt')) or parse_amount(item.get('rsrvtnPrce')) or None,
            "estimated_price": parse_amount(item.get('presmptPrce')) or None,
            "business_type": item.get('bsnsDivNm', ''),
            "final_amount": parse_amount(item.get('fnlSucsfAmt')) or None,
            "winner": item.get('fnlSucsfCorpNm', ''),
            "created_at": data.get('generated_at', datetime.now().isoformat()),
            "source": "나라장터 낙찰정보"
        }
        
        simplified.append(simplified_item)
    
    return simplified


def main():
    """메인 실행 함수"""
    # 원본 파일 사용 (백업된 파일)
    input_file = REPORT_DIR / "competitor_awards_20251101_20251107_original.json"
    
    if not input_file.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {input_file}")
        return
    
    print(f"📄 파일 읽는 중: {input_file.name}")
    
    simplified = simplify_competitor_report(input_file)
    
    print(f"✅ 변환 완료: {len(simplified)}건 (최종 낙찰자만)")
    
    # 출력 파일명 (원본과 구분)
    output_file = REPORT_DIR / "competitor_awards_20251101_20251107_simplified.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(simplified, f, ensure_ascii=False, indent=2)
    
    print(f"💾 저장 완료: {output_file.name}")
    
    # 샘플 출력
    if simplified:
        print("\n[샘플 데이터 1건]:")
        print(json.dumps(simplified[0], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


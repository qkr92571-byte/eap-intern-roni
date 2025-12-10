"""
적합 판정 받은 공고들의 첨부파일 조사 및 서비스 항목 수집 스크립트

워크플로우:
1. 리포트 파일에서 적합(approved) 판정 받은 공고 조회
2. 각 공고의 첨부파일 다운로드 및 분석
3. 서비스 항목 추출
4. 리포트 JSON 업데이트
5. Firestore 업데이트
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 프로젝트 루트 경로 추가
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from services.file_service import load_report, REPORT_DIR, get_date_string
from services.attachment_service import analyze_attachments
from services.quote_service import generate_service_list
from services.firebase_service import init_firebase, update_announcement_by_number

def parse_service_list_markdown(md_path: Path) -> List[Dict[str, str]]:
    """
    service_list 마크다운 파일을 파싱하여 서비스 항목 리스트 반환
    """
    service_items = []
    
    if not md_path.exists():
        return service_items
    
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # "## 요구 서비스 항목" 섹션 찾기
            if "## 요구 서비스 항목" in content:
                items_section = content.split("## 요구 서비스 항목")[1]
                
                # 각 항목 추출 (### 번호. 제목 형식)
                pattern = r'### (\d+)\.\s+(.+?)\n\n(.+?)(?=\n---|\n###|\Z)'
                matches = re.findall(pattern, items_section, re.DOTALL)
                
                for match in matches:
                    num, title, description = match
                    service_items.append({
                        "구분": title.strip(),
                        "설명": description.strip()
                    })
    except Exception as e:
        print(f"⚠️  마크다운 파일 파싱 오류 ({md_path}): {e}")
    
    return service_items


def update_report_with_service_items(
    report_date: datetime,
    announcement_number: str,
    service_items: List[Dict[str, str]]
) -> bool:
    """
    리포트 JSON 파일에 service_items 추가
    """
    try:
        date_str = get_date_string(report_date)
        report_path = REPORT_DIR / f"report_{date_str}.json"
        
        if not report_path.exists():
            print(f"⚠️  리포트 파일을 찾을 수 없습니다: {report_path}")
            return False
        
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        # 해당 공고 찾아서 service_items 추가
        updated = False
        for ann in report_data:
            if ann.get('announcement_number') == announcement_number:
                ann['service_items'] = service_items
                ann['service_items_extracted_at'] = datetime.now().isoformat()
                updated = True
                break
        
        if updated:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 리포트 파일 업데이트 완료: {report_path}")
            return True
        else:
            print(f"⚠️  리포트에서 공고를 찾을 수 없습니다: {announcement_number}")
            return False
            
    except Exception as e:
        print(f"❌ 리포트 파일 업데이트 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def update_firestore_with_service_items(
    announcement_number: str,
    service_items: List[Dict[str, str]]
) -> bool:
    """
    Firestore에 service_items 업데이트
    """
    try:
        update_data = {
            'service_items': service_items,
            'service_items_extracted_at': datetime.now().isoformat()
        }
        
        result = update_announcement_by_number(announcement_number, update_data)
        if result:
            print(f"✅ Firestore 업데이트 완료: {announcement_number}")
            return True
        else:
            print(f"⚠️  Firestore에서 공고를 찾을 수 없습니다: {announcement_number}")
            return False
    except Exception as e:
        print(f"❌ Firestore 업데이트 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def process_approved_announcements(report_date: Optional[datetime] = None) -> Dict:
    """
    적합 판정 받은 공고들의 첨부파일 조사 및 서비스 항목 수집
    
    Args:
        report_date: 리포트 날짜 (기본값: 오늘)
    
    Returns:
        처리 결과 딕셔너리
    """
    if report_date is None:
        report_date = datetime.now()
    
    print("=" * 60)
    print("적합 판정 공고 첨부파일 조사 및 서비스 항목 수집")
    print("=" * 60)
    print(f"날짜: {report_date.strftime('%Y-%m-%d')}")
    
    # Firebase 초기화
    try:
        init_firebase()
        print("✅ Firebase 초기화 성공")
    except Exception as e:
        print(f"⚠️  Firebase 초기화 실패: {e}")
        return {
            'success': False,
            'error': f'Firebase 초기화 실패: {e}',
            'processed': 0
        }
    
    # 리포트 파일 로드
    report_data = load_report(report_date)
    if not report_data:
        print("⚠️  처리할 데이터가 없습니다.")
        return {
            'success': False,
            'error': '처리할 데이터가 없습니다.',
            'processed': 0
        }
    
    # 적합(approved) 판정 받은 공고 필터링
    approved_announcements = [
        ann for ann in report_data
        if ann.get('status') == 'approved' and ann.get('reviewed', False)
    ]
    
    print(f"\n적합 판정 받은 공고 수: {len(approved_announcements)}")
    
    if not approved_announcements:
        print("⚠️  적합 판정 받은 공고가 없습니다.")
        return {
            'success': True,
            'processed': 0,
            'message': '적합 판정 받은 공고가 없습니다.'
        }
    
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    for ann in approved_announcements:
        announcement_number = ann.get('announcement_number')
        title = ann.get('title', '')
        agency = ann.get('agency', '')
        
        print(f"\n{'=' * 60}")
        print(f"처리 중: {announcement_number}")
        print(f"제목: {title}")
        print(f"{'=' * 60}")
        
        # 이미 service_items가 있는지 확인
        if ann.get('service_items'):
            print(f"⏭️  이미 서비스 항목이 수집되어 있습니다. 건너뜁니다.")
            skipped_count += 1
            continue
        
        try:
            # 1. 첨부파일 다운로드 및 분석
            print("\n1. 첨부파일 다운로드 및 분석 중...")
            attachment_result = analyze_attachments(
                announcement_number,
                bid_ord='000',
                title=title,
                created_at=ann.get('created_at')
            )
            
            if not attachment_result.get('success'):
                print(f"⚠️  첨부파일 다운로드 실패: {attachment_result.get('error')}")
                error_count += 1
                continue
            
            # 2. 서비스 항목 추출
            print("\n2. 서비스 항목 추출 중...")
            service_list_result = generate_service_list(
                announcement_number,
                announcement_info={
                    'title': title,
                    'agency': agency
                }
            )
            
            if not service_list_result.get('success'):
                print(f"⚠️  서비스 항목 추출 실패: {service_list_result.get('error')}")
                error_count += 1
                continue
            
            service_items = service_list_result.get('service_items', [])
            if not service_items:
                print("⚠️  추출된 서비스 항목이 없습니다.")
                error_count += 1
                continue
            
            print(f"✅ 서비스 항목 {len(service_items)}개 추출 완료")
            
            # 3. 리포트 JSON 업데이트
            print("\n3. 리포트 JSON 업데이트 중...")
            report_updated = update_report_with_service_items(
                report_date,
                announcement_number,
                service_items
            )
            
            if not report_updated:
                print("⚠️  리포트 파일 업데이트 실패")
                error_count += 1
                continue
            
            # 4. Firestore 업데이트
            print("\n4. Firestore 업데이트 중...")
            firestore_updated = update_firestore_with_service_items(
                announcement_number,
                service_items
            )
            
            if not firestore_updated:
                print("⚠️  Firestore 업데이트 실패")
                error_count += 1
                continue
            
            print(f"\n✅ 완료: {announcement_number}")
            processed_count += 1
            
        except Exception as e:
            print(f"\n❌ 처리 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            error_count += 1
            continue
    
    print("\n" + "=" * 60)
    print("처리 완료")
    print("=" * 60)
    print(f"처리 완료: {processed_count}개")
    print(f"건너뜀: {skipped_count}개")
    print(f"오류: {error_count}개")
    
    return {
        'success': True,
        'processed': processed_count,
        'skipped': skipped_count,
        'errors': error_count,
        'total': len(approved_announcements)
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='적합 판정 받은 공고들의 첨부파일 조사 및 서비스 항목 수집')
    parser.add_argument(
        '--date',
        type=str,
        help='리포트 날짜 (YYYY-MM-DD 형식, 기본값: 오늘)',
        default=None
    )
    
    args = parser.parse_args()
    
    report_date = None
    if args.date:
        try:
            report_date = datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            print(f"❌ 날짜 형식 오류: {args.date} (YYYY-MM-DD 형식으로 입력해주세요)")
            sys.exit(1)
    
    result = process_approved_announcements(report_date)
    
    if not result.get('success'):
        sys.exit(1)


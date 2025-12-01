"""
리포트 파일 검수 서비스
- 리포트 파일의 공고들을 ChatGPT API로 검수
- 검수 결과를 리포트 파일에 반영
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv
import openai

from services.file_service import load_report, REPORT_DIR, get_date_string

load_dotenv()

# OpenAI API 키 설정
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).parent.parent
PROMPTS_DIR = PROJECT_ROOT / 'prompts'
EAP_REVIEW_PROMPT_PATH = PROMPTS_DIR / 'eap_review_prompt.txt'

def load_eap_review_prompt() -> str:
    """
    EAP 검수 프롬프트 파일 로드
    
    Returns:
        프롬프트 텍스트
    """
    if EAP_REVIEW_PROMPT_PATH.exists():
        with open(EAP_REVIEW_PROMPT_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        # 기본 프롬프트 (파일이 없을 경우)
        return """
근로자지원프로그램(EAP, Employee Assistance Program)은 근로자가 직장이나 가정에서 겪는 다양한 문제로 인해 업무 성과에 부정적인 영향을 받지 않도록, 전문가 상담 및 코칭 등 심리 서비스를 무상으로 제공하는 제도입니다.

다음 공고가 EAP에 적합한지 검토해주세요.
"""

def review_report_file(report_date=None, confirm_before_review=True) -> Dict:
    """
    리포트 파일의 모든 공고를 ChatGPT API로 검수하고 리포트 파일을 업데이트
    
    Args:
        report_date: 날짜 (기본값: 오늘)
        confirm_before_review: 검수 전 사용자 컨펌 받기 (기본값: True)
    
    Returns:
        검수 결과 딕셔너리
    """
    if report_date is None:
        report_date = datetime.now()
    
    print("=" * 60)
    print("리포트 파일 검수 시작")
    print("=" * 60)
    print(f"날짜: {report_date.strftime('%Y-%m-%d')}")
    
    # OpenAI API 키 확인
    if not OPENAI_API_KEY:
        error_msg = "⚠️  OPENAI_API_KEY가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요."
        print(error_msg)
        return {
            'success': False,
            'error': error_msg,
            'reviewed_count': 0,
            'approved_count': 0,
            'rejected_count': 0
        }
    
    try:
        # 리포트 파일 로드
        print("\n1. 리포트 파일 로드 중...")
        report_data = load_report(report_date)
        
        if not report_data:
            print("   ⚠️  검수할 데이터가 없습니다.")
            return {
                'success': False,
                'error': '검수할 데이터가 없습니다.',
                'reviewed_count': 0,
                'approved_count': 0,
                'rejected_count': 0
            }
        
        print(f"   ✅ 리포트 파일 로드 완료: {len(report_data)}개 공고")
        
        # 사용자 컨펌 확인
        if confirm_before_review:
            print("\n⚠️  ChatGPT API 사용 시 비용이 발생합니다.")
            print(f"   검수할 공고 수: {len(report_data)}개")
            print(f"   예상 비용: 약 ${len(report_data) * 0.002:.2f} (gpt-3.5-turbo 기준)")
            user_input = input("\n   검수를 진행하시겠습니까? (yes/no): ").strip().lower()
            if user_input not in ('yes', 'y'):
                print("   검수가 취소되었습니다.")
                return {
                    'success': False,
                    'error': '사용자가 검수를 취소했습니다.',
                    'reviewed_count': 0,
                    'approved_count': 0,
                    'rejected_count': 0
                }
            print()
        
        # 각 공고 검수
        print("\n2. ChatGPT API로 공고 검수 중...")
        reviewed_count = 0
        approved_count = 0
        rejected_count = 0
        error_count = 0
        
        for idx, announcement in enumerate(report_data, 1):
            try:
                announcement_number = announcement.get('announcement_number', '')
                
                # 이미 검수된 공고는 건너뛰기 (선택사항)
                # 하지만 review_result가 없거나 status가 없는 경우 재검수
                if announcement.get('reviewed', False) and announcement.get('review_result') and announcement.get('status'):
                    print(f"   [{idx}/{len(report_data)}] 이미 검수됨: {announcement_number}")
                    reviewed_count += 1
                    if announcement.get('status') == 'approved':
                        approved_count += 1
                    elif announcement.get('status') == 'rejected':
                        rejected_count += 1
                    continue
                
                # ChatGPT API로 검수
                review_result = review_announcement_with_chatgpt(announcement)
                
                # 검수 결과를 공고 데이터에 반영
                announcement['reviewed'] = True
                announcement['review_result'] = review_result.get('result', '')
                announcement['review_model'] = review_result.get('model', 'gpt-3.5-turbo')
                announcement['reviewed_at'] = datetime.now().isoformat()
                
                if review_result.get('approved', False):
                    announcement['status'] = 'approved'
                    approved_count += 1
                else:
                    announcement['status'] = 'rejected'
                    rejected_count += 1
                
                reviewed_count += 1
                
                # 진행 상황 출력 (10개마다)
                if idx % 10 == 0:
                    print(f"   진행 중... {idx}/{len(report_data)} (검수: {reviewed_count}, 승인: {approved_count}, 거부: {rejected_count})")
                else:
                    status_icon = "✅" if review_result.get('approved', False) else "❌"
                    print(f"   [{idx}/{len(report_data)}] {status_icon} {announcement_number[:20]}...")
                
            except Exception as e:
                print(f"   [{idx}/{len(report_data)}] 검수 실패: {str(e)}")
                error_count += 1
                # 오류 발생 시 기본값 설정
                announcement['reviewed'] = True
                announcement['review_result'] = f'검수 중 오류 발생: {str(e)}'
                announcement['status'] = 'rejected'
                rejected_count += 1
                continue
        
        # 검수된 리포트 파일 저장
        print("\n3. 검수된 리포트 파일 저장 중...")
        date_str = get_date_string(report_date)
        filename = f'report_{date_str}.json'
        filepath = REPORT_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ 리포트 파일 저장 완료: {filepath}")
        
        # 결과 출력
        print("\n" + "=" * 60)
        print("검수 완료!")
        print("=" * 60)
        print(f"전체 공고: {len(report_data)}개")
        print(f"검수 완료: {reviewed_count}개")
        print(f"승인: {approved_count}개")
        print(f"거부: {rejected_count}개")
        if error_count > 0:
            print(f"오류: {error_count}개")
        
        return {
            'success': True,
            'reviewed_count': reviewed_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'error_count': error_count,
            'report_path': str(filepath)
        }
        
    except Exception as e:
        error_msg = f"검수 중 오류 발생: {str(e)}"
        print(f"\n❌ {error_msg}")
        import traceback
        print(traceback.format_exc())
        return {
            'success': False,
            'error': error_msg,
            'reviewed_count': 0,
            'approved_count': 0,
            'rejected_count': 0
        }

def review_announcement_with_chatgpt(announcement: Dict) -> Dict:
    """
    ChatGPT API를 사용하여 개별 공고 검수
    
    Args:
        announcement: 공고 데이터 딕셔너리
    
    Returns:
        검수 결과 딕셔너리
    """
    try:
        # OpenAI 클라이언트 초기화
        # httpx 클라이언트를 명시적으로 생성하여 proxies 문제 해결
        import httpx
        http_client = httpx.Client(
            timeout=60.0,
            # proxies 파라미터 제외
        )
        client = openai.OpenAI(
            api_key=OPENAI_API_KEY,
            http_client=http_client
        )
        
        # 검수 프롬프트 작성
        title = announcement.get('title', '')
        agency = announcement.get('agency', '')
        business_type = announcement.get('business_type', '')
        budget_amount = announcement.get('budget_amount')
        estimated_price = announcement.get('estimated_price')
        publish_date = announcement.get('publish_date', '')
        
        # 예산 정보 포맷팅
        budget_info = ""
        if budget_amount:
            budget_info += f"배정예산: {format_currency(budget_amount)}원"
        if estimated_price:
            if budget_info:
                budget_info += f"\n추정가격: {format_currency(estimated_price)}원"
            else:
                budget_info = f"추정가격: {format_currency(estimated_price)}원"
        
        # EAP 검수 프롬프트 로드
        base_prompt = load_eap_review_prompt()
        
        # 프롬프트에 공고 정보 삽입
        prompt = base_prompt.format(
            title=title,
            agency=agency,
            business_type=business_type,
            publish_date=publish_date,
            budget_info=budget_info if budget_info else "예산 정보 없음",
            announcement_number=announcement.get('announcement_number', '')
        )
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 근로자지원프로그램(EAP) 전문가입니다. 공고가 EAP의 핵심 요소(심리 상담, 코칭, 근로자 지원 서비스 등)와 관련이 있는지 정확하게 판단합니다."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=400,
            temperature=0.3
        )
        
        result_text = response.choices[0].message.content
        
        # 응답 파싱
        approved = '적합' in result_text or '적합합니다' in result_text or '적합하다' in result_text
        
        return {
            'approved': approved,
            'result': result_text,
            'model': 'gpt-3.5-turbo'
        }
    
    except Exception as e:
        print(f"ChatGPT 검수 중 오류: {str(e)}")
        return {
            'approved': False,
            'result': f'검수 중 오류 발생: {str(e)}',
            'error': str(e),
            'model': 'gpt-3.5-turbo'
        }

def format_currency(amount: int) -> str:
    """
    금액을 읽기 쉬운 형식으로 포맷팅
    
    Args:
        amount: 금액 (원 단위)
    
    Returns:
        포맷팅된 문자열 (예: "1억 5천만원")
    """
    if amount is None:
        return "0원"
    
    if amount < 10000:
        return f"{amount:,}원"
    
    result = []
    
    # 억 단위
    eok = amount // 100000000
    if eok > 0:
        result.append(f"{eok}억")
        amount = amount % 100000000
    
    # 천만 단위
    cheonman = amount // 10000000
    if cheonman > 0:
        result.append(f"{cheonman}천만")
        amount = amount % 10000000
    
    # 만 단위
    man = amount // 10000
    if man > 0:
        result.append(f"{man}만")
        amount = amount % 10000
    
    # 원 단위
    if amount > 0:
        result.append(f"{amount:,}")
    
    return " ".join(result) + "원"


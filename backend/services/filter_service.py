import openai
import os
from dotenv import load_dotenv
from services.firebase_service import get_announcement_by_id, update_announcement
from utils.constants import STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED, MIN_BUDGET, MAX_BUDGET

load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv('OPENAI_API_KEY')

def filter_announcements(announcement_ids, keywords=None):
    """
    공고를 키워드 및 내부 로직으로 필터링하고, ChatGPT API로 검수
    """
    if keywords is None:
        keywords = []
    
    results = []
    
    for announcement_id in announcement_ids:
        announcement = get_announcement_by_id(announcement_id)
        
        if not announcement:
            continue
        
        # 1차 필터링: 키워드 기반 필터링
        passed_keyword_filter = keyword_filter(announcement, keywords)
        
        if not passed_keyword_filter:
            update_announcement(announcement_id, {
                'filtered': True,
                'filter_reason': '키워드 필터링 실패',
                'status': STATUS_REJECTED
            })
            continue
        
        # 2차 필터링: 내부 로직 필터링
        passed_internal_filter = internal_filter(announcement)
        
        if not passed_internal_filter:
            update_announcement(announcement_id, {
                'filtered': True,
                'filter_reason': '내부 로직 필터링 실패',
                'status': STATUS_REJECTED
            })
            continue
        
        # 3차 검수: ChatGPT API 검수
        chatgpt_review = review_with_chatgpt(announcement)
        
        if chatgpt_review['approved']:
            update_announcement(announcement_id, {
                'reviewed': True,
                'review_result': chatgpt_review['result'],
                'status': STATUS_APPROVED
            })
            results.append({
                'id': announcement_id,
                'status': STATUS_APPROVED,
                'review': chatgpt_review
            })
        else:
            update_announcement(announcement_id, {
                'reviewed': True,
                'review_result': chatgpt_review['result'],
                'status': STATUS_REJECTED
            })
            results.append({
                'id': announcement_id,
                'status': STATUS_REJECTED,
                'review': chatgpt_review
            })
    
    return results

def keyword_filter(announcement, keywords):
    """
    키워드 기반 필터링
    keywords가 비어있으면 모든 공고 통과
    """
    if not keywords:
        return True
    
    title = announcement.get('title', '').lower()
    content = announcement.get('content', '').lower()
    category = announcement.get('category', '').lower()
    
    text = f"{title} {content} {category}"
    
    # 키워드 중 하나라도 포함되면 통과
    for keyword in keywords:
        if keyword.lower() in text:
            return True
    
    return False

def internal_filter(announcement):
    """
    내부 로직 기반 필터링
    예: 예산 금액, 기관, 카테고리 등
    """
    # 예산 금액 체크
    budget_amount = announcement.get('budget_amount')
    if budget_amount:
        if budget_amount < MIN_BUDGET or budget_amount > MAX_BUDGET:
            return False
    
    # 예산 문자열이 있는 경우도 처리 (하위 호환성)
    budget_str = announcement.get('budget', '')
    if budget_str and not budget_amount:
        try:
            budget_value = parse_budget(budget_str)
            if budget_value < MIN_BUDGET or budget_value > MAX_BUDGET:
                return False
        except:
            pass
    
    # 기관 필터링 (예시)
    agency = announcement.get('agency', '')
    # 특정 기관 제외 등 (실제 요구사항에 맞게 수정)
    
    return True

def parse_budget(budget_str):
    """예산 문자열을 숫자로 변환"""
    # 간단한 파싱 로직 (실제로는 더 복잡할 수 있음)
    budget_str = budget_str.replace(',', '').replace('원', '').replace(' ', '')
    
    multipliers = {
        '억': 100000000,
        '천만': 10000000,
        '만': 10000,
        '천': 1000
    }
    
    result = 0
    for unit, multiplier in multipliers.items():
        if unit in budget_str:
            parts = budget_str.split(unit)
            if len(parts) > 0:
                try:
                    result += float(parts[0]) * multiplier
                    budget_str = parts[1] if len(parts) > 1 else ''
                except:
                    pass
    
    # 남은 숫자 처리
    try:
        result += float(budget_str)
    except:
        pass
    
    return int(result)

def review_with_chatgpt(announcement):
    """
    ChatGPT API를 사용하여 공고 검수
    """
    try:
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # 검수 프롬프트 작성
        prompt = f"""
다음은 나라장터에서 수집한 사업 공고 정보입니다. 
이 공고가 우리 회사 사업에 적합한지 검토해주세요.

제목: {announcement.get('title', '')}
기관: {announcement.get('agency', '')}
카테고리: {announcement.get('category', '')}
예산: {announcement.get('budget', '')}
내용: {announcement.get('content', '')[:500]}...

다음 형식으로 응답해주세요:
- 적합 여부: 적합/부적합
- 이유: 간단한 설명
"""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 사업 공고를 검토하는 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.3
        )
        
        result_text = response.choices[0].message.content
        
        # 응답 파싱
        approved = '적합' in result_text or '적합합니다' in result_text
        
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
            'error': str(e)
        }


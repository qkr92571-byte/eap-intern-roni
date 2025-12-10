"""
상수 정의
"""

# 공고 상태
STATUS_PENDING = 'pending'
STATUS_APPROVED = 'approved'
STATUS_REJECTED = 'rejected'

STATUS_CHOICES = [STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED]

# 데이터 소스
SOURCE_G2B = '나라장터'

# 기본값
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000

# 예산 범위 (원 단위)
MIN_BUDGET = 1000000  # 100만원
MAX_BUDGET = 100000000000  # 1000억원

# OpenAI 모델 설정
OPENAI_MODEL_REVIEW = 'gpt-3.5-turbo'  # 검수용 모델
OPENAI_MODEL_SERVICE_EXTRACTION = 'gpt-4o-mini'  # 서비스 항목 추출용 모델 (비용 효율적)

# OpenAI API 설정
OPENAI_TIMEOUT = 60.0  # 초
OPENAI_MAX_TOKENS_REVIEW = 400  # 검수용 최대 토큰
OPENAI_MAX_TOKENS_SERVICE_EXTRACTION = 2000  # 서비스 항목 추출용 최대 토큰
OPENAI_TEMPERATURE_REVIEW = 0.3  # 검수용 temperature
OPENAI_TEMPERATURE_SERVICE_EXTRACTION = 0.2  # 서비스 항목 추출용 temperature

# Slack 채널 ID
SLACK_PRODUCTION_CHANNEL_ID = 'C034EQD6W4W'

# 파일 경로
REPORT_DIR_NAME = 'report'
HISTORY_DIR_NAME = 'history'
DOWNLOADS_DIR_NAME = 'downloads'
PROMPTS_DIR_NAME = 'prompts'



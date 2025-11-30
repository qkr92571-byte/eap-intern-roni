from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
from routes import api_bp
from services.firebase_service import init_firebase

load_dotenv()

app = Flask(__name__)
# CORS 설정: 개발 환경에서 모든 origin 허용
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"], supports_credentials=True)

# Firebase 초기화
init_firebase()

# 기본 키워드 초기화
from services.keyword_service import initialize_default_keywords
initialize_default_keywords()

# API 라우트 등록
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/')
def health_check():
    return jsonify({'status': 'ok', 'message': '나라장터 공고 수집 시스템 API'})

if __name__ == '__main__':
    # 환경 변수에서 포트를 가져오거나 기본값 5001 사용
    port = int(os.environ.get('PORT', 5001))
    print(f"\n서버 시작 중... 포트: {port}")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=True)
    except OSError as e:
        if 'Address already in use' in str(e):
            print(f"\n⚠️  포트 {port}가 이미 사용 중입니다.")
            print("다른 포트를 사용하거나 기존 프로세스를 종료하세요.")
            # 포트 5002로 재시도
            print(f"포트 5002로 재시도 중...")
            app.run(host='0.0.0.0', port=5002, debug=True)
        else:
            raise


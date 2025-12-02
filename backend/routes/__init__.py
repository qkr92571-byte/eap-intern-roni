from flask import Blueprint
from .announcement_routes import announcement_bp
from .keyword_routes import keyword_bp
from .report_routes import report_bp
from .nara_api_routes import nara_api_bp

api_bp = Blueprint('api', __name__)

# 하위 라우트 등록
api_bp.register_blueprint(announcement_bp, url_prefix='/announcements')
api_bp.register_blueprint(keyword_bp, url_prefix='/keywords')
api_bp.register_blueprint(report_bp, url_prefix='/reports')
api_bp.register_blueprint(nara_api_bp, url_prefix='/nara-api')


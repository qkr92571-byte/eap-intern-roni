"""
Flask API Smoke 테스트
- Flask test client 사용 (실제 서버 불필요)
- Firebase/Firestore는 mock 처리
"""
import sys
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def client(mocker):
    """Flask test client. Firebase를 mock으로 대체."""
    mocker.patch('services.firebase_service.init_firebase')
    mocker.patch('services.firebase_service.get_db', return_value=MagicMock())
    mocker.patch('services.keyword_service.initialize_default_keywords')

    # app 모듈 캐시 제거 → mock이 활성화된 상태에서 재초기화
    sys.modules.pop('app', None)
    from app import app as flask_app
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as test_client:
        yield test_client


class TestHealthCheck:

    def test_루트_헬스체크(self, client):
        resp = client.get('/')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'ok'


class TestKeywordsAPI:

    def test_키워드_목록_조회(self, client, mocker):
        # routes.keyword_routes에서 import된 함수를 직접 패치
        mocker.patch(
            'routes.keyword_routes.get_keywords',
            return_value=['찾아가는 상담실', '심리상담', 'EAP'],
        )
        resp = client.get('/api/keywords')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert '찾아가는 상담실' in data['data']['keywords']

    def test_키워드_추가(self, client, mocker):
        mocker.patch('routes.keyword_routes.add_keyword', return_value=True)
        mocker.patch('routes.keyword_routes.get_keywords', return_value=['마음건강'])
        resp = client.post('/api/keywords', json={'keyword': '마음건강'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_키워드_없이_추가시_400(self, client):
        resp = client.post('/api/keywords', json={})
        assert resp.status_code == 400

    def test_키워드_삭제(self, client, mocker):
        mocker.patch('routes.keyword_routes.remove_keyword', return_value=True)
        mocker.patch('routes.keyword_routes.get_keywords', return_value=[])
        resp = client.delete('/api/keywords/마음건강')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True


class TestAnnouncementsAPI:

    def test_공고_목록_조회(self, client, mocker):
        mocker.patch(
            'routes.announcement_routes.get_announcements',
            return_value=[{
                'id': 'test-id',
                'title': '소방공무원 찾아가는 상담실',
                'status': 'approved',
            }],
        )
        resp = client.get('/api/announcements')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

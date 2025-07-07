import pytest

@pytest.fixture
def client():
    """
    Create a test client for the Flask application.
    """
    from web.main import app
    with app.test_client() as client:
        yield client

def test_home_route(client):
    """
    Test the home route of the web application.
    """

    response = client.get('/')
    assert response.status_code == 200
    assert response.data == b'Welcome to the Web Application!'

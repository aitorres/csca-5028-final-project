"""
Unit tests for the web application's main module.
"""

import pytest

from web.main import app


@pytest.fixture(name='web_client')
def fixture_web_client():
    """
    Create a test client for the Flask application.
    """

    with app.test_client() as client:
        yield client


def test_home_route(web_client):
    """
    Test the home route of the web application.
    """

    response = web_client.get('/')
    assert response.status_code == 200
    content = response.get_data(as_text=True)

    assert "What's up in Vancouver?" in content
    assert "CU Boulder's MSCS program" in content

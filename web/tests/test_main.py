"""
Unit tests for the web application's main module.
"""

from typing import Generator

import pytest
from flask.testing import FlaskClient

from web.main import app


@pytest.fixture(name='web_client')
def fixture_web_client() -> Generator[FlaskClient, None, None]:
    """
    Create a test client for the Flask application.
    """

    with app.test_client() as client:
        yield client


def test_home_route(web_client) -> None:
    """
    Test the home route of the web application.
    """

    response = web_client.get('/')
    assert response.status_code == 200
    content = response.get_data(as_text=True)

    assert "What's up in Vancouver?" in content
    assert "CU Boulder's MSCS program" in content


def test_health_check_route(web_client) -> None:
    """
    Test the health check route of the web application.
    """

    response = web_client.get('/health')
    assert response.status_code == 200
    assert response.get_data(as_text=True) == "ok"

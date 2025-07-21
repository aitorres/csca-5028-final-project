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

    response = web_client.get('/api/health')
    assert response.status_code == 200
    assert response.get_data(as_text=True) == "ok"


def test_get_post_count_route(mocker, web_client) -> None:
    """
    Tests the post count route of the web application API.

    Since this API endpoint makes a call to the database,
    we mock the database connection and use a spy to assert
    we are making the expected calls.
    """

    mock_db = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_db.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (42,)

    mocker.patch('web.main.get_db_connection', return_value=mock_db)

    response = web_client.get('/api/posts/count')
    assert response.status_code == 200
    assert response.get_json() == {"count": 42}

    mock_cursor.execute.assert_called_once_with(
        "SELECT COUNT(*) FROM posts"
    )
    mock_cursor.close.assert_called_once()


def test_get_posts_api(mocker, web_client) -> None:
    """
    Tests the get posts API route of the web application.

    Since this API endpoint makes a call to the database,
    we mock the database connection and use a spy to assert
    we are making the expected calls.
    """

    mock_db = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_db.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        (
            1,
            "This is the first post",
            "positive",
            "2025-07-20 12:00:00",
            "2025-07-17 12:00:00",
            "bluesky",
        ),
        (
            2,
            "This is the second post",
            "neutral",
            "2025-07-21 12:00:00",
            "2025-07-18 12:00:00",
            "user",
        ),
    ]

    mocker.patch('web.main.get_db_connection', return_value=mock_db)

    response = web_client.get('/api/posts')
    assert response.status_code == 200
    data = response.get_json()

    assert len(data) == 2
    assert data[0] == {
        "id": 1,
        "text": "This is the first post",
        "sentiment": "positive",
        "inserted_at": "2025-07-20 12:00:00",
        "created_at": "2025-07-17 12:00:00",
        "source": "bluesky"
    }
    assert data[1] == {
        "id": 2,
        "text": "This is the second post",
        "sentiment": "neutral",
        "inserted_at": "2025-07-21 12:00:00",
        "created_at": "2025-07-18 12:00:00",
        "source": "user"
    }

    mock_cursor.execute.assert_called_once_with(
        """
        SELECT id, content, sentiment, inserted_at, created_at, source
        FROM posts
        ORDER BY created_at DESC, id DESC
        """
    )
    mock_cursor.close.assert_called_once()


def test_get_post_source_statistics(mocker, web_client) -> None:
    """
    Tests the post source statistics API route of the web application.

    Since this API endpoint makes a call to the database,
    we mock the database connection and use a spy to assert
    we are making the expected calls.
    """

    mock_db = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_db.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        ("bluesky", 10),
        ("user", 5),
    ]

    mocker.patch('web.main.get_db_connection', return_value=mock_db)

    response = web_client.get('/api/posts/statistics/sources')
    assert response.status_code == 200
    data = response.get_json()

    assert data == {
        "labels": ["bluesky", "user"],
        "data": [10, 5]
    }

    mock_cursor.execute.assert_called_once_with(
        """
        SELECT source, COUNT(*) as count
        FROM posts
        GROUP BY source
        """
    )
    mock_cursor.close.assert_called_once()


def test_get_post_sentiment_statistics(mocker, web_client) -> None:
    """
    Tests the post sentiment statistics API route of the web application.

    Since this API endpoint makes a call to the database,
    we mock the database connection and use a spy to assert
    we are making the expected calls.
    """

    mock_db = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_db.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        ("positive", 20),
        ("negative", 10),
        ("neutral", 5),
    ]

    mocker.patch('web.main.get_db_connection', return_value=mock_db)

    response = web_client.get('/api/posts/statistics/sentiment')
    assert response.status_code == 200
    data = response.get_json()

    assert data == {
        "labels": ["positive", "negative", "neutral"],
        "data": [20, 10, 5]
    }

    mock_cursor.execute.assert_called_once_with(
        """
        SELECT sentiment, COUNT(*) as count
        FROM posts
    GROUP BY sentiment"""
    )
    mock_cursor.close.assert_called_once()


def test_get_post_sentiment_statistics_with_interval(mocker, web_client) -> None:
    """
    Tests the post sentiment statistics API route with a time interval,
    including both valid and invalid queries.

    Since this API endpoint makes a call to the database,
    we mock the database connection and use a spy to assert
    we are making the expected calls.
    """

    # Checking for invalid cases first
    response = web_client.get('/api/posts/statistics/sentiment?hours=invalid')
    assert response.status_code == 400
    assert response.get_json() == {"error": "If specified, hours must be a valid integer"}

    response = web_client.get('/api/posts/statistics/sentiment?hours=-1')
    assert response.status_code == 400
    assert response.get_json() == {"error": "If specified, hours must be a positive integer"}

    # Checking for valid case
    query = f"""
        SELECT sentiment, COUNT(*) as count
        FROM posts
    WHERE created_at >= NOW() - INTERVAL '24 hours' GROUP BY sentiment"""

    mock_db = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_db.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        ("positive", 15),
        ("negative", 7),
        ("neutral", 3),
    ]

    mocker.patch('web.main.get_db_connection', return_value=mock_db)

    response = web_client.get(f'/api/posts/statistics/sentiment?hours=24')
    assert response.status_code == 200
    data = response.get_json()

    assert data == {
        "labels": ["positive", "negative", "neutral"],
        "data": [15, 7, 3]
    }

    mock_cursor.execute.assert_called_once_with(query)
    mock_cursor.close.assert_called_once()

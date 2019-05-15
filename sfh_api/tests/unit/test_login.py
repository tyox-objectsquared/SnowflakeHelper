from sfh_api.src.snowflake_helper.app import app
import pytest
import json

USERNAME = "SEDC_READ"
PASSWORD = "Chang3m3"
ACCOUNT_NAME = "os27885"

@pytest.fixture
def client():
    client = app.test_client()
    yield client

def test_data(client):
    login_data = json.dumps({
        "username": USERNAME,
        "password": PASSWORD,
        "account": ACCOUNT_NAME
    })
    rv = client.post("/login", data=login_data, follow_redirects=True)
    assert rv.status_code == 200
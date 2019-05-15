from sfh_api.src.snowflake_helper import app
import pytest
import json

USERNAME = "SEDC_READ"
PASSWORD = "Chang3m3"
ACCOUNT_NAME = "os27885"

@pytest.fixture
def client():
    client = app.app.test_client()
    yield client

@pytest.fixture
def auth_header(client):
    login_data = json.dumps({
        "username": USERNAME,
        "password": PASSWORD,
        "account": ACCOUNT_NAME
    })
    rv = client.post("/login", data=login_data)
    body = rv.data
    auth_token = body["auth_token"]
    yield auth_token

def test_encode_auth_token(client):
    app.encode_auth_token()

def test_login_response_format(client):
    login_data = json.dumps({
        "username": USERNAME,
        "password": PASSWORD,
        "account": ACCOUNT_NAME
    })
    rv = client.post("/login", data=login_data)
    body = json.loads(rv.data)
    is_auth = body["data"]["isAuth"]
    has_token = "auth_token" in body
    assert is_auth and has_token
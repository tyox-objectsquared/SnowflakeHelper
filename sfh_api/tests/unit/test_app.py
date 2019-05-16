from sfh_api.src.snowflake_helper import app
from sfh_api.tests.testing_creds import TEST_USERNAME, TEST_PASSWORD, TEST_ACCOUNT_NAME, TEST_DB, TEST_WAREHOUSE
import pytest
import json
import datetime
import time

TEST_TAG = "Snowflake Helper Testing"

@pytest.fixture
def client():
    client = app.app.test_client()
    app.MODE = "TESTING"
    yield client

@pytest.fixture
def auth_token(client):
    login_data = json.dumps({
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
        "account": TEST_ACCOUNT_NAME
    })
    rv = client.post("/login", data=login_data)
    body = json.loads(rv.data)
    auth_token = body["auth_token"]
    yield auth_token


@pytest.fixture
def auth_header(auth_token):
    yield {"Authorization": auth_token}


@pytest.fixture
def now():
    yield int(datetime.datetime.utcnow().timestamp())

def test_login_response(client):
    login_data = json.dumps({
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
        "account": TEST_ACCOUNT_NAME
    })
    rv = client.post("/login", data=login_data)
    body = json.loads(rv.data)
    is_auth = body["data"]["isAuth"]
    has_token = "auth_token" in body
    assert (is_auth and has_token) and rv.status_code == 200


def test_account_info_response(client, auth_header):
    rv = client.get("/account-info?username={0}".format(TEST_USERNAME) , headers=auth_header)
    body = json.loads(rv.data)["data"]
    print(body)
    assert ("NAME" in body and "LOGIN_NAME" in body) and rv.status_code == 200


def test_usage_response(client, now, auth_header):
    rv = client.get("/usage?&start_date={0}".format(now) , headers=auth_header)
    body = json.loads(rv.data)["data"]
    print(body)
    assert isinstance(body, dict)


def test_queries_response(client, now, auth_header):
    rv = client.get("/queries?&start_date={0}&numMinutes={1}".format(now, 30), headers=auth_header)
    body = json.loads(rv.data)["data"]
    print(body)
    assert isinstance(body, list)


def test_stop_query_response(client, now, auth_header):
    #start a query
    query = "select * from {0}.MDM.SV_INTERVAL_METER_F, {0}.MDM.SV_READING_F /*{1}*/".format(TEST_DB, TEST_TAG)
    rv0 = client.post("/queries/start?".format(now, 30), headers=auth_header, data=json.dumps({"query": query}))
    start_resp = json.loads(rv0.data)["data"]
    time.sleep(5) # wait for 5 secs for query to reach Snowflake

    #get info on the running query
    rv1 = client.get("/queries?&start_date={0}&numMinutes={1}".format(now, 1), headers=auth_header)
    query_list = json.loads(rv1.data)["data"]

    #stop the query
    for q in query_list:
        if q["QUERY_TEXT"] == query:
            rv2 = client.get("/queries/stop?&start_date={0}&id={1}".format(now, q.QUERY_ID), headers=auth_header)
            stop_resp = json.loads(rv2.data)["data"]
            print(start_resp, query_list, stop_resp)


def test_encode_auth_token():
    data = {"user": "TEST_USER", "account": "TEST_ACCOUNT"}
    token = app.encode_auth_token(data)
    assert token #will throw an error if unable to encode


def test_decode_auth_token(auth_token):
    data, exp = app.decode_auth_token(auth_token)
    print(data)
    assert "user" in data and "account" in data


def test_extend_auth_token(auth_token):
    data_x, exp_x = app.decode_auth_token(auth_token)
    data_y, exp_y = app.decode_auth_token( app.extend_auth_token(auth_token) )
    assert (exp_y - exp_x) > 0



from sfh_api.src.snowflake_helper import app
from sfh_api.tests.testing_creds import TEST_USERNAME, TEST_PASSWORD, TEST_ACCOUNT_NAME, TEST_DB, TEST_TAG
import pytest
import json
import datetime
import time
from threading import Thread


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
    #query = "select * from {0}.MDM.INTERVAL_METER_F, {0}.MDM.READING_F /*{1}*/".format(TEST_DB, TEST_TAG)
    query = "select count(*) from {0}.MDM.READING_F /*{1}*/".format(TEST_DB, TEST_TAG)
    new_thread = Thread(target=__threaded_start_query, args=[query, client, auth_header])
    new_thread.start()
    time.sleep(5) # wait for 5 secs for query to reach Snowflake

    #get info on the running query
    rv1 = client.get("/queries?start_date={0}&numMinutes={1}".format(now, 2), headers=auth_header)
    query_list = json.loads(rv1.data)["data"]
    print("List of running queries:")
    print(query_list)

    #stop the query
    stop_resp = {}
    for q in query_list:
        if q["QUERY_TEXT"] == query:
            rv2 = client.get("/queries/stop?start_date={0}&id={1}".format(now, q.QUERY_ID), headers=auth_header)
            stop_resp = json.loads(rv2.data)["data"]
    print("Stop result:")
    print(stop_resp)
    assert stop_resp["status"] == "SUCCESS"

@pytest.mark.skip
def __threaded_start_query(query, client, auth_header):
    rv0 = client.post("/queries/start", headers=auth_header, data=json.dumps({"query": query}))
    print("Query result:")
    print(json.loads(rv0.data)["data"])


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



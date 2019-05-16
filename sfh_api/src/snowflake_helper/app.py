#!/usr/bin/env python3
from flask import Flask, request, make_response
from flask_cors import CORS
from sfh_api.src.snowflake_helper import snowflake_access as sa
from sfh_api.tests.testing_creds import TEST_USERNAME, TEST_PASSWORD, TEST_ACCOUNT_NAME
import json
import snowflake.connector
import datetime
import jwt

app = Flask(__name__)
MODE = 'PROD'
SECRET_KEY = '3GAbKNF938Vq5LZA6TU7jc5zPts2PcA6'
app.config["SECRET_KEY"] = SECRET_KEY
CORS(app)


### PUBLIC ENDPOINTS - anyone can access ###

@app.route('/login',  methods=["POST"])
def login():
    try:
        data = json.loads(request.data)
        data["account"] = data["account"].upper() + '.us-east-1'
        # check if a connection to snowflake can be made
        sao = sa.SnowflakeAccess(login_name=data["username"], password=data["password"], account_name=data["account"])
        is_authorized = hasattr(sao,'connection')
        if is_authorized:
            sao.close()
            auth_token = encode_auth_token({'user': data["username"], 'account': data["account"]}) #no need to transfer password anymore
            if auth_token: #return the encoded auth_token
                return make_response(json.dumps({"data": {"isAuth": True}, "auth_token": auth_token}, default=str), 200)
    except snowflake.connector.errors.DatabaseError:
        return make_response(json.dumps({"data": {'isAuth': False, 'message': "Incorrect username or password was specified."}}), 401)
    except snowflake.connector.errors.ForbiddenError:
        return make_response(json.dumps({"data": {'isAuth': False, 'message':  "Failed to connect to Snowflake. Verify the account name is correct"}}), 401)


### PRIVATE ENDPOINTS - authorization header is required ###

def private_request(req, method_name):
    auth_token = req.headers.get('Authorization')
    if auth_token:
        resp, exp = decode_auth_token(auth_token)
        if resp == 'expired': return 'authorization token expired', 401
        if resp == 'invalid': return 'authorization token invalid', 401
        extended_token = extend_auth_token(auth_token)
        try:
            sao = None
            if MODE == 'TESTING':
                sao = sa.SnowflakeAccess(login_name=TEST_USERNAME, password=TEST_PASSWORD, account_name=TEST_ACCOUNT_NAME) # testing done on main account, not the reader acct
            else:
                sao = sa.SnowflakeAccess(login_name='SEDCADMIN', password='P@rt41209', account_name=resp.get('account')) # log in as SEDCAMIN user on reader account
            sao.declare_role('accountadmin') # switch to accountadmin role
        except snowflake.connector.errors.DatabaseError:
            return 'Account is not properly configured for usage with with Snowflake Helper. Please contact an administrator.', 500
        data = None

        try:
            #Time Sensitive Methods - use the request timestamp
            if method_name == 'metering_history':
                data = sao.metering_history(**req.args)
            elif method_name == 'query_history':
                data = sao.query_user_history(**req.args)
            elif method_name == 'stop_query':
                data = sao.stop_query(**req.args)
            #Non Time Sensitive Methods, don't require the request timestamp
            elif method_name == 'account_info':
                data = sao.account_info(req.args["username"])
            elif method_name == 'change_email':
                req_data = json.loads(req.data)
                data = sao.change_email(req_data["username"], req_data["emailAddress"])
            elif method_name == 'change_password':
                req_data = json.loads(req.data)
                data = sao.change_password(req_data["loginName"], req_data["username"], req_data["oldP"], req_data["newP"])
            elif method_name == 'start_query':
                req_data = json.loads(req.data)
                data = sao.start_query(req_data["query"])
        except snowflake.connector.ProgrammingError as e0:
            return str(e0), 500
        sao.close() # close snowflake session when finished
        response = make_response(json.dumps({'data': data, 'auth_token': extended_token}, default=str), 200)
        return response
    else: #no header
        return 'no authorization provided', 401

@app.route('/account-info', methods=["GET"])
def account_info():
    return private_request(request, 'account_info')

@app.route('/usage', methods=["GET"])
def usage_history():
    return private_request(request, 'metering_history')

@app.route('/queries', methods=["GET"])
def query_history():
    return private_request(request, 'query_history')

@app.route('/queries/stop', methods=["POST"])
def stop_query():
    return private_request(request, 'stop_query')

@app.route('/queries/start', methods=["POST"])
def start_query():
    return private_request(request, 'start_query')

@app.route('/update-email', methods=["POST"])
def change_email():
    return private_request(request, 'change_email')

@app.route('/update-password', methods=["POST"])
def change_password():
    return private_request(request, 'change_password')


#Helper Methods for jwt

def encode_auth_token(data):
    try:
        payload = {
            'exp': (datetime.datetime.utcnow() + datetime.timedelta(minutes=5)).timestamp(),
            'iat': datetime.datetime.utcnow(),
            'sub': data
        }
        return jwt.encode(
            payload,
            app.config.get('SECRET_KEY'),
            algorithm='HS256'
        ).decode('utf-8')
    except Exception as e:
        return e

def decode_auth_token(auth_token):
    try:
        payload = jwt.decode(auth_token, app.config.get('SECRET_KEY'), algorithms=["HS256"])
        return payload["sub"], payload["exp"]
    except jwt.ExpiredSignatureError:
        return 'expired'
    except jwt.InvalidTokenError:
        return 'invalid'

def extend_auth_token(auth_token):
    try:
        payload = jwt.decode(auth_token, app.config.get('SECRET_KEY'), algorithms=["HS256"])
        payload["exp"] = (datetime.datetime.utcnow() + datetime.timedelta(minutes=5)).timestamp()
        return jwt.encode(
            payload,
            app.config.get('SECRET_KEY'),
            algorithm='HS256'
        ).decode('utf-8')
    except Exception as e:
        return e


if __name__ == '__main__':
    app.run(app.run(debug=True, host='0.0.0.0'))

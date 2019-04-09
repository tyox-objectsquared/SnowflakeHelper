#!/usr/bin/env python3
from flask import Flask, request, make_response
from flask_cors import CORS
import snowflake_access as sa
import json
import snowflake.connector
import datetime
import jwt

app = Flask(__name__)
SECRET_KEY = '3GAbKNF938Vq5LZA6TU7jc5zPts2PcA6R6tvehgC3jaLZmdPygJ7CRFPc4rYJnZB'
app.config['SECRET_KEY'] = SECRET_KEY
CORS(app)

# TODO Dockerize
ADMIN_USERNAME = 'tyox@objectsquared.com'
ADMIN_PASSWORD = 'HiromiUehara09!'
ADMIN_ACCOUNT = 'oz95710.us-east-1'
ADMIN_WH_NAME = 'SEDC_WH'
COOPS_TABLE_NAME = ' MDM.ETLWHSE.COOPERATIVE'
MONITOR_SEDC = True

PILOT_USERNAME = 'ALERTS_PILOT'
PILOT_PASSWORD = 'EwRvt5qVUeKWbpwKBAvN7DqZ3LUENTMdYKz2Bf44E3yMkb5TgGGkqTrKf8k3znmv'
PILOT_ACCOUNT = 'oz95710.us-east-1'


### PUBLIC ENDPOINTS - anyone can access ###

@app.route('/login',  methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            data = json.loads(request.data)
            data['account'] = data['account'].upper() + '.us-east-1'
            # check if a connection to snowflake can be made
            sao = sa.SnowflakeAccess(data['username'], data['password'], data['account'])
            is_authorized = hasattr(sao,'connection')
            if is_authorized:
                auth_token = encode_auth_token(data['username'])
                if auth_token: #return the encoded auth_token
                    return make_response(json.dumps({"isAuth": True, "auth_token": auth_token}, default=str), 200)
        except snowflake.connector.errors.DatabaseError as e0:
            return make_response(json.dumps({'isAuth': False, 'message': e0.msg}), 200)



### PRIVATE ENDPOINTS - authorization header is required ###

def private_request(req, data_method):
    auth_token = req.headers.get('Authorization')
    if auth_token:
        resp = decode_auth_token(auth_token)
        if resp == 'expired': return 'authorization token expired', 401
        if resp == 'invalid': return 'authorization token invalid', 401
        extended_token = extend_auth_token(auth_token)
        response = make_response(json.dumps(data_method), 200)
        response.headers['auth_token'] = extended_token
        return response
    else: #no header
        return 'no authorization provided', 401


@app.route('/metering', methods=['GET'])
def usage_history():
    sao = sa.SnowflakeAccess(PILOT_USERNAME, PILOT_PASSWORD, PILOT_ACCOUNT)
    return private_request(request, sao.metering_history())

@app.route('/queries', methods=['GET'])
def query_history():
    sao = sa.SnowflakeAccess(PILOT_USERNAME, PILOT_PASSWORD, PILOT_ACCOUNT)
    return private_request(request, sao.query_user_history(**request.args))

@app.route('/queries/stop/<id>', methods=['POST', 'GET'])
def stop_query(id):
    sao = sa.SnowflakeAccess(PILOT_USERNAME, PILOT_PASSWORD, PILOT_ACCOUNT)
    return private_request(request, sao.stop_query(id))


#Helper Methods for jwt

def encode_auth_token(user_id):
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
            'iat': datetime.datetime.utcnow(),
            'sub': user_id
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
        payload = jwt.decode(auth_token, app.config.get('SECRET_KEY'), algorithms=['HS256'])
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return 'expired'
    except jwt.InvalidTokenError:
        return 'invalid'


def extend_auth_token(auth_token):
    try:
        payload = jwt.decode(auth_token, app.config.get('SECRET_KEY'), algorithms=['HS256'])
        payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        return jwt.encode(
            payload,
            app.config.get('SECRET_KEY'),
            algorithm='HS256'
        ).decode('utf-8')
    except Exception as e:
        return e


if __name__ == '__main__':
    app.run(debug=True)

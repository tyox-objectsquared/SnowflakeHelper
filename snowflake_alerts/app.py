#!/usr/bin/env python3
from flask import Flask, render_template, request, make_response
from flask_cors import CORS
import snowflake_access as sa
import json
import snowflake.connector
import datetime
import jwt

app = Flask(__name__)
SECRET_KEY = '3GAbKNF938Vq5LZA6TU7jc5zPts2PcA6R6tvehgC3jaLZmdPygJ7CRFPc4rYJnZB'
app.config['SECRET_KEY'] = SECRET_KEY
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
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

@app.route('/coops', methods=['GET'])
def coops():
    sao = sa.SnowflakeAccess(ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_ACCOUNT)
    coops = sao.coops(COOPS_TABLE_NAME, ADMIN_WH_NAME)
    if MONITOR_SEDC:
        coops['SEDC'] = 'OZ95710'
    return json.dumps(coops, default=str)

@app.route('/login',  methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            data = json.loads(request.data)
            data[2] += '.us-east-1'
            # check if a connection to snowflake can be made
            sao = sa.SnowflakeAccess(data[0], data[1], data[2])
            is_authorized = hasattr(sao,'connection')
            if is_authorized:
                auth_token = encode_auth_token(data[0])
                if auth_token:
                    return json.dumps({"isAuth": True, "auth_token": decode_auth_token(auth_token)})
        except snowflake.connector.errors.DatabaseError as e0:
            return json.dumps({'isAuth': False, 'message': e0.msg})



### PRIVATE ENDPOINTS - authorization header is required ###

@app.route('/metering', methods=['GET'])
def metering_history():
    auth_header = request.headers.get('Authorization')
    if auth_header:
        resp = decode_auth_token(auth_header)
        if resp == 'expired': return 'authorization token expired', 401
        if resp == 'invalid': return 'authorization token invalid', 401
        sao = sa.SnowflakeAccess(PILOT_USERNAME, PILOT_PASSWORD, PILOT_ACCOUNT)
        return json.dumps(sao.metering_history(), default=str), 200
    else: #no header
        return 'no authorization provided', 401

@app.route('/queries', methods=['GET'])
def query_history():
    auth_header = request.headers.get('Authorization')
    if auth_header:
        resp = decode_auth_token(auth_header)
        if resp == 'expired': return 'authorization token expired', 401
        if resp == 'invalid': return 'authorization token invalid', 401
        args = {}
        num_mins = request.args.get('minutes')
        if num_mins: args['num_minutes'] = num_mins
        show_ongoing = request.args.get('show_ongoing')
        if show_ongoing: args['ongoing_only'] = show_ongoing
        sao = sa.SnowflakeAccess(PILOT_USERNAME, PILOT_PASSWORD, PILOT_ACCOUNT)
        return json.dumps(sao.query_user_history(**args), default=str), 200
    else: #no header
        return 'no authorization provided', 401

@app.route('/queries/stop/<id>', methods=['POST', 'GET'])
def stop_query(id):
    auth_header = request.headers.get('Authorization')
    if auth_header:
        resp = decode_auth_token(auth_header)
        if resp == 'expired': return 'authorization token expired', 401
        if resp == 'invalid': return 'authorization token invalid', 401
        sao = sa.SnowflakeAccess(PILOT_USERNAME, PILOT_PASSWORD, PILOT_ACCOUNT)
        return json.dumps(sao.stop_query(id), default=str), 200
    else: #no header
        return 'no authorization provided', 401


#Helper Methods for jwt

def encode_auth_token(user_id):
    """
    Generates the Auth Token
    :return: string
    """
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=5),
            'iat': datetime.datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(
            payload,
            app.config.get('SECRET_KEY'),
            algorithm='HS256'
        )
    except Exception as e:
        return e


def decode_auth_token(auth_token):
    """
    Decodes the auth token
    :param auth_token:
    :return: integer|string
    """
    try:
        payload = jwt.decode(auth_token, app.config.get('SECRET_KEY'))
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return 'expired'
    except jwt.InvalidTokenError:
        return 'invalid'

if __name__ == '__main__':
    app.run(debug=True)

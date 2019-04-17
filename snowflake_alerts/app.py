#!/usr/bin/env python3
from flask import Flask, request, make_response
from flask_cors import CORS
import snowflake_access as sa
import json
import snowflake.connector
import datetime
import jwt

app = Flask(__name__)
SECRET_KEY = '3GAbKNF938Vq5LZA6TU7jc5zPts2PcA6'
app.config['SECRET_KEY'] = SECRET_KEY
CORS(app)

# TODO Dockerize

### PUBLIC ENDPOINTS - anyone can access ###

@app.route('/login',  methods=['POST'])
def login():
    try:
        data = json.loads(request.data)
        data['account'] = data['account'].upper() + '.us-east-1'
        # check if a connection to snowflake can be made
        sao = sa.SnowflakeAccess(data['username'], data['password'], data['account'])
        is_authorized = hasattr(sao,'connection')
        if is_authorized:
            auth_token = encode_auth_token({'user': data['username'], 'account': data['account']}) #no need to transfer password anymore
            if auth_token: #return the encoded auth_token
                return make_response(json.dumps({"data": {"isAuth": True}, "auth_token": auth_token}, default=str), 200)
    except snowflake.connector.errors.DatabaseError as e0:
        return make_response(json.dumps({"data": {'isAuth': False, 'message': e0.msg}}), 401)



### PRIVATE ENDPOINTS - authorization header is required ###

def private_request(req, method_name):
    auth_token = req.headers.get('Authorization')
    if auth_token:
        resp = decode_auth_token(auth_token)
        if resp == 'expired': return 'authorization token expired', 401
        if resp == 'invalid': return 'authorization token invalid', 401
        extended_token = extend_auth_token(auth_token)
        # CURRENTLY uses accountadmin user
        sao = sa.SnowflakeAccess(username='SEDCADMIN', password='P@rt41209', account_name=resp.get('account'))
        data = None
        try:
            if method_name == 'metering_history':
                data = sao.metering_history()
            elif method_name == 'query_history':
                data = sao.query_user_history(**req.args)
            elif method_name == 'stop_query':
                data = sao.stop_query(**req.args)
        except snowflake.connector.ProgrammingError as e0:
            return str(e0), 500
        response = make_response(json.dumps({'data': data, 'auth_token': extended_token}, default=str), 200)
        return response
    else: #no header
        return 'no authorization provided', 401


@app.route('/usage', methods=['GET'])
def usage_history():
    return private_request(request, 'metering_history')

@app.route('/queries', methods=['GET'])
def query_history():
    return private_request(request, 'query_history')

@app.route('/queries/stop', methods=['POST'])
def stop_query():
    return private_request(request, 'stop_query')


#Helper Methods for jwt

def encode_auth_token(data):
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
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
    app.run(app.run(debug=True, host='0.0.0.0'))

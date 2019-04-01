#!/usr/bin/env python3
from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, session
from flask_cors import CORS
import snowflake.connector
import snowflake_access as sa
import json

app = Flask(__name__)
SECRET_KEY = '3GAbKNF938Vq5LZA6TU7jc5zPts2PcA6R6tvehgC3jaLZmdPygJ7CRFPc4rYJnZB'
app.secret_key = SECRET_KEY
CORS(app)

# TODO move to Docker run arguments
PILOT_USERNAME = 'ALERTS_PILOT'
PILOT_PASSWORD = 'EwRvt5qVUeKWbpwKBAvN7DqZ3LUENTMdYKz2Bf44E3yMkb5TgGGkqTrKf8k3znmv'
PILOT_ACCOUNT = 'oz95710.us-east-1'


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for(endpoint='login_p', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login',  methods=['GET', 'POST'])
def login_p():
    error = None
    if request.method == 'POST':
        try:
            #check if a connection to snowflake can be made
            conn = snowflake.connector.connect(
                user=request.form['username'],
                password=request.form['password'],
                account=PILOT_ACCOUNT)
            conn.close()
            session['user'] = request.form['username']
            return redirect(url_for('welcome'))
        except snowflake.connector.DatabaseError:
            error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route('/cancel', methods=['PUT'])

@app.route('/logout', methods=['GET', 'POST'])
def logout_p():
    session.pop('user', None)
    return redirect(url_for('login_p'))

@app.route('/metering', methods=['GET'])
def metering_history():
    sao = sa.SnowflakeAccess(PILOT_USERNAME, PILOT_PASSWORD, PILOT_ACCOUNT)
    return json.dumps(sao.metering_history(), default=str)

@app.route('/queries', methods=['GET'])
def query_history():
    #return '[{"QUERY_TEXT": "select query_text, user_name, warehouse_name, execution_status, error_code, error_message, start_time, end_time, total_elapsed_time from table( snowflake.information_schema.query_history( end_time_range_start=> dateadd(\'minutes\', -30, current_timestamp()))) order by start_time", "USER_NAME": "ALERTS_PILOT", "WAREHOUSE_NAME": "SEDC_WH", "EXECUTION_STATUS": "SUCCESS", "ERROR_CODE": null, "ERROR_MESSAGE": null, "START_TIME": "2018-03-26 17:16:31.986000-04:00", "END_TIME": "2019-03-26 17:16:32.953000-04:00", "TOTAL_ELAPSED_TIME": "0.967s"}, {"QUERY_TEXT": "select query_text, user_name, warehouse_name, execution_status, error_code, error_message, start_time, end_time, total_elapsed_time from table( snowflake.information_schema.query_history( end_time_range_start=> dateadd(\'minutes\', -30, current_timestamp()))) order by start_time", "USER_NAME": "ALERTS_PILOT", "WAREHOUSE_NAME": "SEDC_WH", "EXECUTION_STATUS": "SUCCESS", "ERROR_CODE": null, "ERROR_MESSAGE": null, "START_TIME": "2019-03-26 17:17:27.495000-04:00", "END_TIME": "2019-03-26 17:17:27.902000-04:00", "TOTAL_ELAPSED_TIME": "0.407s"}, {"QUERY_TEXT": "select query_text, user_name, warehouse_name, execution_status, error_code, error_message, start_time, end_time, total_elapsed_time from table( snowflake.information_schema.query_history( end_time_range_start=> dateadd(\'minutes\', -30, current_timestamp()))) order by start_time", "USER_NAME": "ALERTS_PILOT", "WAREHOUSE_NAME": "SEDC_WH", "EXECUTION_STATUS": "RUNNING", "ERROR_CODE": null, "ERROR_MESSAGE": null, "START_TIME": "2019-03-26 17:18:45.611000-04:00", "END_TIME": "2019-03-26 17:18:45.611000-04:00", "TOTAL_ELAPSED_TIME": "0.0s"}]'
    args_map = {}
    if request.args.get('minutes') != None:
        args_map['num_minutes'] =  request.args.get('minutes')
    if request.args.get('show_ongoing') != None:
        args_map['ongoing_only'] = request.args.get('show_ongoing')
    sao = sa.SnowflakeAccess(PILOT_USERNAME, PILOT_PASSWORD, PILOT_ACCOUNT)
    return json.dumps(sao.query_user_history(**args_map), default=str)

@app.route('/')
def welcome():
    return render_template('welcome.html')  # render a template


if __name__ == '__main__':
    app.run(debug=True)

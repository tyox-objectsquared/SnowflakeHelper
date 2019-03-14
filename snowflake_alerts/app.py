#!/usr/bin/env python3
from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, session
import snowflake.connector
import snowflake_access as sa


app = Flask(__name__)
SECRET_KEY = '3GAbKNF938Vq5LZA6TU7jc5zPts2PcA6R6tvehgC3jaLZmdPygJ7CRFPc4rYJnZB'
app.secret_key = SECRET_KEY

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


@app.route('/logout',  methods=['GET', 'POST'])
def logout_p():
    session.pop('user', None)
    return redirect(url_for('login_p'))


@app.route('/queries', methods=['GET'])
def query_history():
    return query_user_history(None)


@app.route('/queries/<username>', methods=['GET'])
def query_user_history(username):
    minutes = 30
    ongoing_queries_only = False
    if request.args.get('minutes') != None:
        minutes =  request.args.get('minutes')
    if request.args.get('show_ongoing') != None:
        ongoing_queries_only = request.args.get('show_ongoing')
    sao = sa.SnowflakeAccess(PILOT_USERNAME, PILOT_PASSWORD, PILOT_ACCOUNT)
    return sao.query_user_history(username=username,num_minutes=minutes, ongoing_only=ongoing_queries_only)


@app.route('/')
def welcome():
    return render_template('welcome.html')  # render a template


if __name__ == '__main__':
    app.run(debug=True)

import snowflake.connector
from snowflake.connector import DictCursor
from datetime import datetime, timedelta
from pytz import timezone
from operator import itemgetter

TAG = "Snowflake Helper"
SNOWFLAKE_TIME_FMT = "%a, %d %b %Y %H:%M:%S GMT"
EST = timezone("US/Eastern")

class SnowflakeAccess:
    def __init__(self, login_name, password, account_name):
            try:
                self.connection = snowflake.connector.connect(user=login_name, password=password, account=account_name, login_timeout=5)
                self.login_name = login_name
                self.account_name = account_name
                self.region = account_name.split(".")[1]
            except snowflake.connector.errors.ForbiddenError:
                raise
            except snowflake.connector.errors.DatabaseError:
                raise


    def close(self):
        self.connection.close()


    def declare_role(self, role):
        self.connection.cursor().execute("use role {0}/*{1}*/".format(role, TAG))


    def change_email(self, username, email):
        self.connection.cursor().execute("alter user {0} set email = \'{1}\'/*{2}*/".format(username, email, TAG))
        return {"status": "success", "message": "Email has been updated successfully."}


    def account_info(self, username):
        cur = self.connection.cursor(DictCursor)
        cur.execute('desc user {0}/*{1}*/'.format(username, TAG))
        user_data = {}
        for rec in cur:
            key = rec["property"]
            value = rec["value"]
            if value != 'null' and key != 'PASSWORD':
                user_data[key] = value
        return user_data


    def change_password(self, login_name, username, old_password, new_password):
        try:
            acct = SnowflakeAccess(login_name=login_name, password=old_password, account_name=self.account_name)
            self.connection.cursor().execute("alter user {0} set password = \'{1}\'/*{2}*/".format(username, new_password, TAG))
            resp = {'status': 'success', 'message': 'Password was changed successfully.'}
        except snowflake.connector.errors.DatabaseError as e0:
            print(e0.msg)
            resp = {'status': 'failure', 'message': e0.msg}
        return resp


    '''
    Relational data record from Snowflake:
    rec:
        START_TIME: datetime,
        CREDITS_USED: 0.0

    GOAL: Structure the interval data into a JSON-friendly tree structure:
    month_index: {
        day_index:{
            interval: {
                0: x1 (hourly interval data)
                1: x2
                ...
                23: x24
            }
            credits: sum(x_i)
            *total_time: sum(y_j)
            *users: {
                user0: {
                    time: y_0
                    share: time / total_time * 100 (%)
                },
                ...
            }
        }
    }
    * Fields present only for dates in past one week; Snowflake only keeps one week of query logs
    '''
    def metering_history(self, start_date):
        start_date = datetime.fromtimestamp(int(start_date), EST)
        cur = self.connection.cursor(DictCursor)
        try:
            cur.execute("select credits_used, start_time from snowflake.account_usage.warehouse_metering_history/*"+TAG+"*/")
        except snowflake.connector.ProgrammingError:
            raise
        history = []
        history_combined = []
        history_normalized = []
        history_structured = {}
        time_fmt = "%Y-%m-%d %H:%M:%S"
        # Data Transformations
        for rec in cur:
            entry = {
                "time": rec["START_TIME"].astimezone(timezone("US/Eastern")),
                "credits": float(rec["CREDITS_USED"])
            }
            history.append(entry)
        history.sort(key=itemgetter("time"))

        # Combine duplicate times / consolidate warehouse entries
        for i in range(0, len(history)):
            if i != 0 and history[i]["time"].strftime(time_fmt) == history[i-1]["time"].strftime(time_fmt):
                history_combined[-1]["credits"] += history[i]["credits"]
            else:
                history_combined.append(history[i])

        # Normalize to transform into interval data
        index_datetime = history_combined[0]["time"].replace(day=1, hour=0) # start from first hour of the month
        count = 0
        while count < len(history_combined): # While there is still data to process
            if index_datetime.strftime(time_fmt) == history_combined[count]["time"].strftime(time_fmt):
                history_normalized.append(history_combined[count])
                count += 1
            else:
                history_normalized.append({"credits": 0.0, "time": index_datetime}) # fill in data gaps with 0 entry
            index_datetime = (index_datetime + timedelta(hours=1)).astimezone(timezone("US/Eastern")) # timezone doesnt always change over to EST
        last_datetime = history_combined[-1]["time"].replace(month=history_combined[-1]["time"].month + 1, day=1,hour=0) - timedelta(hours=1) # last hour of the month
        while not (index_datetime.strftime(time_fmt) == last_datetime.strftime(time_fmt)): # 0-pad remaining hours
            history_normalized.append({"credits": 0.0, "time": index_datetime})
            index_datetime = (index_datetime + timedelta(hours=1)).astimezone(timezone("US/Eastern"))

        #Structure data into JSON-friendly tree
        queries = self.query_user_usage(start_date) # Get entire query history statistics
        for item in history_normalized:
            month_index = item["time"].strftime("%b, %Y")
            day_index = item["time"].day
            hour_index = item["time"].hour
            if month_index not in history_structured:
                history_structured[month_index] = {}
            if day_index not in history_structured[month_index]:
                history_structured[month_index][day_index] = {"interval": {}, "credits": 0}
                date_index = item["time"].strftime("%Y-%m-%d")
                if date_index in queries:
                    history_structured[month_index][day_index]["users"] = queries[date_index]["users"]
                    history_structured[month_index][day_index]["total_time"] = queries[date_index]["total"]
            history_structured[month_index][day_index]["credits"] += item["credits"]
            history_structured[month_index][day_index]["interval"][hour_index] = item["credits"]

        #rounding of all credit values to 2 decimal places
        for month in history_structured:
            for day in history_structured[month]:
                history_structured[month][day]["credits"] = round(history_structured[month][day]["credits"], 2)
                for hour in history_structured[month][day]["interval"]:
                    history_structured[month][day]["interval"][hour] = round(history_structured[month][day]["interval"][hour], 2)
        return history_structured


    def query_user_usage(self, start_date):
        end_date = start_date - timedelta(hours=166)
        cur = self.connection.cursor(DictCursor)
        queries = []
        queries_normalized = {} #keyed by day
        try:
            cur.execute("select user_name, start_time, total_elapsed_time from "
                        "table(snowflake.information_schema.query_history("
                        "end_time_range_start=> to_timestamp_ltz(\'{0}\'), "
                        "end_time_range_end=> to_timestamp_ltz(\'{1}\'))) "
                        "where user_name not like \'SEDCADMIN\' " #Hide SEDCADMIN usage
                        "order by start_time/*{2}*/".format(end_date.strftime("%Y-%m-%d %H:%M:%S %z"), start_date.strftime("%Y-%m-%d %H:%M:%S %z"), TAG))
            for rec in cur:
                # Data Transformations
                queries.append({
                    "username": rec["USER_NAME"],
                    "start_time": rec["START_TIME"].astimezone(timezone("US/Eastern")),
                    "elapsed_time": rec["TOTAL_ELAPSED_TIME"]
                })
        except snowflake.connector.ProgrammingError as e0:
            print(e0.msg)
            raise
        for query in queries:
            day = query["start_time"].strftime("%Y-%m-%d")
            user = query["username"]
            if day not in queries_normalized:
                queries_normalized[day] = {"total": 0.0, "users": {}}
            if user not in queries_normalized[day]["users"]:
                queries_normalized[day]["users"][user] = {"time": 0}
            queries_normalized[day]["total"] += query["elapsed_time"]
            queries_normalized[day]["users"][user]["time"] += query["elapsed_time"]
        # calculate the % share of time that each user occupies
        for day in queries_normalized:
            for user in queries_normalized[day]["users"]:
                user_time = queries_normalized[day]["users"][user]["time"]
                total_time = queries_normalized[day]["total"]
                queries_normalized[day]["users"][user]["share"] = round(user_time / total_time * 100.00, 2)
                queries_normalized[day]["users"][user]["time"] = '{0}s'.format(round(queries_normalized[day]["users"][user]["time"] / 1000.00, 2))
            queries_normalized[day]["total"] = '{0}s'.format(round(queries_normalized[day]["total"] / 1000.00, 2))
        return queries_normalized


    def query_user_history(self, start_date, numMinutes=30, ongoingOnly=False): # Defaults to all queries in the last 30 minutes
        cur = self.connection.cursor(DictCursor)
        start_date = datetime.fromtimestamp(int(start_date), EST) - timedelta(minutes=int(numMinutes))
        history = []
        try:
            cur.execute("select query_id, query_text, user_name, warehouse_name, execution_status, error_code, error_message, start_time, end_time, total_elapsed_time from "
                        "table(snowflake.information_schema.query_history("
                        "end_time_range_start=> to_timestamp_ltz(\'{0}\'))) "
                        "where query_text not like \'%\*{1}\*%\' " #filter out queries that have the Snowflake Helper TAG as an SQL comment
                        "and user_name not like \'SEDCADMIN\' " #Hide SEDCADMIN queries
                        "order by start_time/*{1}*/".format(start_date.strftime("%Y-%m-%d %H:%M:%S %z"), TAG))
            for rec in cur:
                # Data Transformations
                rec["START_TIME"] = rec["START_TIME"].astimezone(timezone("US/Eastern"))
                rec["END_TIME"] = rec["END_TIME"].astimezone(timezone("US/Eastern"))
                if not (rec["EXECUTION_STATUS"] == 'FAILED_WITH_ERROR' or rec["EXECUTION_STATUS"] == 'FAILED_WITH_INCIDENT'):
                    rec.pop('ERROR_MESSAGE')
                    rec.pop('ERROR_CODE')
                minutes = int(rec["TOTAL_ELAPSED_TIME"] / 60000.0)
                seconds = (rec["TOTAL_ELAPSED_TIME"] / 1000.0) % 60.000
                time_string = '{0}s'.format(seconds)
                if minutes > 0:
                    time_string = '{0}m {1}s'.format(minutes, round(seconds))
                if int(rec["TOTAL_ELAPSED_TIME"]) < 0:
                    rec["TOTAL_ELAPSED_TIME"] = '0.0s'
                    rec["END_TIME"] = rec["START_TIME"]
                else:
                    rec["TOTAL_ELAPSED_TIME"] = time_string
                if ongoingOnly:
                    if rec["EXECUTION_STATUS"] == 'RESUMING_WAREHOUSE' or rec["EXECUTION_STATUS"] == 'RUNNING' or rec["EXECUTION_STATUS"] == 'QUEUED':
                        history.append(rec)
                else:
                    history.append(rec)
        except snowflake.connector.ProgrammingError as e0:
            print(e0.msg)
            raise
        history.reverse()
        return history


    def start_query(self, query):
        cur = self.connection.cursor()
        cur.execute(query)
        data = []
        for rec in cur:
            data.append(rec)
        return data[0]



    def stop_query(self, id, start_date):
        cur = self.connection.cursor()
        start_date = datetime.fromtimestamp(int(start_date), EST) - timedelta(minutes=1)
        message = cur.execute("select system$cancel_query(\'{0}\')".format(id)).fetchone()
        if message[0] != "Identified SQL statement is not currently executing.":
            status, error_message, error_code, start_time, end_time = cur.execute(
                "select execution_status, error_message, error_code, start_time, end_time from "
                "table(snowflake.information_schema.query_history("
                "end_time_range_start=> to_timestamp_ltz(\'{0}\'))) "
                "where query_id = \'{1}\'/*{2}*/".format(start_date, id, TAG)).fetchone()
            obj = {"id": id, "status": status, "message": message[0], "start_time": start_time, "end_time": end_time}
            if error_message is not None:
                obj["error_message"] = error_message
                obj["error_code"] = error_code
            return obj
        else:
            return {"id": id, "status": "SUCCESS", "message": message[0]}


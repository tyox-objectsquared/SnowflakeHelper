import snowflake.connector
from snowflake.connector import DictCursor
import datetime
from pytz import timezone
from operator import itemgetter


class SnowflakeAccess:

    inst = None

    class __SAO:  #snowflake access object, private
        def __init__(self, login_name, password, account_name):
            try:
                self.connection = snowflake.connector.connect(user=login_name, password=password, account=account_name, login_timeout=5)
                self.login_name = login_name
                self.account_name = account_name
                self.region = account_name.split(".")[1]
                cur = self.connection.cursor(DictCursor)
                user_name = cur.execute('select current_user()').fetchone()['CURRENT_USER()']
                cur.execute('desc user {0}'.format(user_name))
                for rec in cur:
                    key = rec['property']
                    value = rec['value']
                    if value != 'null':
                        self.__setattr__(key, value)
            except snowflake.connector.errors.DatabaseError:
                self.connection = None
                raise

    def __init__(self, username, password, account_name):
        if not SnowflakeAccess.inst:
            SnowflakeAccess.inst = SnowflakeAccess.__SAO(username, password, account_name)
        else:
            try:
                SnowflakeAccess.inst.connection = snowflake.connector.connect(user=username, password=password, account=account_name)
            except snowflake.connector.errors.DatabaseError:
                raise
    def __getattr__(self, name):
        return getattr(self.inst, name)

    def alerts_creds(self):
        cur = self.inst.connection.cursor()
        username, password = cur.execute('select * from mdm.etlwhse.alerts').fetchone()
        return {'username': username, 'password': password, 'account': self.inst.account_name}

    def close(self):
        self.inst.connection.close()

    def cancel_query(self, id):
        self.inst.connection.cursor().execute("select system$cancel_query({0});".format(id))

    def metering_history(self):
        cur = self.inst.connection.cursor(DictCursor)
        cur.execute("select credits_used, start_time from snowflake.account_usage.warehouse_metering_history")

        # Data Transformations
        history = []
        for rec in cur:
            rec['START_TIME'] = rec['START_TIME'].astimezone(timezone("US/Eastern"))
            rec['CREDITS_USED'] = float(rec['CREDITS_USED'])
            history.append(rec)
        history.sort(key=itemgetter("START_TIME"))

        # Combine duplicate times / consolidate warehouse entries
        history_combined = [history[0]]
        for i in range(1, len(history)):
            if history[i]['START_TIME'] == history[i-1]['START_TIME']:
                history_combined[-1]['CREDITS_USED'] += history[i]['CREDITS_USED']
            else:
                history_combined.append(history[i])

        # Normalize to transform into interval data
        index_datetime = history_combined[0]['START_TIME'].replace(day=1, hour=0) # start from first hour of the month
        count = 0
        history_normalized = []
        while count < len(history_combined): # While there is still data to process
            if  ((index_datetime - history_combined[count]['START_TIME']).days == 0 and
                (index_datetime - history_combined[count]['START_TIME']).seconds == 0): # same datetime down to the second
                history_normalized.append(history_combined[count])
                count += 1
            else:
                history_normalized.append({'CREDITS_USED': 0, 'START_TIME': index_datetime}) # fill in data gaps with 0 entry
            index_datetime += datetime.timedelta(hours=1) # iterator
            index_datetime = index_datetime.astimezone(timezone("US/Eastern")) # timezone doesnt change properly over DST
        last_record =  history_combined[-1]['START_TIME']
        last_datetime = last_record.replace(month=last_record.month + 1, day=1,hour=0) - datetime.timedelta(hours=1) #fill out remaining hours in last day and rest of month
        while not ((index_datetime - last_datetime).days == 0 and (index_datetime - last_datetime).seconds == 0):
            history_normalized.append({'CREDITS_USED': 0, 'START_TIME': index_datetime})
            index_datetime += datetime.timedelta(hours=1)
            index_datetime = index_datetime.astimezone(timezone("US/Eastern"))
        #normalize query data into intervals
        queries = self.query_user_usage() # Get entire query history statistics
        queries_normalized = {} #keyed by day
        for query in queries:
            day = query['START_TIME'].strftime("%Y-%m-%d")
            user = query['USER_NAME']
            if day not in queries_normalized:
                queries_normalized[day] = {'total': 0, 'users': {}}
            if user not in queries_normalized[day]['users']:
                queries_normalized[day]['users'][user] = {'time': 0}
            queries_normalized[day]['total'] += query['TOTAL_ELAPSED_TIME']
            queries_normalized[day]['users'][user]['time'] += query['TOTAL_ELAPSED_TIME']
        #calculate the % share of time that each user occupies
        for day in queries_normalized:
            for user in queries_normalized[day]['users']:
                user_time = queries_normalized[day]['users'][user]['time']
                total_time = queries_normalized[day]['total']
                queries_normalized[day]['users'][user]['share'] = round(user_time / total_time * 100.00, 2)
                queries_normalized[day]['users'][user]['time'] = '{0}s'.format(round(queries_normalized[day]['users'][user]['time'] / 1000.00, 2))
            queries_normalized[day]['total'] = '{0}s'.format(round(queries_normalized[day]['total'] / 1000.00, 2))

        # Structure the interval data into a tree structure:
        # month_index: {
        #     day_index:{
        #         interval: {
        #             0: x1 (hourly interval data)
        #             1: x2
        #             ...
        #             23: x24
        #         }
        #         credits: sum(x_i)
        #         *total_time: sum(y_j)
        #         *users: {
        #             user0: {
        #                 time: y_0
        #                 share: time / total_time * 100 (%)
        #             },
        #             ...
        #         }
        #     }
        # }
        # * Fields present only for dates in past one week; Snowflake only keeps one week of query logs

        month_abbrev = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]
        history_structured = {}
        for item in history_normalized:
            month_index = month_abbrev[item['START_TIME'].month - 1] + ", " + str(item['START_TIME'].year)
            day_index = item['START_TIME'].day
            hour_index = item['START_TIME'].hour
            credits = item['CREDITS_USED']
            if month_index not in history_structured:
                history_structured[month_index] = {}
            if day_index not in history_structured[month_index]:
                history_structured[month_index][day_index] = {'interval': {}, 'credits': 0}
                day = item['START_TIME'].strftime("%Y-%m-%d")
                if day in queries_normalized:
                    time_data = queries_normalized[item['START_TIME'].strftime("%Y-%m-%d")]
                    history_structured[month_index][day_index]['users'] = time_data['users']
                    history_structured[month_index][day_index]['total_time'] = time_data['total']
            history_structured[month_index][day_index]['credits'] += credits
            history_structured[month_index][day_index]['interval'][hour_index] = credits
        #rounding of all credit values to 2 decimal places, including daily totals
        for month in history_structured:
            for day in history_structured[month]:
                history_structured[month][day]['credits'] = round(history_structured[month][day]['credits'], 2)
                for hour in history_structured[month][day]['interval']:
                    history_structured[month][day]['interval'][hour] = round(history_structured[month][day]['interval'][hour], 2)
        return history_structured


    def query_user_usage(self, start_date=datetime.datetime.now(timezone("US/Eastern")) - datetime.timedelta(hours=166),
                         end_date=datetime.datetime.now(timezone("US/Eastern"))):
        cur = self.inst.connection.cursor(DictCursor)
        history = []
        try:
            cur.execute("select user_name, start_time, total_elapsed_time from "
                        "table(snowflake.information_schema.query_history("
                        "end_time_range_start=> to_timestamp_ltz(\'{0}\'), "
                        "end_time_range_end=> to_timestamp_ltz(\'{1}\'))) "
                        "order by start_time".format(start_date.strftime("%Y-%m-%d %H:%M:%S %z"), end_date.strftime("%Y-%m-%d %H:%M:%S %z")))
            for rec in cur:
                # Data Transformations
                rec['START_TIME'] = rec['START_TIME'].astimezone(timezone("US/Eastern"))
                history.append(rec)
        except snowflake.connector.ProgrammingError as e0:
            print(e0.msg)
        return history


    def query_user_history(self, numMinutes=30, ongoingOnly=False): # Defaults to all queries in the last 30 minutes
        cur = self.inst.connection.cursor(DictCursor)
        start_date = datetime.datetime.now(timezone("US/Eastern")) - datetime.timedelta(minutes=int(numMinutes))
        history = []
        try:
            cur.execute("select query_id, query_text, user_name, warehouse_name, execution_status, error_code, error_message, start_time, end_time, total_elapsed_time from "
                        "table(snowflake.information_schema.query_history("
                        "end_time_range_start=> to_timestamp_ltz(\'{0}\'))) "
                        "where user_name not like \'%ALERTS%\'"
                        "order by start_time".format(start_date.strftime("%Y-%m-%d %H:%M:%S %z")))
            for rec in cur:
                # Data Transformations
                rec['START_TIME'] = rec['START_TIME'].astimezone(timezone("US/Eastern"))
                rec['END_TIME'] = rec['END_TIME'].astimezone(timezone("US/Eastern"))
                if not (rec['EXECUTION_STATUS'] == 'FAILED_WITH_ERROR' or rec['EXECUTION_STATUS'] == 'FAILED_WITH_INCIDENT'):
                    rec.pop('ERROR_MESSAGE')
                    rec.pop('ERROR_CODE')
                minutes = int(rec['TOTAL_ELAPSED_TIME'] / 60000.0)
                seconds = (rec['TOTAL_ELAPSED_TIME'] / 1000.0) % 60.000
                time_string = '{0}s'.format(seconds)
                if minutes > 0:
                    time_string = '{0}m {1}s'.format(minutes, round(seconds))
                if int(rec['TOTAL_ELAPSED_TIME']) < 0:
                    rec['TOTAL_ELAPSED_TIME'] = '0.0s'
                    rec['END_TIME'] = rec['START_TIME']
                else:
                    rec['TOTAL_ELAPSED_TIME'] = time_string
                if ongoingOnly:
                    if rec['EXECUTION_STATUS'] == 'RESUMING_WAREHOUSE' or rec['EXECUTION_STATUS'] == 'RUNNING' or rec['EXECUTION_STATUS'] == 'QUEUED':
                        history.append(rec)
                else:
                    history.append(rec)
        except snowflake.connector.ProgrammingError as e0:
            print(e0.msg)
        history.reverse()
        return history

    def stop_query(self, id):
        message = self.inst.connection.cursor().execute("select system$cancel_query(\'{0}\')".format(id)).fetchone()
        if message[0] != 'Identified SQL statement is not currently executing.':
            status, error_message, error_code, start_time, end_time = self.inst.connection.cursor().execute(
                "select execution_status, error_message, error_code, start_time, end_time from "
                "table(snowflake.information_schema.query_history("
                "end_time_range_start=> to_timestamp_ltz(\'{0}\'))) "
                "where query_id = \'{1}\'"
                .format(datetime.datetime.now(timezone("US/Eastern")) - datetime.timedelta(minutes=1), id)).fetchone()
            obj = {'id': id, 'status': status, 'message': message[0], 'start_time': start_time, 'end_time': end_time}
            if error_message is not None:
                obj['error_message'] = error_message
                obj['error_code'] = error_code
            return obj
        else:
            return {'id': id, 'status': 'SUCCESS', 'message': message[0]}

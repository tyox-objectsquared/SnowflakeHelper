import snowflake.connector
from snowflake.connector import DictCursor
from pytz import timezone

class SnowflakeAccess:

    inst = None

    class __SAO:  #snowflake access object, private
        def __init__(self, username, password, account_name):
            try:
                self.connection = snowflake.connector.connect(user=username, password=password, account=account_name)
            except snowflake.connector.errors.DatabaseError as e0:
                print(e0.msg)
            self.username = username
            self.account_name = account_name
            self.region = account_name.split(".")[1]
        def __str__(self):
            return repr(self) + "\n\tusername: " + self.username + "\n\taccount: " + self .account_name


    def __init__(self, username, password, account_name):
        if not SnowflakeAccess.inst:
            SnowflakeAccess.inst = SnowflakeAccess.__SAO(username, password, account_name)
        else:
            try:
                SnowflakeAccess.inst.connection = snowflake.connector.connect(user=username, password=password, account=account_name)
            except snowflake.connector.errors.DatabaseError as e0:
                print(e0.msg)
    def __getattr__(self, name):
        return getattr(self.inst, name)


    def close(self):
        self.inst.connection.close()


    def query_user_history(self, num_minutes, ongoing_only, username=None):
        cur = self.inst.connection.cursor(DictCursor)
        queries = []
        try:
            if username != None:
                cur.execute("select * from "
                            "table( snowflake.information_schema.query_history_by_user( "
                            "user_name=> \'" + username + "\', "
                            "end_time_range_start=> dateadd(\'minutes\', -" + str(num_minutes) + ", current_timestamp()))) "
                            "order by start_time")
            else:
                cur.execute("select * from "
                            "table( snowflake.information_schema.query_history( "
                            "end_time_range_start=> dateadd(\'minutes\', -" + str(num_minutes) + ", current_timestamp()))) "
                            "order by start_time")
            for rec in cur:
                rec['START_TIME'] = rec['START_TIME'].astimezone(timezone("US/Eastern")).strftime("%I:%M%p")
                rec['END_TIME'] = rec['END_TIME'].astimezone(timezone("US/Eastern")).strftime("%I:%M%p")
                minutes = int(rec['TOTAL_ELAPSED_TIME'] / 60000.0)
                seconds = (rec['TOTAL_ELAPSED_TIME'] / 1000.0) % 60.000
                time_string = '{0}s'.format(seconds)
                if minutes > 0:
                    time_string = '{0}m'.format(minutes) + time_string
                if int(rec['TOTAL_ELAPSED_TIME']) < 0:
                    rec['TOTAL_ELAPSED_TIME'] = '0.0s'
                else:
                    rec['TOTAL_ELAPSED_TIME'] = time_string
                if ongoing_only:
                    if (rec['EXECUTION_STATUS'] == 'RESUMING_WAREHOUSE' or rec['EXECUTION_STATUS'] == 'RUNNING' or rec['EXECUTION_STATUS'] == 'QUEUED'):
                        queries.append(rec)
                else:
                    queries.append(rec)
        except snowflake.connector.ProgrammingError as e0:
            print(e0.msg)
        return queries


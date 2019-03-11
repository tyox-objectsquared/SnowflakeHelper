#Snowflake Alerts Console
A containerized web interface for SEDC's cooperative reader accounts to monitor and manage their Snowflake usage

####Features
- Login using existing Snowflake credentials (user)
- Browse past queries and view currently running queries (user)
- Kill problematic queries (mgmt)
- Manage users on the reader account (mgmt)
- View credits used by both the individual (user) and the account (mgmt)

#####Docker Commands
- docker build -t SnowflakeAlerts:latest
- docker run -d -p 80:5000 SnowflakeAlerts

####Tech Stack
#####Backend:
- Flask REST API
- Snowflake Python Connector

#####Frontend:
- Angular 6
- Bootstrap
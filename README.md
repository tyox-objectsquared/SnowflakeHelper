# Snowflake Helper
A containerized web interface for SEDC's cooperative reader accounts to monitor and manage their Snowflake usage

#### Features
- Login using existing Snowflake credentials
- Change Snowflake password
- Change Snowflake email address
- View past queries and currently running queries
- Stop problematic queries quickly
- View utilization time distribution between users for recent queries

##### Docker Commands
- Build: docker build -t {docker_username}/snowflake-helper:{version} .
- Run: docker run -p 5000:5000 -p 3000:3000 --name SnowflakeHelper {docker_username}/snowflake-helper:{version}

#### Tech Stack
##### Backend (Python):
- Flask REST API
- Snowflake Python Connector
##### Frontend (NodeJS):
- React + NodeJS libraries
- Bootstrap
# Snowflake Helper
A web interface for SEDC's cooperative reader accounts to monitor and manage their Snowflake usage

#### Features
- Login using existing Snowflake credentials
- Change Snowflake password
- Change Snowflake email address
- View past queries and currently running queries
- Stop problematic queries quickly
- View utilization time distribution between users for recent queries

##### Running
Install + Start scripts are located in the ./run directory.

##### Docker Commands (from ./run/Docker context)
- Build: docker-compose build
- Run (also builds if not yet built): docker-compose up
- Stop: docker-compose stop
- Stop + Clean: docker-compose down 

#### Current Tech Stack
##### Backend (Python 3.7.2):
- Flask REST API
- Snowflake Python Connector
- pytest Testing Module
##### Frontend (NodeJS 11.4.0):
- React + NodeJS libraries
- Bootstrap styling
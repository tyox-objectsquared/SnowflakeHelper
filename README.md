# Snowflake Helper
A containerized web interface for SEDC's cooperative reader accounts to monitor and manage their Snowflake usage

#### Features
- Login using existing Snowflake credentials
- Change Snowflake password
- Change Snowflake email address
- View past queries and currently running queries
- Stop problematic queries quickly
- View utilization time distribution between users for recent queries

##### Docker Commands (from project root-dir context)
- Build: docker-compose build
- Run (also builds if not yet built): docker-compose up
- Stop: docker-compose stop
- Stop + Clean: docker-compose down 

#### Tech Stack
##### Backend (Python):
- Flask REST API
- Snowflake Python Connector
##### Frontend (NodeJS):
- React + NodeJS libraries
- Bootstrap
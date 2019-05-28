::Requires Python w/ pip to run

::Setup logging
@echo off
cd ..\..\..
mkdir logs\start_api
set timestamp=%DATE:/=-%_%TIME::=-%
set timestamp=%timestamp: =%
set log_path="%cd%/logs/start_api/%timestamp%.log"


::Install then Run virtualenv
pip install virtualenv >_ && type _ && type _ > %log_path%
cd ./sfh_api
virtualenv venv  >_ && type _ && type _ >> %log_path%
call venv\Scripts\activate >_ && type _ && type _ >> %log_path%


::Install Required Modules
pip install --upgrade pip >_ && type _ && type _ >> %log_path%
pip install -r requirements.txt >_ && type _ && type _ >> %log_path%


::Unit Tests - optional
if "%1"=="\t" (
    pytest tests\unit\test_app.py >_ && type _ && type _ >> %log_path%
)


::Run Flask Server
del /f ./_
echo on
python src\main.py
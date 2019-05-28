::Requires NodeJS w/ npm and yarn

::Setup logging
@echo off
cd ..\..\..
mkdir logs\start_webapp
set timestamp=%DATE:/=-%_%TIME::=-%
set timestamp=%timestamp: =%
set log_path="%cd%/logs/start_webapp/%timestamp%.log"


::Install npm packages
cd ./webapp
call npm install >_ && type _ && type _ >> %log_path%


::Build the package
call npm run-script build >_ && type _ && type _ >> %log_path%


::Serve the package
::yarn global add serve >_ && type _ && type _ >> %log_path%
echo on
del /f .\_
npx serve -p 80 ./build

PAUSE

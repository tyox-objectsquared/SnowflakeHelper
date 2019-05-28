<#Requires Python w/ pip to run#>
param([string]$testing = "no")
<#Setup logging#>
cd ../../..
if ( -not(Test-Path ./logs) ) {mkdir logs}
if ( -not(Test-Path ./logs/start_api) ) {mkdir logs/start_api}
$date=Get-Date -UFormat "%Y-%m-%d-%H-%M-%S"
$log_path= "" + (Get-Location) + "/logs/start_api/" + $date + ".log"


<#Install then Run virtualenv#>
pip install virtualenv | Tee-Object -FilePath $log_path
cd ./sfh_api
virtualenv venv | Tee-Object -Append -FilePath $log_path
call venv\Scripts\activate | Tee-Object -Append  -FilePath $log_path


<#Install Required Modules#>
pip install --upgrade pip | Tee-Object -Append  -FilePath $log_path
pip install -r requirements.txt | Tee-Object -Append  -FilePath $log_path


<#Unit Tests#>
if ($testing -eq "yes")
{pytest tests\unit\test_app.py | Tee-Object -Append  -FilePath $log_path}


<#Run Flask Server#>
python src\main.py
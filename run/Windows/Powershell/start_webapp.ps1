<#Requires Python w/ pip to run#>

<#Setup logging#>
cd ../../..
if ( -not(Test-Path ./logs) ) {mkdir logs}
if ( -not(Test-Path ./logs/start_webapp) ) {mkdir logs/start_webapp}
$date=Get-Date -UFormat "%Y-%m-%d-%H-%M-%S"
$log_path= "" + (Get-Location) + "/logs/start_webapp/" + $date + ".log"


<#Build the package#>
cd ./webapp
yarn | Tee-Object -Append -FilePath $log_path
yarn build | Tee-Object -Append  -FilePath $log_path


<#Serve the package#>
yarn global add serve | Tee-Object -Append  -FilePath $log_path
npx serve -p 80 ./build
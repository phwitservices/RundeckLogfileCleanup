# RundeckLogfileCleanup
Python script to remove old Rundeck executions and log files

The default properties file is properties.json and this must be in the same directory as the script. Otherwise, pass the full filepath of a properties file as the only argument to the script.
The properties file has the format

{
	"RUNDECKSERVER": "rundeck server name or IP address",
	"PORT": 4440,
	"API_KEY": "API Key with correct privileges",
	"PAGE_SIZE": 1000,
	"MAXIMUM_DAYS": 90,
	"TIMEOUT": 60,
	"DELETE_TIMEOUT": 1200,
	"VERBOSE": false
}

You should put your own Rundeck server name and API key in the appropriate places. Choose how long you want to keep log files for with the MAXIMUM_DAYS variable, the default removes jobs after 90 days. The script completely removes the execution from the Rundeck database and the log file from disk - there's no going back once this is done!

The other settings should be OK for most installs.

If the job keeps timing out try setting a smaller PAGE_SIZE which will query jobs in smaller batches. The first time you run this script it will probably take a while, if you run it regularly after that then the number of deletions should be lower and the script will therefore execute more quickly.

The script is tested and working on v2.4.0-1 "americano indigo briefcase". I've tried on a v2.2 installation and the job execution format seems to be different.
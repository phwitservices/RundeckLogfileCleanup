#!/usr/bin/python
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import xml.etree.ElementTree as ET
import time
import json
import sys

# Returns list of all the project names
def get_projects():
    global PROPERTIES
    global HEADERS
    project_names = []
    try:
        url = URL + 'projects'
        r = requests.get(url, headers=HEADERS, verify=False,timeout=PROPERTIES['TIMEOUT'])
        root = ET.fromstring(r.text)
        for project in root:	
            for name in project.findall('name'):
                project_names.append(name.text)
    except:
        print "Problem with project listing {0}".format(r)
        pass
    return project_names   

# Returns list of all the jobids
def get_jobs_for_project(project_name):
    global PROPERTIES
    global HEADERS
    job_ids = []
    try:
        url = URL + 'jobs'
        payload = { 'project':  project_name }
        r = requests.get(url, params=payload, headers=HEADERS, verify=False,timeout=PROPERTIES['TIMEOUT'])    
        root = ET.fromstring(r.text.encode('utf-8'))	
        for job in root:
            job_ids.append( (job.attrib['id'],job.find('name').text) )
    except:
        print "Problem with job listing {0}".format(r)
        pass
    return job_ids

# API call to get a page of the executions for a particular job id      
def get_executions_for_job(job_id,page):
    global PROPERTIES
    global HEADERS
    root = None
    try:
        url = URL + 'job/'+job_id+'/executions'
        r = requests.get(url, params={'max':PROPERTIES['PAGE_SIZE'],'offset':page*PROPERTIES['PAGE_SIZE']}, headers=HEADERS, verify=False,timeout=PROPERTIES['TIMEOUT'])
        root = ET.fromstring(r.text.encode('utf-8'))
    except:
        print "Problem with execution listing {0}".format(r)
        pass
    return root

#
# Return a dictionary of execute ids & dates
#
def get_execution_dates(root):
    execid_dates = {}
    try:
        for execution in root:
            execution_id = execution.get('id')
            for date in execution.findall('date-ended'):
                execution_date = date.get('unixtime')
            execid_dates[execution_id] = execution_date
    except:
        pass
    return execid_dates
       
#API call to delete an execution by ID
def delete_execution(execution_id):
    global PROPERTIES
    global HEADERS
    url = URL + 'execution/'+execution_id
    try:
        r = requests.delete(url, headers=HEADERS, verify=False,timeout=PROPERTIES['TIMEOUT'])
        if PROPERTIES['VERBOSE']:
            print "            Deleted execution id {0} {1} {2}".format( execution_id, r.text, r )
    except:
        pass

#API call to bulk delete executions by ID
def delete_executions(execution_ids):
    global PROPERTIES
    global HEADERS
    url = URL + 'executions/delete'
    try:
        r = requests.post(url, headers=HEADERS, data= json.dumps({'ids':execution_ids}) , verify=False,timeout=PROPERTIES['DELETE_TIMEOUT'])
        if PROPERTIES['VERBOSE']:
            print "            Deleted execution ids {0}".format( execution_ids, r.text, r )
    except:
        try:
            print "Problem with execution deletion {0}".format(r)
        except:
            pass
        pass
    
def delete_test(execution_date):
    global PROPERTIES
    global TODAY
    millis_in_one_day = 1000*60*60*24
    return ((TODAY - execution_date) > millis_in_one_day * PROPERTIES['MAXIMUM_DAYS'])

def check_deletion(execid_dates):
    delete= ()
    for exec_id, exec_date in execid_dates.iteritems():
        if delete_test( int(exec_date) ):
            delete  += (exec_id,)
    print "        Delete {0} jobs from this page".format( len(delete) )
    return delete

#
# Main
#
setting_filename = sys.argv[1] if len(sys.argv)>1 else 'properties.json'
with open(setting_filename,'r') as props_file:    
    PROPERTIES = json.load( props_file )

protocol='http'
if PROPERTIES['SSL']:
	protocol='https'
	# disable warnings about unverified https connections
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

URL = '{0}://{1}:{2}/api/{3}/'.format(protocol,PROPERTIES['RUNDECKSERVER'],PROPERTIES['PORT'],PROPERTIES['API_VERSION'])
HEADERS = {'Content-Type': 'application/json','X-RunDeck-Auth-Token': PROPERTIES['API_KEY'] }

TODAY = int(round(time.time() * 1000))

for project in get_projects():
    print project
    for (jobid,jobname) in get_jobs_for_project(project):
        print "    {0}".format(jobname.encode('utf-8'))
        page = 0
        deleteable = ()
        more = True
        while more :
            try:
                execution_root = get_executions_for_job(jobid,page)
                print "        Page {0} got {1} jobs".format(page,execution_root.attrib['count'])
                page += 1
                deleteable += check_deletion(get_execution_dates(execution_root))
                more = int(execution_root.attrib['count']) == PROPERTIES['PAGE_SIZE']
            except:
                print "Problem with executions {0} {1}".format(execution_root,sys.exc_info()[0])
                more = False
        if (len(deleteable) > 0 ):
            print "        Deleting {0} jobs in total".format( len(deleteable) )
            delete_executions(deleteable)

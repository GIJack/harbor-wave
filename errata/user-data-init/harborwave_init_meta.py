#!/usr/bin/env python
# exit codes 0-success, 1-operation error, 2-condition error
prog_desc='''
Download initialize harbor-wave data from Digital Ocean's API, so its available
for the system
'''

import sys,os
import json
import urllib.request
from http.client import responses as http_responses
from datetime import datetime

config = {
    'host'        : '169.254.169.254',
    'path'        : '/metadata/v1/user-data',
    'timeout'     : 3, # timeout, in seconds, for URL query
    'logfile'     : "/var/log/harbor-wave-init.log",
    'app-dir'     : '/opt/harborwave',
    'done-file'   : '/opt/harborwave/done',
    'needed-keys' : ['sequence', 'base-name', 'payload', 'payload-filename','domain','total_vms'],
}

def message(message):
    print_message = "harborwave_initlization: " + message
    print(print_message)
    do_log(print_message)

def exit_with_error(error,message):
    print_message = "harborwave_initlization ¡ERROR!: " + message
    print(print_message, file=sys.stderr)
    do_log(print_message)
    sys.exit(error)

def submsg(message):
    print_message = "[+]\t" + message
    print(print_message)
    do_log(print_message)
        
def warn(message):
    print_message="harborwave_initlization: ¡WARN!: " + message
    print(print_message, file=sys.stderr)
    do_log(print_message)

def do_log(message):
    time_obj   = datetime.now()
    time_stamp = time_obj.ctime()
    out_message = time_stamp + "\t" + message + "\n"
    log_obj = open(config['logfile'],'a')
    log_obj.write(out_message)
    log_obj.close()

def get_data(config):
    '''get the data and return it as a dict, takes the config array'''
    get_url     = "http://" + config['host'] + config['path']
    
    # do URL call, and check for errors, both in fetching and any codes from
    # the server
    try:
        response = urllib.request.urlopen(get_url,timeout=config['timeout'])
    except:
        exit_with_error(1,"Could not retrieve data from API!")
    if response.code != 200:
        exit_with_error(1,"HTTP Error " + response.code + ": " + http_responses[response.code])
    
    # now, get a python dict from the response
    raw_data    = response.read()
    output_data = raw_data.decode()
    try:
        output_data = json.loads(output_data)
    except:
        exit_with_error(9,"Data isn't in the JSON format, are you sure this is a harbor-wave VM?")
    
    # check to make sure all fields are there
    data_keys = output_data.keys()
    missing_keys = []
    for item in config['needed-keys']:
        if item not in data_keys:
            missing_keys.appennd(item)
    if missing_keys != []:
        missing_keys = ",".join(missing_keys)
        exit_with_error(9,"Missing JSON items" + missing keys + ": are you sure this is a harbor-wave VM?")
    
    return output_data

def write_environment(data):
    '''Add sequence and base-name to /etc/environment.'''
    env_file = '/etc/environment'
    out_lines  = "HARBORWAVE_SEQEUNCE="  + str(data['sequence']) + "\n"
    out_lines += "HARBORWAVE_TOTAL_VMS=" + str(data['total_vms']) + "\n"
    out_lines += "HARBORWAVE_BASENAME="  + data['base-name'] + "\n"
    out_lines += "HARBORWAVE_DOMAIN="    + data['domain'] + "\n"
    try:
        file_obj = open(env_file,'a')
        file_obj.write(out_lines)
        file_obj.close()
    except:
        warn("Could not write to " + env_file)
        return 1
        
    return 0

def write_payload(data):
    '''write payload file'''
    
    payload_dir = config['app-dir'] + "/payload"
    os.makedirs(payload_dir,mode=0o755,exist_ok=True)
    if data['payload-filename'] != "":
        payload_file = payload_dir + "/" + data['payload-filename']
    else:
        payload_file = payload_dir + "/data"
    try:
        file_obj = open(payload_file,"w")
        file_obj.write(data['payload'])
        file_obj.close()
    except:
        warn("Could not write payload to " + payload_file)
        return 1
    
    return 0

def write_done():
    '''Touch /opt/harbor-wave/done so we know this script ran already'''
    done_file = config['done-file']
    try:
        file_obj = open(done_file,"w")
        file_obj.write("\n")
        file_obj.close()
    except:
        warn("Could not write donefile, the script will repeat!")
        return 1

    return 0

def main():
    message("Getting and parsing Harbor-Wave data from Digital Ocean API")
    WARNS = 0
    # Check if this script ran already
    if os.path.exists(config['done-file']) == True:
        warn("Script ran already, doing nothing and exiting")
        sys.exit(0)
    
    # ensure directory is available
    os.makedirs(config['app-dir'],mode=0o755,exist_ok=True)
    
    submsg("Retrieving Data")
    data = get_data(config)
    
    submsg("Writing to environment file")
    WARNS += write_environment(data)
    
    submsg("Extracting payload")
    WARNS += write_payload(data)
    
    submsg("Writing donefile")
    WARNS += write_done()
    
    if WARNS > 0:
        message("Done, but with " + WARNS + " warning(s)")
        sys.exit(1)
    else:
        message("Done")

if __name__ == "__main__":
    main()

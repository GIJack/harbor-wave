#!/usr/bin/env python3
# exit codes 0-success, 1-operation error, 2-condition error

prog_desc='''Manage Templates for Harbor Wave.

Create/List/Destroy.

Needs a digital ocean API key and an S3 Bucket(DO Spaces), you can upload to.

Works hand-in-hand with disk-image-scripts if you are uploading a compiled
project from within the template dir it will fill in information from the
template.rc
'''

import argparse
import os,sys
import boto3
import digitalocean

default_config = {
}

class colors:
    '''pretty terminal colors'''
    reset='\033[0m'
    bold='\033[01m'
    red='\033[31m'
    cyan='\033[36m'
    yellow='\033[93m'

def message(message):
    print("harbor-template: " + message)

def exit_with_error(exit,message):
    print("harbor-template" + colors.red + colors.bold + " ¡ERROR!: " + colors.reset + message, file=sys.stderr)
    sys.exit(exit)

def submsg(message):
    print("\t" + message)
    
def warn(message):
    print("harbor-template:" + colors.yellow + colors.bold + " ¡WARN!: " + colors.reset + message, file=sys.stderr)
    return

def main():
    parser = argparse.ArgumentParser(description=full_help_banner,epilog="\n\n",add_help=False,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", nargs="?"    ,help="See above for description of commands")
    parser.add_argument("arguments", nargs="*"  ,help="Arguments for command, see above")
    parser.add_argument("-?","--help"           ,help="Show This Help Message", action="help")
    parser.add_argument("-T","--terse"          ,help="terse output, for scripting",action="store_true")

    args = parser.parse_args()
    
    # get config from file
    config_dir = os.getenv("HOME") + "/.config/harbor-wave/"

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# exit codes 0-success, 1-operation error, 2-condition error

prog_desc='''Manage Templates for Harbor Wave.

Create/List/Destroy.

Needs a digital ocean API key and an S3 Bucket(DO Spaces), you can upload to.

Works hand-in-hand with disk-image-scripts if you are uploading a compiled
project from within the template dir it will fill in information from the
template.rc
'''
command_help='''
			COMMANDS:

  help <topic> - brief overview. if topic is specified then only the relevant
  entries for that topic are printed.
  
  help topics: config, commands
  
  list [what] - list things. Use the --terse option for CSV output.
  Subcommands/arguments:
  
      templates  - Show custom droplet templates in digitalocean(can be used).
      
      files      - Show files in S3/spaces bucket.
  
  set [item] [value]  - set a config item. See bellow for list of config items.
  Setting a value of "" will reset this item to its default value

  get [item]          - print value for item, see bellow for list of config items
  
  print-config        - print all config items in pretty table.
  
  add [what] - add an item
  subcommands/arguments:
      
      template [options]   - add custom droplet template. format tbd
  
  delete [what] - delete from your account.
  Subcommands/arguments:
  
      template [id]   - delete custom template from Digital Ocean
      
      file [filename] - delete file from Spaces/S3 bucket.
  
  clean               - delete all files in the S3/spaces bucket
'''
config_help='''
        CONFIG ITEMS:

   api-key       - Digital Ocean API key, used for accessing the account. NOTE this
   is the only option that does NOT go in the .cfg file, but rather the seperate
   api-key file. Shared setting with harbor-wave
   
   bucket        - S3 compatable bucket(DigitalOcean Spaces) to use for uploads
   
   bucket_key    - API key to use for uploads to bucket
   
   bucket_secret - API secret to use for uploads to bucket
'''
full_help_banner=prog_desc+command_help+config_help


import argparse
import os,sys
import boto3
import digitalocean

default_config = {
  "bucket"    : "",
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
    
def check_and_load_config(config_dir):
    '''Runs on startup: checks and loads config file. missing entries are added, missing config files are made. takes one parameter: filename for config dir'''
    
    # Mabey we should put these somewhere else? idk, top level dict?
    config_file_name = "harbor-master.cfg"
    api_file_name    = "api-key"
    
    # These will be loaded with actual values later. Value None means load 
    # failed
    loaded_config    = None
    loaded_api_key   = None
    
    # check if config directory exists. If not make it:
    if os.path.isdir(config_dir) == False and os.path.exists(config_dir) == True:
        raise FileNotFoundError("Config directory not found")
    elif os.path.exists(config_dir) == False:
        os.makedirs(config_dir,mode=0o750,exist_ok=True)
    
    # Check config file
    config_file = config_dir + "/" + config_file_name
    
    # check if config file exists, if not make it then return defaults:
    # If the config file exists, load it
    if os.path.isfile(config_file)   == False and os.path.exists(config_file) == True:
        raise FileNotFoundError("Config file not found")
    elif os.path.exists(config_file) == False:
        write_config(config_file,default_config) #TODO write default_config
        os.chmod(config_file, 0o640)
        loaded_config = default_config
    else:
        # load config from file, after we are sure it exists
        file_obj = open(config_file,"r")
        contents = file_obj.read()
        file_obj.close()
        loaded_config = json.loads(contents)
    # Double check we've got a loaded config.
    if loaded_config == None:
        raise RuntimeError("Loading configuration file failed.")
    # check to make sure all items are present. If not, use defaults
    for item in default_config.keys():
        if item not in loaded_config.keys():
            loaded_config[item] = default_config[item]
    # now, re-write updated config
    try:
        write_config(loaded_config)
    except:
        pass

    # If API-key file exists, load API-key
    api_file = config_dir + "/" + api_file_name
    if os.path.isfile(api_file) == False and os.path.exists(api_file) == True:
        raise RuntimeError("Loading API Key file failed")
    elif os.path.exists(api_file) == True:
        try:
            file_obj = open(api_file,"r")            
            loaded_api_key = file_obj.read()
            file_obj.close()
            # add API Key to the config
            loaded_config['api-key'] = loaded_api_key
        except:
            warn("could not read API key from api-key file, check permissions")
    else:
        loaded_config['api-key'] = None

    return loaded_config

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

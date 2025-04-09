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
  Setting a value of "" will reset this item to its default value.

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

  api-key            - digital ocean API key. NOTE: This setting is
  shared with harbor-wave, setting in one affects the other
      
  bucket             - Spaces/S3 Bucket URL. This is where you upload
  template files before being added
      
  bucket-key-name    - Spaces/S3 bucket key name
     
  bucket-key-seceret - Spaces/S3 bucket key secret
'''
full_help_banner=prog_desc+command_help+config_help


import argparse
import os,sys
import boto3
import digitalocean

default_config = {
  "bucket"    : "",
  "bucket_key_name" : "",
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

def check_api_key(key):
    '''checks if API key is valid format. returns True/False. Takes one parameter, the key'''
    # a DO access key is 64 characters long, hexidecimal, new format has
    # meta headers before the hexdec
    key_len = 64
    base    = 16
    # Strip headers, if present
    key = key.split('_')[-1]
    # Key is a string
    if type(key) != str:
        return False
    # Key is 64 characters long
    if len(key) != key_len:
        return False
    # Key is hexdecimal
    try:
        int(key,base)
    except:
        return False
    # No more tests
    return True

def check_and_connect(loaded_config):
    '''give the loaded config, check the API key, and return a DO manager session'''
    
    # check to make sure we have the right config options
    needed_keys = ("api-key")
    for key in needed_keys:
        if key not in loaded_config.keys():
            exit_with_error(2,key + " not set. see help config")
    
    api_key = loaded_config['api-key']
    if check_api_key(api_key) != True:
        exit_with_error(2,"Invalid API Key")
        
    # get open a session
    manager = digitalocean.Manager(token=api_key)
    
    return manager
    
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

def list_templates(loaded_config,terse=False):
    '''List available templates to make machines from. Takes one parameter, the config dict '''    
    # get images
    manager = check_and_connect(loaded_config)
    try:
        all_images = manager.get_my_images()
    except digitalocean.DataReadError:
        exit_with_error(2,"list: DataReadError, check settings and try again")
    
    # Seperate out user uploaded images
    use_images = []
    for image in all_images:
        if image.type == "custom":
            use_images.append(image)
            
    #now print
    tab_size = 30
    banner = colors.bold + "ID\tREGIONS\tDESCRIPTION".expandtabs(tab_size) + colors.reset
    if terse == False:
        print(banner)
        for image in use_images:
            out_line = str(image.id) + "\t" + ",".join(image.regions) + "\t" + image.name
            out_line = out_line.expandtabs(tab_size)
            print(out_line)
    elif terse == True:
        for image in use_images:
            out_line = str(image.id) + "," + " ".join(image.regions) + "," + image.name
            print(out_line)
    else:
        exit_with_error(10,"list: templates: terse is neither true nor false. should not happen, debug")

ef print_config(loaded_config,terse=False):
    '''Fancy printing of all config items. if terse is True, then print a comma-field seperated ver for grep and cut'''
    restricted_list = ['api-key', 'bucket_key_secret']
    header_line= colors.bold + "ITEM\t\tVALUE".expandtabs(13) + colors.reset
    if terse == False:
        print(header_line)
        out_line=""
        for item in loaded_config:
            if item in restricted_list:
                value = "********"
            else:
                value = loaded_config[item]
                value = str(value)
            out_line = item + "\t\t" + value
            out_line = out_line.expandtabs(13)
            print(out_line)
    elif terse == True:
        for item in loaded_config:
            if item in restricted_list:
                value = "HIDDEN"
            else:
                value = loaded_config[item]
                value = str(value)
            out_line = item + ',' + value
            print(out_line)
    else:
        exit_with_error(9,"print-config: terse is neither True nor False, should never get here, debug!")

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

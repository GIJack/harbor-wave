#!/usr/bin/env python3
# exit codes 0-success, 1-operation error, 2-condition error

prog_desc='''Manage Templates for Harbor Wave.

Create/List/Destroy.

Needs a digital ocean API key and an S3 Bucket(DO Spaces), you can upload to.

Works hand-in-hand with disk-image-scripts if you are uploading a compiled
project from within the template dir it will fill in information from the
template.rc

For the template.rc format see here:
https://github.com/GIJack/disk-image-scripts/blob/master/default_template/template.rc
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
      
      regions    - Show all available regions from Digital Ocean
  
  set [item] [value]  - set a config item. See bellow for list of config items.
  Setting a value of "" will reset this item to its default value.

  get [item]          - print value for item, see bellow for list of config items
  
  print-config        - print all config items in pretty table.
  
  add [what] - add an item
  subcommands/arguments:
      
      template [filename] <template.rc>   - add custom droplet template. upload
      a file to the bucket and then add it as a Digital Ocean template for use
      with harbor-wave. fill in specifications from the disk-image-scripts
      template.rc. If no second filename is specified, there is an attempt to
      read it from current directory.
      
      region [template id] [regions] - add one or more regions to existing
      template.
  
  del [what] - delete from your account.
  Subcommands/arguments:
  
      template [id]   - delete custom template from Digital Ocean
      
      file [filename] - delete file from Spaces/S3 bucket.
      
      region [template id] [regions] - remove one or more regions to an existing
      template
  
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

#python imports
import argparse
import json
import os,sys
#third party imports
import boto3
import botocore
import digitalocean

default_config = {
  "bucket"          : "",
  "bucket-key-name" : "",
  "region"          : "nyc1",
}

class colors:
    '''pretty terminal colors'''
    reset='\033[0m'
    bold='\033[01m'
    red='\033[31m'
    cyan='\033[36m'
    yellow='\033[93m'

def message(message):
    print("harbor-master: " + message)

def exit_with_error(exit,message):
    print("harbor-master" + colors.red + colors.bold + " ¡ERROR!: " + colors.reset + message, file=sys.stderr)
    sys.exit(exit)

def submsg(message):
    print("\t" + message)
    
def warn(message):
    print("harbor-master:" + colors.yellow + colors.bold + " ¡WARN!: " + colors.reset + message, file=sys.stderr)
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
    needed_keys = ["api-key"]
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
    config_file_name       = "harbor-master.cfg"
    api_file_name          = "api-key"
    bucket_secret_filename = "bucket-key-secret"
    
    # These will be loaded with actual values later. Value None means load 
    # failed
    loaded_config         = None
    loaded_api_key        = None
    loaded_bucket_secret  = None
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

    #Load Bucket Secret key in same fashion
    bucket_secret_file = config_dir + "/" + bucket_secret_filename
    if os.path.isfile(bucket_secret_file) == False and os.path.exists(bucket_secret_file) == True:
        raise RuntimeError("Loading bucket secret file failed")
    elif os.path.exists(bucket_secret_file) == True:
        try:
            file_obj = open(bucket_secret_file,"r")            
            loaded_bucket_secret = file_obj.read()
            file_obj.close()
            # add API Key to the config
            loaded_config['bucket-key-secret'] = loaded_bucket_secret
        except:
            warn("could not read bucket secret from bucket secret file, check permissions")
    else:
        loaded_config['bucket-key-secret'] = None

    return loaded_config
    
def get_config(loaded_config,item):
    '''prints working config item, takes two options, dict with config items, and item you need'''
    # sensative items we will avoid printing.
    restricted_list = ['api-key','bucket-key-secret']
    if item not in loaded_config.keys():
        exit_with_error(2,"get: No such config item: " + item + ". See help config")
    
    output = loaded_config[item]
    if item in restricted_list:
        if item != "":
            output = "HIDDEN"
        else:
            output = ""
    else:
        output = str(output)
    print(output)

def set_config(config_dir,loaded_config,item,value):
    '''update config, vars loaded_config is a dict of values to write, the rest should be self explanitory'''
    bucket_secret_file_name = "bucket-key-secret"
    api_file_name      = "api-key"
    config_file_name   = "harbor-master.cfg"
    api_file           = "%s/%s" % (config_dir,api_file_name)
    config_file        = "%s/%s" % (config_dir,config_file_name)
    bucket_secret_file = "%s/%s" % (config_dir,bucket_secret_file_name)
    set_item_str       = ["api-key","bucket", "bucket-key-name","bucket-key-secret","region"]
    all_set_items      = set_item_str # + set_item_int + set_item_bool
    
    # Null value check
    if item == None or item == "":
        exit_with_error(2, "set: item name can't be blank")
    # Null set now resets to default
    elif item not in all_set_items:
        errormsg = "set: %s is not a valid config item, see help config" % (item)
        exit_with_error(2,errormsg)
    elif value == None or value == "":
        value = default_config[item]
    # Check and set type
    if item in set_item_str:
        try:
            value = str(value)
        except:
            errormsg = "set: invalid value for %s. Must resolve to a string" % (errormsg)
            exit_with_error(2,errormsg)
    elif item in set_item_int:
        try:
            value = int(value)
        except:
            errormsg = "set: invalid value for %s. must by an interger" % (item)
            exit_with_error(2,errormsg)
    elif item in set_item_bool:
        if value.lower() == "true" or value.lower() == "t" or value == "1":
            value = True
        elif value.lower() == "false" or value.lower() == "f" or value == "0":
            value = False
        else:
            errormsg = "set: invalid value for %s. must be True/False" % (item)
            exit_with_error(2,errormsg)

    # if item is an api key, check before set:
    if item == "api-key":
        if check_api_key(value) != True:
            exit_with_error(2,"set: Invalid API Key for api-key")
    else:
        # now update the config array, but not for the api-key
        loaded_config[item] = value
    
    # Make sure we keep secrets out of the main config
    del(loaded_config['api-key'])
    del(loaded_config['bucket-key-secret'])
    
    # write the config. Write API key and bucket secret to their own files,
    # otherwise save to the main config
    try:
        if item == "api-key":
            file_obj = open(api_file,"w")
            file_obj.write(value)
            file_obj.close()
            os.chmod(api_file, 0o600)
        elif item == "bucket-key-secret":
            file_obj = open(bucket_secret_file,"w")
            file_obj.write(value)
            file_obj.close()
            os.chmod(api_file, 0o600)
        else:
            write_config(config_file,loaded_config)
    except:
        exit_with_error(2,"set: Could not write to config file")

def write_config(file_name,config_obj):
    '''write config to JSON file'''

    contents  = json.dumps(config_obj,indent=4)
    contents += "\n"

    file_obj = open(file_name, "w")
    file_obj.write(contents)
    file_obj.close()

    return

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

def list_regions(loaded_config,terse=False):
    '''List region codes and descriptions for use in config, pass the config dict'''

    # get regions
    manager = check_and_connect(loaded_config)
    try:
        regions = manager.get_all_regions()
    except digitalocean.DataReadError:
        exit_with_error(2,"list: DataReadError, check settings and try again")
        
    #Put them in a dict{} and sort
    region_dict = {}
    for item in regions:
        region_dict[item.slug] = item.name
    sorted_regions = sorted(region_dict)

    #print
    tab_space = 13
    banner = colors.bold + "ID\tDESCRIPTION".expandtabs(tab_space) + colors.reset
    if terse == False:
        print(banner)
        for item in sorted_regions:
            out_line = item + "\t" + region_dict[item]
            out_line = out_line.expandtabs(tab_space)
            print(out_line)
    elif terse == True:
        for item in sorted_regions:
            out_line = item + "," + region_dict[item]
            print(out_line)
    else:
        exit_with_error(10,"list: regions: terse neither true nor false, should not be, debug!")

def print_config(loaded_config,terse=False):
    '''Fancy printing of all config items. if terse is True, then print a comma-field seperated ver for grep and cut'''
    restricted_list = ['api-key', 'bucket-key-secret']
    tab_spaces = 25
    header_line= colors.bold + "ITEM\tVALUE".expandtabs(tab_spaces) + colors.reset
    if terse == False:
        print(header_line)
        out_line=""
        for item in loaded_config:
            if item in restricted_list:
                value = "********"
            else:
                value = loaded_config[item]
                value = str(value)
            out_line = item + "\t" + value
            out_line = out_line.expandtabs(tab_spaces)
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

def gen_bucket_client(loaded_config):
    url = "https://%s.digitaloceanspaces.com/" % (loaded_config["region"])
    #url = "diskimages.nyc3.digitaloceanspaces.com"
    
    session = boto3.session.Session()
    client  = session.client(
        's3',
        region_name           = loaded_config["region"],
        endpoint_url          = url,
        aws_access_key_id     = loaded_config["bucket-key-name"],
        aws_secret_access_key = loaded_config["bucket-key-secret"]
    )
    
    return client

def list_bucket_files(loaded_config,terse=False):
    '''list files in bucket'''
    # Formatting option
    tab_size=30
    
    #Generate Bucket Object    
    bucket_obj = gen_bucket_client(loaded_config)
    
    # Query Server
    try:
        response = bucket_obj.list_objects_v2(Bucket=loaded_config['bucket'])
    except botocore.exceptions.NoCredentialsError:
        error_message = 'Credentials not provided or invalid.'
        exit_with_error(1,error_message)
    except botocore.exceptions.EndpointConnectionError:
        error_message = f'Unable to connect to endpoint: Check your region or endpoint.'
        exit_with_error(1,error_message)
    except botocore.exceptions.ParamValidationError as e:
        error_message = f'An Error Occured: ' + e.args[0]
        exit_with_error(1,error_message)
    except Exception as e:
        error_message =  f'An Error Occurred: {e}'
        exit_with_error(1,error_message)
        
    # Now print results
    header_line = colors.bold + "Filename\tLastModified".expandtabs(tab_size) + colors.reset
    if terse != True:
        print(header_line)
    out_list = []
    if 'Contents' in response:
        for obj in response['Contents']:
            if terse != True:
                item_line = "%s\t%s".expandtabs(tab_size) % (obj['Key'],obj['LastModified'].ctime())
                print(item_line)
            else:
                item_line = "%s:%s" % (obj['Key'],obj['LastModified'].ctime())
                out_list.append(item_line)
    else:
        if terse != True:
            item_line = "<No Items>"
    #Now do terse printing 
    if terse == True:
        output = ",".join(out_lines)
        print(output)
        
def clean_bucket(loaded_config):
    '''Delete All Files In Bucket'''
    
    # Formatting option
    tab_size=30
    
    #Generate Bucket Object    
    bucket_obj = gen_bucket_client(loaded_confg)
    
    # Query Server
    try:
        response = bucket_obj.list_objects_v2(Bucket=loaded_config['bucket'])
    except botocore.exceptions.NoCredentialsError:
        error_message = 'Credentials not provided or invalid.'
        exit_with_error(1,error_message)
    except botocore.exceptions.EndpointConnectionError:
        error_message = f'Unable to connect to endpoint: Check your region or endpoint.'
        exit_with_error(1,error_message)
    except botocore.exceptions.ParamValidationError as e:
        error_message = f'An Error Occured: ' + e.args[0]
        exit_with_error(1,error_message)
    except Exception as e:
        error_message =  f'An Error Occurred: {e}'
        exit_with_error(1,error_message)
        
    

def main():
    parser = argparse.ArgumentParser(description=full_help_banner,epilog="\n\n",add_help=False,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", nargs="?"    ,help="See above for description of commands")
    parser.add_argument("arguments", nargs="*"  ,help="Arguments for command, see above")
    parser.add_argument("-?","--help"           ,help="Show This Help Message", action="help")
    parser.add_argument("-T","--terse"          ,help="terse output, for scripting",action="store_true")
    
    config_overrides = parser.add_argument_group("Config Overrides","Configuration Overrides, lower case")
    config_overrides.add_argument("-r","--region"  ,help="Region code. Specify what datacenter this goes in",type=str)

    args = parser.parse_args()
    
    # get config from file
    config_dir = os.getenv("HOME") + "/.config/harbor-wave/"
    loaded_config = check_and_load_config(config_dir)

    # Now apply command line switch options
    if args.region != None:
        loaded_config['region'] = args.region
    
    # Lets roll. Commands do their own checks
    if args.command == None:
        exit_with_error(2,"No command given, see --help")
    elif args.command == "help":
        if len(args.arguments) >= 1:
            subject = args.arguments[0]
        else:
            parser.print_help()
            sys.exit(4)
        if subject == "commands":
            print(command_help)
            sys.exit(4)
        elif subject == "config":
            print(config_help)
            sys.exit(4)
        else:
            exit_with_error(2,"help: no such topic. see --help or help for topics")
    elif args.command == "touch":
        sys.exit(0)
    elif args.command == "set":
        if len(args.arguments) < 2:
            exit_with_error(2,"set: Command takes two arguments, item and value. See --help")
        item  = args.arguments[0]
        value = args.arguments[1]
        set_config(config_dir,loaded_config,item,value)
    elif args.command == "get":
        if len(args.arguments) < 1:
            exit_with_error(2,"get: Command takes one argument: item. See --help")
        item = args.arguments[0]
        get_config(loaded_config,item)
    elif args.command == "print-config":
        print_config(loaded_config,args.terse)
    elif args.command == "list":
        if len(args.arguments) < 1:
            exit_with_error(2,"list: list what? needs an argument, see --help")
        option = args.arguments[0]
        if option == "help":
            output_line = "list: following are valid list subcommands: templates, files, regions. See  --help for more info"
            print(output_line)
        elif option == "templates":
            list_templates(loaded_config,args.terse)
        elif option == "files":
            list_bucket_files(loaded_config,args.terse)
        elif option == "regions":
            list_regions(loaded_config,args.terse)

if __name__ == "__main__":
    main()

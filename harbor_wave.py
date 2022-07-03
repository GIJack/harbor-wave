#!/usr/bin/env python
# exit codes 0-success, 1-operation error, 2-condition error
prog_desc='''Use the Digital Ocean API to spawn temporary utility machines based
on custom templates in DO's cloud. The idea being able to rapidly create and
destroy custom machines via the DO API call. Designed to go hand and hand with
disk-image-scripts:
https://github.com/GIJack/disk-image-scripts

You need a Digital Ocean Account, set up ssh-keys, an account API, and S3 bucket
for the custom images, and a project to organize them.

config is stored in ~/.config/harbor-wave/harbor-wave.cfg and is JSON

API key is stored in ~/.config/harbor-wave/api_key

Switches override config

			COMMANDS:

  help - this text

  list [what] - list various things. Subcommands/arguments:
      machines   - Show Virtual Machines in use associated with harbor-wave.
      Based on VM tag in settings.

      templates  - Show available custom images.
  
      regions    - List valid region codes for use in config
  
      vm-sizes   - List of valid vm size codes for use in config
      
      money-left - How much $$$ you have left on your DO account. So far,
      you need to log in to the Web interface to add more $$$. Haven't worked
      out replenish by API yet...
      
    example: harbor-wave list vm-sizes

  spawn <N> - Create a new N new VMs. default is 1

  destroy [VM Names] - Destroy Name VMs. List of names. the ALL tag will destroy
  all VMs associated with harborwave as determined by having the right VM tag.

  set [property] - set a config item. See bellow for list of config items

  get [property] - print value for item, see bellow for list of config items
  
  print-config   - print all config items in pretty table.

  touch         - Stop after proccessing initial config. useful for generating
  blank config file. Will not touch the api-key

        CONFIG ITEMS:

   api-key - Digital Ocean API key, used for accessing the account. NOTE this
   is the only option that does NOT go in the .cfg file, but rather the seperate
   api-key file

   domain      - DNS domain to use if use-dns is set True
   
   project - digital ocean project name. Optional, but must exist if set.
   Droplets created with spawn will be added to this project.

   region  - digital ocean region code slug to spawn droplets. You can get a
   list of valid entries with the list-reigons command. Default: nyc1
   
   ssh-key-n   - Interger, count from 0. Select which SSH key is being used to
   access the VM. Should display in order on the DO website. This is the ssh
   login key for root unless you have modified it with cloud-init. If you only
   have one key, this is 0
   
   tag         - tag to use for the droplets that harbor-wave will use to
   recognize its own. Default: harborwave
      
   vm-base-name - what to call droplets that will be spawned, if more than one
   is spawned, this will be the base, and new names will be incremented. At
   current this will be numeric. Might change in the future(perhaps name-sets)
   
   vm-size     - Size code for how big the droplet should be.  See list-vm-sizes
   for list of size codes. Default: s-1vcpu-1gb.
   
   vm-template - ID of the custom template image for spawning droplets. You can
   get a list of valid values with list-templates
   
   use-dns     - Use fully qualified domain names for droplet host names, and
   set DNS in network settings. True or False. This domain MUST EXIST on your
   Digital Ocean account.

'''

import os,sys
import argparse
import json
import digitalocean

default_config = {
    "domain"       : "",
    "region"       : "nyc1",
    "ssh-key-n"    : 0,
    "tag"          : "harborwave",
    "vm-base-name" : "",
    "vm-size"      : "s-1vcpu-1gb",
    "vm-template"  : "",
    "use-dns"      : False
}

class colors:
    '''pretty terminal colors'''
    reset='\033[0m'
    bold='\033[01m'
    red='\033[31m'
    cyan='\033[36m'
    yellow='\033[93m'

def message(message):
    print("harbor-wave: " + message)

def exit_with_error(exit,message):
    print("harbor-wave" + colors.red + colors.bold + " ¡ERROR!: " + colors.reset + message, file=sys.stderr)
    sys.exit(exit)
    
def warn(message):
    print("harbor-wave:" + colors.yellow + colors.bold + " ¡WARN!: " + colors.reset + message, file=sys.stderr)
    return

def check_api_key(key):
    '''checks if API key is valid format. returns True/False. Takes one parameter, the key'''
    # a DO access key is 64 characters long, hexidecimal
    key_len = 64
    base    = 16
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

def list_machines(loaded_config,terse=False):
    '''give a list of droplets in project, nomially ones created with this prog.
    if terse is True, then print in CSV format for grep and cut'''
    
    # pre-flight tests
    if "tag" not in loaded_config.keys():
        exit_with_error(2,"Droplet tag not set in config. see --help for set and tag item")
    if "api-key" not in loaded_config.keys():
        exit_with_error(2,"api-key not set. see --help on set.")
    droplet_tag = loaded_config['tag']
    api_key     = loaded_config['api-key']
    if check_api_key(api_key) != True:
        exit_with_error(2,"Invalid API Key")
    
    #lets go
    manager = digitalocean.Manager(token=api_key)
    try:
        droplet_list = manager.get_all_droplets(tag_name=droplet_tag)
    except digitalocean.DataReadError:
        exit_with_error(1,"list: invalid api-key, authentication failed, check account")
    
    tab_spacing = 12
    header  = colors.bold + "Name\t\tRegion\tSize\t\tImage\t\tDatestamp".expandtabs(tab_spacing) + colors.reset
    out_line = ""
    if terse == False:
        print(header)
        for droplet in droplet_list:
            out_line = droplet.name + "\t" + droplet.region['slug'] + "\t" + droplet.size['slug'] + "\t\t" + droplet.image['name'] + "\t\t" + droplet.created_at
            out_line = out_line.expandtabs(tab_spacing)
            print(out_line)
    elif terse == True:
        for droplet in droplet_list:
            out_line = droplet.name + "," + droplet.region['slug'] + "," + droplet.size['slug'] + "," + droplet.image['name'] + ',' + droplet.created_at
            print(out_line)
    else:
        exit_with_error(9,"list: machines: terse is neither True nor False, should never get here, debug!")

def list_templates(loaded_config,terse=False):
    '''List available templates to make machines from. Takes one parameter, the config dict '''
    # pre-flight tests
    if "api-key" not in loaded_config.keys():
        exit_with_error(2,"api-key not set. see --help on set.")
    api_key = loaded_config['api-key']
    if check_api_key(api_key) != True:
        exit_with_error(2,"Invalid API Key")
    
    # get images
    manager = digitalocean.Manager(token=api_key)
    try:
        all_images = manager.get_my_images()
    except digitalocean.DataReadError:
        exit_with_error(1,"list: invalid api-key, authentication failed, check account")
    
    # Seperate out user uploaded images
    use_images = []
    for image in all_images:
        if image.type == "custom":
            use_images.append(image)
            
    #now print
    tab_size = 15
    banner = colors.bold + "ID\tREGIONS\t\tDESCRIPTION".expandtabs(tab_size) + colors.reset
    print(banner)
    for image in use_images:
        out_line = str(image.id) + "\t" + ",".join(image.regions) + "\t\t" + image.name
        out_line = out_line.expandtabs(tab_size)
        print(out_line)

def list_regions(loaded_config,terse=False):
    '''List region codes and descriptions for use in config, pass the config dict'''
    # pre-flight tests
    if "api-key" not in loaded_config.keys():
        exit_with_error(2,"api-key not set. see --help on set.")
    api_key = loaded_config['api-key']
    if check_api_key(api_key) != True:
        exit_with_error(2,"Invalid API Key")
     
    # get regions
    manager = digitalocean.Manager(token=api_key)
    try:
        regions = manager.get_all_regions()
    except digitalocean.DataReadError:
        exit_with_error(1,"list: invalid api-key, authentication failed, check account")

    #print
    tab_space = 13
    banner = colors.bold + "ID\t\tDESCRIPTION".expandtabs(tab_space) + colors.reset
    print(banner)
    for item in regions:
        out_line = item.slug + "\t\t" + item.name
        out_line = out_line.expandtabs(tab_space)
        print(out_line)

def list_sizes(loaded_config,terse=False):
    '''List Available VM sizes, needs config dict'''
    # pre-flight tests
    if "api-key" not in loaded_config.keys():
        exit_with_error(2,"api-key not set. see --help on set.")
    api_key = loaded_config['api-key']
    if check_api_key(api_key) != True:
        exit_with_error(2,"Invalid API Key")
        
    # get VM sizes
    manager = digitalocean.Manager(token=api_key)
    
    try:
        avail_sizes = manager.get_all_sizes()
    except digitalocean.DataReadError:
        exit_with_error(1,"list: invalid api-key, authentication failed, check account")
    
    # print
    tab_space = 19
    header = colors.bold + "SLUG\t\tCPU\tRAM\tDISK\t$$-HOUR".expandtabs(tab_space) + colors.reset
    if terse == False:
        print(header)
        for item in avail_sizes:
            if item.available != True:
                continue
            item_memory = item.memory / 1024
            out_line = item.slug + "\t\t" + str(item.vcpus) + " CPU(s)\t" + str(item_memory) + "GB RAM\t" + str(item.disk) + "GB HD\t" + str(item.price_hourly)
            out_line = out_line.expandtabs(tab_space)
            print(out_line)
    elif terse == True:
        for item in avail_sizes:
            item_memory = item.memory / 1024
            out_line = item.slug + "," + str(item.vcpus) + "," + str(item_memory) + "," + str(item.disk) + "," + str(item.price_hourly)
            print(out_line)
    else:
        exit_with_error(9,"list: sizes - terse neither true nor false, should not be here, debug!")

def list_account_balance(loaded_config,terse=False):
    '''Shows how much money you have left in the account'''
    '''List Available VM sizes, needs config dict'''
    # pre-flight tests
    if "api-key" not in loaded_config.keys():
        exit_with_error(2,"api-key not set. see --help on set.")
    api_key = loaded_config['api-key']
    if check_api_key(api_key) != True:
        exit_with_error(2,"Invalid API Key")
        
    # get VM sizes
    manager = digitalocean.Manager(token=api_key)
    
    try:
        funds = manager.get_balance()
    except digitalocean.DataReadError:
        exit_with_error(1,"list: invalid api-key, authentication failed, check account")    
   
    #print
    if terse == False:
        output = "Remaining Funds: $" + str(abs(float(funds.account_balance)))
    elif terse == True:
        output = "$" + str(abs(float(funds.account_balance)))
    message(output)

def set_config(config_dir,loaded_config,item,value):
    '''update config, vars loaded_config is a dict of values to write, the rest should be self explanitory'''
    api_file_name    = "api-key"
    config_file_name = "harbor-wave.cfg"
    api_file         = config_dir + "/" + api_file_name
    config_file      = config_dir + "/" + config_file_name
    set_item_str     = ("api-key","domain", "vm-base-name","project","vm-size","region","vm-template", "tag")
    set_item_int     = ("ssh-key-n")
    set_item_bool    = ("use-dns")
    all_set_items    = set_item_str + set_item_int + set_item_bool
    
    ## check if valid
    # Null value check
    if item == None or item == "":
        exit_with_error(2, "set: item name can't be blank")
    elif value == None or value == "":
        exit_with_error(2, "set: item value can't be blank")
    elif item not in all_set_items:
        exit_with_error(2, "set: " + item + " is not a valid config item" )
    # Check and set type
    if item in set_item_str:
        try:
            value = str(value)
        except:
            exit_with_error(2,"set: invalid value for " + item)
    elif item in set_item_int:
        try:
            value = int(value)
        except:
            exit_with_error(2,"set: invalid value for " + item)
    elif item in set_item_bool:
        try:
            value = bool(value)
        except:
            exit_with_error(2,"set: invalid value for " + item)

    # if item is an api key, check before set:
    if item == "api-key":
        if check_api_key(value) != True:
            exit_with_error(2,"set: Invalid API Key for api-key")
    else:
        # now update the config array, but not for the api-key
        loaded_config[item] = value
    
    # Make sure we keep the API key out of the main config
    del(loaded_config['api-key'])
    
    # write the config. Write API key to 
    try:
        if item == "api-key":
            file_obj = open(api_file,"w")
            file_obj.write(value)
            file_obj.close()
            os.chmod(api_file, 0o600)
        else:
            write_config(config_file,loaded_config)
    except:
        exit_with_error(2,"set: Could not write to config file")

def print_config(loaded_config,terse=False):
    '''Fancy printing of all config items. if terse is True, then print a comma-field seperated ver for grep and cut'''
    restricted_list = ['api-key']
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
    
def get_config(loaded_config,item):
    '''prints working config item, takes two options, dict with config items, and item you need'''
    if item == "api-key":
        exit_with_error(2,"get: Won't print api key... ")
    if item not in loaded_config.keys():
        exit_with_error(2,"get: No such config item: " + item)
    
    output = loaded_config[item]
    output = str(output)
    print(output)

def write_config(file_name,config_obj):
    '''write config to JSON file'''

    contents  = json.dumps(config_obj,indent=4)
    contents += "\n"

    file_obj = open(file_name, "w")
    file_obj.write(contents)
    file_obj.close()

def check_and_load_config(config_dir):
    '''Runs on startup: checks and loads config file. missing entries are added, missing config files are made. takes one parameter: filename for config dir'''
    
    # Mabey we should put these somewhere else? idk, top level dict?
    config_file_name = "harbor-wave.cfg"
    api_file_name    = "api-key"
    
    # These will be loaded with actual values later. Value None means load
    # load failed
    loaded_config    = None
    loaded_api_key   = None
    
    # check if config directory exists. If not make it:
    if os.path.isdir(config_dir) == False and os.path.exists(config_dir) == True:
        raise "BadConfDir"
    elif os.path.exists(config_dir) == False:
        os.makedirs(config_dir,mode=0o750,exist_ok=True)
    
    # Check config file
    config_file = config_dir + "/" + config_file_name
    
    # check if config file exists, if not make it then return defaults:
    # If the config file exists, load it
    if os.path.isfile(config_file)   == False and os.path.exists(config_file) == True:
        raise "BadConfFile"
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
        raise "LoadConfigFailed"
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
        raise "BadAPIFile"
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
    parser = argparse.ArgumentParser(description=prog_desc,epilog="\n\n",add_help=False,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", nargs="?"        ,help="See above for description of commands")
    parser.add_argument("arguments", nargs="*"       ,help="Arguments for command, see above")
    parser.add_argument("-?","--help"                ,help="Show This Help Message", action="help")

    parser.add_argument("-a","--api-key"             ,help="Digitial Ocean API key to use",type=str)
    parser.add_argument("-d","--domain"              ,help="Domain to use if --use-dns is used.",type=str)
    parser.add_argument("-g","--tag"                 ,help="DO tag to use on VMs so harbor-wave can identify its VMs. default: harborwave",type=str)
    parser.add_argument("-k","--ssh-key-n"           ,help="Interger: index of SSH-key to use for root(or other if so configed) access. Default is 0",type=int)
    parser.add_argument("-n","--vm-base-name"        ,help="Base Name For New VMs",type=str)
    parser.add_argument("-s","--vm-size"             ,help="Size code for new VMs",type=str)
    parser.add_argument("-t","--vm-template"         ,help="Image Template for spawning new VMs",type=str)
    parser.add_argument("-u","--use-dns"             ,help="Use FQDNs for naming VMs and add DNS entries in Networking",action="store_true")

    args = parser.parse_args()

    # get config from file
    config_dir = os.getenv("HOME") + "/.config/harbor-wave/"
    try:
        loaded_config = check_and_load_config(config_dir)
    except:
        warn("could not load config, all options must be specified on command line or harbor-wave will fail")
    
    # Now apply command line switch options
    
    if args.api_key != None:
        loaded_config['api-key']       = args.api_key
    if args.domain != None:
        loaded_config['domain']        = args.domain
    if args.tag != None:
        loaded_config['tag']           = args.tag
    if args.ssh_key_n != None:
        loaded_config['ssh-key-n']     = args.ssh_key_n
    if args.vm_base_name != None:
        loaded_config ['vm-base-name'] = args.vm_base_name
    if args.vm_size != None:
        loaded_config['vm-size']       = args.vm_size
    if args.vm_template != None:
        loaded_config['vm-template']   = args.vm_template
    if args.use_dns == True:
        loaded_config['use-dns']       = True

    # Lets roll. Commands do their own checks
    if args.command == None:
        exit_with_error(2,"No command given, see --help")
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
        print_config(loaded_config)
    elif args.command == "list":
        terse = False
        if len(args.arguments) < 1:
            exit_with_error(2,"list: list what? needs an argument, see --help")
        option = args.arguments[0]
        if option == "help":
            message("list:  valid options are machines, templates, regions, and vm-sizes. see --help for more info")
            sys.exit(4)
        elif option == "machines":
            list_machines(loaded_config)
        elif option == "templates":
            list_templates(loaded_config)
        elif option == "regions":
            list_regions(loaded_config)
        elif option == "vm-sizes":
            list_sizes(loaded_config)
        elif option == "money-left":
            list_account_balance(loaded_config)
        else:
            exit_with_error(2,"list: Invalid option, see -help for options")
    else:
        exit_with_error(2,"No such command. See --help")

if __name__ == "__main__":
    main()

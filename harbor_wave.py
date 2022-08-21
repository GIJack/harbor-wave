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
'''
command_help='''
			COMMANDS:

  help <topic> - brief overview. if topic is specified then only the relevant
  entries for that topic are printed.
  
  help topics: config, commands

  list [what] - list things. Use the --terse option for CSV output.
  Subcommands/arguments:
      machines   - Show Virtual Machines in use associated with harbor-wave.
      Based on VM tag in settings.
      
      projects   - List projects on current account

      templates  - Show available custom images.
  
      regions    - List valid region codes for use in config
      
      ssh-keys   - List SSH-keys on the account. use INDEX for ssh-key-n config
      item with set
  
      sizes      - List of valid vm size codes for use in config
      
      money-left - How much $$$ you have left on your DO account. also shows
      "Burn Rate", the rate of which harbor-wave machines cost money. burn-rate
      is in dollars per hour, and only shows money used by harbor-wave machines,
      not the entirity for the account.
      
    example: harbor-wave list sizes

  spawn <N> - Create a new N new VMs. default is 1

  destroy <"ALL"> - Destroy VMs. If ALL is appended, then all harbor-wave VMs
  will be destroyed, based on tag.
  
  set [item] [value] - set a config item. See bellow for list of config items.
  Setting a value of "" will reset this item to its default value

  get [item]     - print value for item, see bellow for list of config items
  
  print-config   - print all config items in pretty table.

  touch          - Stop after proccessing initial config. useful for generating
  blank config file. Will not touch the api-key
'''
config_help='''
        CONFIG ITEMS:

   api-key - Digital Ocean API key, used for accessing the account. NOTE this
   is the only option that does NOT go in the .cfg file, but rather the seperate
   api-key file

   domain      - DNS domain to use if use-dns is set True
   
   payload     - Input data from your local machine and made availble over the
   Digital Ocean API, for use with cloud-init or other. This is a string
   unless it starts with FILE:. In this case, file contents are uploaded
   
   project     - name of project in account where new machines spawn. If blank
   default is used

   region      - digital ocean region code slug to spawn droplets. You can get a
   list of valid entries with the list-reigons command. Default: nyc1
   
   ssh-key-n   - Interger, index of SSH keys to include when creating virtual
   machines. see list ssh-keys
   
   tag         - tag to use for the droplets that harbor-wave will use to
   recognize its own. Default: harborwave
      
   base-name - what to call droplets that will be spawned, if more than one
   is spawned, this will be the base, and new names will be incremented. At
   current this will be numeric. Might change in the future(perhaps name-sets)
   
   size     - Size code new droplets.  See list sizes for list of size codes and
   their descriptions. Default: s-1vcpu-1gb.
   
   template - ID of the custom template image for spawning droplets. You can
   get a list of valid values with list templates
   
   use-dns     - Use fully qualified domain names for droplet host names, and
   set DNS in network settings. True or False. This domain MUST EXIST on your
   Digital Ocean account.

'''
full_help_banner=prog_desc+command_help+config_help

import os,sys
import argparse
import json
import digitalocean
from datetime import datetime, tzinfo, timedelta
from zoneinfo import ZoneInfo

default_config = {
    "domain"       : "",
    "payload"      : "",
    "project"      : "",
    "region"       : "nyc1",
    "ssh-key-n"    : 0,
    "tag"          : "harborwave",
    "base-name" : "",
    "size"      : "s-1vcpu-1gb",
    "template"  : "",
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

def submsg(message):
    print("[+]\t" + message)
    
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
    
def check_dns(loaded_config):
    '''Check if domain is usable for DNS, ignores use-dns, returns True of False'''
    
    manager = check_and_connect(loaded_config)
    
    try:
        all_domains = manager.get_all_domains()
    except digitalocean.DataReadError:
        exit_with_error(1,"list: DataReadError, check settings and try again")
        
    # make a list with just the names
    domain_list = []
    for item in all_domains:
        domain_list.append(item.name)
    
    # Check if config lines up with what is on DO
    if loaded_config['domain'] in domain_list:
        return True
    else:
        return False

def convert_datestamp(in_date):
    '''takes a string from droplet.createdate, and returns a python datetime object'''
    # this is the format that createdate returns
    # see: https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
    do_timeformat = "%Y-%m-%dT%XZ"
    do_timezone   = ZoneInfo("Zulu")
    local_tz      = datetime.now().astimezone().tzinfo
    
    # get a timedate object out of Digital Ocean's formating, including re-add timezone
    date_obj  = datetime.strptime(in_date,do_timeformat)
    date_obj  = date_obj.replace(tzinfo=do_timezone)
    # convert to local date
    date_obj  = date_obj.astimezone(local_tz)
    # strip timezone because otherwise maths don't work. ?!?!?
    date_obj  = date_obj.replace(tzinfo=None)
    return date_obj

def check_and_connect(loaded_config):
    '''give the loaded config, check the API key, and return a DO manager session'''
    
    # check to make sure we have the right config options
    needed_keys = ("api-key","domain","region","ssh-key-n","base-name","size","template","use-dns")
    for key in needed_keys:
        if key not in loaded_config.keys():
            exit_with_error(2,key + " not set. see help config")
    
    api_key = loaded_config['api-key']
    if check_api_key(api_key) != True:
        exit_with_error(2,"Invalid API Key")
        
    # get open a session
    manager = digitalocean.Manager(token=api_key)
    
    return manager

def list_machines(loaded_config,terse=False):
    '''give a list of droplets in project, nomially ones created with this prog.
    if terse is True, then print in CSV format for grep and cut'''
    
    manager = check_and_connect(loaded_config)
    droplet_tag = loaded_config['tag']
    try:
        droplet_list = manager.get_all_droplets(tag_name=droplet_tag)
    except digitalocean.DataReadError:
        exit_with_error(2,"list: DataReadError, check settings and try again")
    
    tab_spacing = 20
    header  = colors.bold + "NAME\tIP ADDRESS\tREGION\tSIZE\tTEMPLATE\t\tTIME RUNNING(H:M:S.µS)".expandtabs(tab_spacing) + colors.reset
    out_line = ""
    if terse == False:
        print(header)
        for droplet in droplet_list:
            # get how long machine has been running
            droplet_start_obj = convert_datestamp(droplet.created_at)
            time_running = datetime.now() - droplet_start_obj
            time_running = str(time_running)
            out_line = droplet.name + "\t" + str(droplet.ip_address) + "\t" + droplet.region['slug'] + "\t" + droplet.size['slug'] + "\t" + droplet.image['name'] + "\t" + time_running
            out_line = out_line.expandtabs(tab_spacing)
            print(out_line)
    elif terse == True:
        for droplet in droplet_list:
            droplet_start_obj = convert_datestamp(droplet.created_at)
            time_running = datetime.now() - droplet_start_obj
            time_running = str(time_running)
            out_line = droplet.name + "," + droplet.ip_address + "," + droplet.region['slug'] + "," + droplet.size['slug'] + "," + droplet.image['name'] + ',' + time_running
            print(out_line)
    else:
        exit_with_error(10,"list: machines: terse is neither True nor False, should never get here, debug!")

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

    #print
    tab_space = 13
    banner = colors.bold + "ID\tDESCRIPTION".expandtabs(tab_space) + colors.reset
    if terse == False:
        print(banner)
        for item in regions:
            out_line = item.slug + "\t" + item.name
            out_line = out_line.expandtabs(tab_space)
            print(out_line)
    elif terse == True:
        for item in regions:
            out_line = item.slug + "," + item.name
            print(out_line)
    else:
        exit_with_error(10,"list: regions: terse neither true nor false, should not be, debug!")

def list_sizes(loaded_config,terse=False):
    '''List Available VM sizes, needs config dict'''
    
    # get VM sizes
    manager = check_and_connect(loaded_config)
    try:
        avail_sizes = manager.get_all_sizes()
    except digitalocean.DataReadError:
        exit_with_error(2,"list: DataReadError, check settings and try again")
    
    # print
    tab_space = 19
    header = colors.bold + "NAME\t\tCPU\tRAM\tDISK\t$$-HOUR".expandtabs(tab_space) + colors.reset
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
        exit_with_error(10,"list: sizes - terse neither true nor false, should not be here, debug!")

def list_projects(loaded_config,terse=False):
    '''List all Projects in your Digital Ocean Account'''
    
    manager = check_and_connect(loaded_config)
    
    try:
        projects = manager.get_all_projects()
    except digitalocean.DataReadError:
        exit_with_error(2,"list: DataReadError, check settings and try again")
    
    tab_spaces = 25
    header = colors.bold + "NAME\tTIER\tDESCRIPTION".expandtabs(tab_spaces) + colors.reset
    if terse == False:
        print(header)
        for item in projects:
            out_line = item.name + "\t" + item.environment + "\t" + item.description
            out_line = out_line.expandtabs(tab_spaces)
            print(out_line)
    elif terse == True:
        for item in projects:
            out_line = item.name + "," + item.environment + "," + item.description
            print(out_line)
    else:
        exit_with_error(10,"list: projects - terse neither true nor false, should not be here, debug")

def list_account_balance(loaded_config,terse=False):
    '''Shows how much money you have left in the account'''
        
    # get funds
    manager = check_and_connect(loaded_config)
    try:
        funds = manager.get_balance()
    except digitalocean.DataReadError:
        exit_with_error(2,"list: DataReadError, check settings and try again")    

    droplet_tag = loaded_config['tag']
    try:
        droplet_list = manager.get_all_droplets(tag_name=droplet_tag)
    except digitalocean.DataReadError:
        exit_with_error(2,"list: DataReadError, check settings and try again")
   
    # some back-of-the-napkin math
    used_so_far = float(funds.month_to_date_usage)
    balance     = abs(float(funds.account_balance))
    remaining   = round(balance - used_so_far,2)
    
    # get total burn rate from harbor-wave VMs
    burn_rate = float(0)

    for item in droplet_list:
        burn_rate += item.size['price_hourly']
    
    #print
    banner = "Finances"
    tab_space = 18
    if terse == False:
        message(banner)
        output = colors.bold + "Remaining Funds: \t" + colors.reset + "$" + str(remaining)
        output = output.expandtabs(tab_space)
        print(output)
        output = colors.bold + "Burn Rate($/Hour): \t" + colors.reset + "$" + str(burn_rate)
        output = output.expandtabs(tab_space)
        print(output)
        
    elif terse == True:
        output = str(remaining) + "," + str(burn_rate)
        print(output)
    else:
        exit_with_error(10,"list: money-left: terse neither True nor False, should not be here, debug!")

def list_ssh_keys(loaded_config,terse=False):
    '''List SSH keys registered to your digital ocean account'''
        
    # get VM sizes
    manager = check_and_connect(loaded_config)
    try:
        ssh_keys = manager.get_all_sshkeys()
    except digitalocean.DataReadError:
        exit_with_error(2,"list: DataReadError, check settings and try again")  
    
    # Now print
    tab_size =  18
    header = colors.bold + "INDEX\tNAME\tFINGERPRINT".expandtabs(tab_size) + colors.reset
    num_keys = len(ssh_keys)
    if terse == False:
        print(header)
        for index in range(num_keys):
            key = ssh_keys[index]
            out_line = str(index) + '\t' + key.name + "\t" + key.fingerprint
            out_line = out_line.expandtabs(tab_size)
            print(out_line)
    elif terse == True:
        for index in range(num_keys):
            key = ssh_keys[index]
            out_line = str(index) + ',' + key.name + ',' + key.fingerprint
            print(out_line)
    else:
        exit_with_error(10,"list ssh-keys: terse is neither true nor false, this should not be, debug!")

def create_machine(loaded_config,machine_name,ssh_key,user_meta=""):
    '''Creates a single virtual-machine, uses machine_name variable for name,
    ignores base-name in config. This is a base class that does no checking
    or iteration. must also pass the SSH key, to only have to load it once
    Also does not mess with DNS. returns True or False, depending on if success
    or not
    '''
    
    manager  = check_and_connect(loaded_config)
    new_vm  = digitalocean.Droplet(token=loaded_config['api-key'],
                                    name=machine_name,
                                    region=loaded_config['region'],
                                    image=loaded_config['template'],
                                    size_slug=loaded_config['size'],
                                    tags=[ loaded_config['tag'] ],
                                    ssh_keys= [ ssh_key ],
                                    user_data=user_meta,
                                    backups=False )
    new_vm.create()
    
    if loaded_config['project'] != None and loaded_config['project'] != "":
        use_project = None
        projects = manager.get_all_projects()
        for item in projects:
            if item.name == loaded_config['project']:
                use_project = item
        if use_project == None:
            warn("spawn: could not add " + machine_name + " to non-existant project: " + loaded_config['project'] + ", skipping")
            return
        droplet_add_string = "do:droplet:" + str(new_vm.id)
        use_project.assign_resource([droplet_add_string])

def create_dns(loaded_config,vm_name,ip_address):
    '''Update DNS for new virtual machine, assumes domain is valid, check first'''

    api_key     = loaded_config['api-key']
    domain_name = loaded_config['domain']
    domain_obj  = digitalocean.Domain(token=api_key, name=domain)
    new_record  = domain_obj.create_new_domain_record(type="A", name=vm_name, data=ip_address)
    return new_record

def spawn_machines(loaded_config,N=1):
    '''the spawn command. takes the config dict and N, int number of machines'''
    
    manager = check_and_connect(loaded_config)
    
    #Some more checks
    if len(loaded_config["base-name"]) < 1:
        exit_with_error(2,"spawn: base-name needs to be at least one char for this to work!")
    try:
        N = int(N)
    except:
        exit_with_error(2,"spawn: N needs to be an interger")
    # Get ssh keys
    try:
        all_ssh_keys = manager.get_all_sshkeys()
    except digitalocean.DataReadError:
        exit_with_error(1,"spawn: DataReadError, check settings and try again")
    key_n   = loaded_config['ssh-key-n']
    use_key = all_ssh_keys[key_n]
    
    if loaded_config['use-dns'] == True:
        warn("use-dns is not implemented yet, will be ignored") #TODO, finish domains
        if check_dns(loaded_config['domain']) == False:
            exit_with_error(9,"spawn: use-dns is True, but domain name is not in Digital Ocean config, stop!")

    # Load payload from file, if applicable
    meta_payload = None
    if loaded_config['payload'].startswith("FILE:") == True:
        # get filename as everythinng after first ':'
        meta_filename = loaded_config['payload'].split(":")[1:]
        meta_filename = " ".join(meta_filename)
        try:
            file_obj = open(meta_filename,"r")
            file_data = file_obj.read()
            file_obj.close()
            meta_payload = file_data
        except:
            exit_with_error(2,"spawn: could not read payload from " + meta_filename + ". Please ensure this file exists and read permissions are set")
    else:
        meta_payload = loaded_config['payload']
    
    banner = "Spawning machine series: " + loaded_config['base-name'] + ", " + str(N) + " machines(s)"
    message(banner)
    # spawn N machines
    fails = 0
    for i in range(N):
        user_meta = { "sequence" : int(i), "base-name":loaded_config['base-name'], "payload":meta_payload }
        user_meta = json.dumps(user_meta,indent=2)
        vm_name   = loaded_config['base-name'] + str(i)
        msg_line  = vm_name + " created"
        try:
            create_machine(loaded_config,vm_name,use_key,user_meta)
            submsg(msg_line)
        except:
            warn("spawn: could not create machine " + vm_name)
            fails += 1
    
    if fails >= 1:
        message("Done, but with " + str(fails) + " failures" )
        sys.exit(1)
    else:
        message("Done")
    

def destroy_machines(loaded_config,args=[]):
    '''delete virtual machine(s). Deletes machines specified by a list
    of matching machine names. If ALL is specified instead of a list
    all machines with the configured tag will be deleted'''

    manager   = check_and_connect(loaded_config)
    vm_tag    = loaded_config['tag']
    base_name = loaded_config['base-name']
    
    # get a list of machines to delete
    try:
        running_machine_list = manager.get_all_droplets(tag_name=vm_tag)
    except:
        exit_with_error(1,"destroy: could NOT get list of machines, exiting")
    
    # Sort out what needs to be deleted
    delete_machines       = []
    if "ALL" in args:
        delete_machines = running_machine_list
        N = len(delete_machines)
        banner = "Destroying ALL Machines. Count: " + str(N) + " machine(s)"
    else:
        for item in running_machine_list:
            if item.name.startswith(base_name):
                delete_machines.append(item)
        N = len(delete_machines)
        banner = "Destroying machine series: " + base_name + ", " + str(N) + " machine(s)"
    
    fails = 0
    message(banner)
    for item in delete_machines:
        try:
            item.destroy()
            submsg(item.name + " destroyed")
        except:
            warn("Could not destroy" + item.name)
            fails+=1
    if fails >= 1:
        message("Done, but with " + fails + " failures")
        sys.exit(1)
    else:
        message("Done")

def set_config(config_dir,loaded_config,item,value):
    '''update config, vars loaded_config is a dict of values to write, the rest should be self explanitory'''
    api_file_name    = "api-key"
    config_file_name = "harbor-wave.cfg"
    api_file         = config_dir + "/" + api_file_name
    config_file      = config_dir + "/" + config_file_name
    set_item_str     = ["api-key","domain", "base-name","payload","project","size","region","template", "tag"]
    set_item_int     = ["ssh-key-n"]
    set_item_bool    = ["use-dns"]
    all_set_items    = set_item_str + set_item_int + set_item_bool
    
    ## check if valid
    # Null value check
    if item == None or item == "":
        exit_with_error(2, "set: item name can't be blank")
    # Null set now resets to default
    elif value == None or value == "":
        value = default_config[item]
    elif item not in all_set_items:
        exit_with_error(2, "set: " + item + " is not a valid config item, see help config" )
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
    # sensative items we will avoid printing.
    restricted_list = ['api_key']
    if item in restricted_list:
        exit_with_error(2,"get: Won't print " + item + "... ")
    if item not in loaded_config.keys():
        exit_with_error(2,"get: No such config item: " + item + ". See help config")
    
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
    # failed
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
    parser = argparse.ArgumentParser(description=full_help_banner,epilog="\n\n",add_help=False,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", nargs="?"   ,help="See above for description of commands")
    parser.add_argument("arguments", nargs="*" ,help="Arguments for command, see above")
    parser.add_argument("-?","--help"          ,help="Show This Help Message", action="help")
    parser.add_argument("-T","--terse"         ,help="when using list or print-config, print CSV format instead of justified tab tables. Does nothing for other options",action="store_true")

    config_overrides = parser.add_argument_group("Config Overrides","Configuration Overrides, lower case")
    config_overrides.add_argument("-a","--api-key"    ,help="Digitial Ocean API key to use",type=str)
    config_overrides.add_argument("-d","--domain"     ,help="Domain to use if --use-dns is used.",type=str)
    config_overrides.add_argument("-g","--tag"        ,help="DO tag to use on VMs so harbor-wave can identify its VMs. default: harborwave",type=str)
    config_overrides.add_argument("-k","--ssh-key-n"  ,help="Interger: index of SSH-key to use for root(or other if so configed) access. Default is 0",type=int)
    config_overrides.add_argument("-l","--payload"    ,help="Aribtrary content that gets sent to every spawned machine via user-data in API. if FILE: is specified, local file is read and used as a payload as a string",type=str)
    config_overrides.add_argument("-n","--base-name"  ,help="Base Name For New VMs",type=str)
    config_overrides.add_argument("-p","--project"    ,help="name of project in account where new machines spawn. If blank default is used",type=str)
    config_overrides.add_argument("-r","--region"     ,help="Region code. Specify what datacenter this goes in",type=str)
    config_overrides.add_argument("-s","--size"       ,help="Size code for new VMs",type=str)
    config_overrides.add_argument("-t","--template"   ,help="Image Template for spawning new VMs",type=str)
    config_overrides.add_argument("-u","--use-dns"    ,help="Use FQDNs for naming VMs and add DNS entries in Networking. NOT IMPLEMENNTED YET",action="store_true")

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
    if args.payload != None:
        loaded_config['payload']       = args.payload
    if args.project != None:
        loaded_config['project']       = args.project
    if args.tag != None:
        loaded_config['tag']           = args.tag
    if args.region != None:
        loaded.config['region']        = args.region
    if args.ssh_key_n != None:
        loaded_config['ssh-key-n']     = args.ssh_key_n
    if args.base_name != None:
        loaded_config ['base-name']    = args.base_name
    if args.size != None:
        loaded_config['size']          = args.size
    if args.template != None:
        loaded_config['template']      = args.template
    if args.use_dns == True:
        loaded_config['use-dns']       = True

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
            output_line = "list: following are valid list subcommands: machines, templates, regions, ssh-keys, sizes, and money-left. See  --help for more info"
            print(output_line)
        elif option == "machines":
            list_machines(loaded_config,args.terse)
        elif option == "projects":
            list_projects(loaded_config,args.terse)
        elif option == "templates":
            list_templates(loaded_config,args.terse)
        elif option == "regions":
            list_regions(loaded_config,args.terse)
        elif option == "ssh-keys":
            list_ssh_keys(loaded_config,args.terse)
        elif option == "sizes":
            list_sizes(loaded_config,args.terse)
        elif option == "money-left":
            list_account_balance(loaded_config,args.terse)
        else:
            exit_with_error(2,"list: Invalid option, see --help for options")
    elif args.command == "spawn":
        if len(args.arguments) >= 1:
            N = args.arguments[0]
            spawn_machines(loaded_config,N)
        else:
            spawn_machines(loaded_config)
    elif args.command == "destroy":
        if len(args.arguments) >= 1:
            options = args.arguments
        else:
            options = []
        destroy_machines(loaded_config,options)
    else:
        exit_with_error(2,"No such command. See --help")

if __name__ == "__main__":
    main()

#!/usr/bin/env python

prog_desc='''Use the Digital Ocean API to spawn temporary utility machines based
on custom templates in DO's cloud. The idea being able to rapidly create and
destroy custom machines via the DO API call. Designed to go hand and hand with
disk-image-scripts:
https://github.com/GIJack/disk-image-scripts

You need a Digital Ocean Account, set up ssh-keys, an account API, and S3 bucket
for the custom images, and a project to organize them.

the config is stored in ~/.config/harbor-wave/harbor-wave.cfg

API key is stored in ~/.config/harbor-wave/api_key

Switches override config

			COMMANDS:

  help - this text

  list-templates - Show available custom images

  list-machines  - Show virtual machines in project
  
  list-regions   - List valid region codes for use in config
  
  list-vm-sizes  - List of valid vm size codes for use in config

  spawn <N> - Create a new N new VMs. default is 1

  destroy [Name] - Destroy Name virtualmachine

  set [property] - set a config item.
    Items string:  region, project, vm-base-name, vm-template, domain, api-key
    Items bool:    use-dns
    Items Int:     ssh-key-n
    
  touch         - create a blank config file, so this can be edited by hand.

        CONFIG ITEMS:

   api-key - Digital Ocean API key, used for accessing the account
   
   region  - digital ocean region code slug to spawn new machines. You can get
   a list of valid entries with the list-reigons command
   
   project - digital ocean project name. Optional, but must exist if set. This
   project is where new VMs will spawn, and will limit to this project listing.
   
   vm-base-name - what to call VMs that will be spawned, if more than one is
   spawned, this will be the base, and new names will be incremented. At current
   this will be numeric. Might change in the future(perhaps name-sets)
   
   vm-size     - Size code for how big the VM should be.  See list-vm-sizes for
   list of size codes. Default: s-1vcpu-1gb.
   
   vm-template - ID of the custom template image for spawning VMs. you can get
   a list of valid values with list-templates
   
   use-dns     - use fully qualified domain names for VM host names, and set
   DNS in network settings. True or False.

   domain      - DNS domain to use if use-dns is set True
   
   ssh-key-n   - Interger, count from 0. Select which SSH key is being used to
   access the VM. Should display in order on the DO website. This is the ssh
   login key for root unless you have modified it with cloud-init. If you only
   have one key, this is 0
'''

import argparse
import digitalocean

def main():
    parser = argparse.ArgumentParser(description=prog_desc,epilog="\n\n",add_help=False,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("commmand", nargs="?"        ,help="See above for description of commands")
    parser.add_argument("arguments", nargs="*"       ,help="Arguments for command, see above")
    parser.add_argument("-?","--help"                ,help="Show This Help Message", action="help")

    parser.add_argument("-a","--api-key"             ,help="Digitial Ocean API key to use",type=str)
    parser.add_argument("-d","--domain"              ,help="Domain to use if --use-dns is used.",type=str)
    parser.add_argument("-k","--ssh-key-n"           ,help="Interger: index of SSH-key to use for root(or other if so configed) access. Default is 0",type=int)
    parser.add_argument("-n","--vm-base-name"        ,help="Base Name For New VMs",type=str)
    parser.add_argument("-p","--project"             ,help="Digitial Ocean Project to use",type=str)
    parser.add_argument("-s","--vm-size"             ,help="Size code for new VMs")
    parser.add_argument("-t","--vm-template"         ,help="Image Template for spawning new VMs",type=str)
    parser.add_argument("-u","--use-dns"             ,help="Use FQDNs for naming VMs and add DNS entries in Networking")

    
    args = parser.parse_args()
    print(args)

if __name__ == "__main__":
    main()

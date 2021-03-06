harbor-wave
=============

STATUS: early-alpha. All commands now implemented. --use-dns switch is not
implemented yet, everything else should work.

See TODO.md for more info.

NOTE: REPORT ALL BUGS. ISSUE TRACKER IS ENABLED AND AWAITING YOUR REPORT

Harbor Wave is a Utility for the Digital Ocean(https://digitalocean.com), cloud
service, to deploy temporary applications using droplets based on custom
templates. While using multiple machines, it is possible to deploy an
application as a swarm of droplets, each with a unique sequence number. You can
do this simply by specifying the amount of droplets with the spawn command.

Communication and interaction between droplets is up to the application in
the template, but can be facilitated via the private networking between droplets
that exists by default

Based on a digital Ocean API python lib: https://github.com/koalalorenzo/python-digitalocean

This is designed as part of an application stack with Disk-Image-Scripts, which
is to generate custom template images:
https://github.com/GIJack/disk-image-scripts


Steps
====

One
-----
Get a Digital Ocean Account.

https://cloud.digitalocean.com/registrations/new

Two
-----
Setup digital Ocean Account. You need:
* SSH Key
* API Key
* DNS(optional)

Three
------
Upload Custom Template Image to DO. This can be done in the WebUI

https://docs.digitalocean.com/products/images/custom-images/

This project is designed with Disk-Image-Scripts in mind:

https://github.com/GIJack/disk-image-scripts

You can use disk-image scripts to create custom templates based on arch, and
in the near future, debian based distros(such as Ubuntu-server), and hopefully
Redhat

TODO: add this to the script, in python(needs S3/buckets NOT in the DO lib)

Four
----
Config harbor wave
```
harbor-wave touch
```
and then edit ~/.config/harbor-wave

*OR*

```
harbor-wave set region <region_slug>
harbor-wave set api-key <your_do_api_key>
harbor-wave set vm-base-name <base_name_for_vm>
harbor-wave set ssh-key-n <N> #index of SSH key
```

SSH key index, is a count-from-0 index, you can see available keys with
```
harbor-wave list ssh-keys
```

you are ready to start spawning VMs with

```
harbor-wave spawn <N>
```
N is optional. Its a count of machines to spin up. Each will be named with
basename + sequence number.

You can get this sequence number from inside the machine with the user_data
metadata option from digital ocean's cloud:

https://docs.digitalocean.com/products/droplets/how-to/provide-user-data/

to spin down the environment use the destroy command. this will destroy all
machines with vm-basename. you can specify ALL, to destroy all machines with
the harborwave tag

```
harbor-wave destroy <"ALL">
```

List machines associated with harborwave(based on tag)
```
harbor-wave list machines
```
List available config values, as pulled from DO servers:
```
harbor-wave list regions
harbor-wave list vm-sizes
harbor-wave list templates
harbor-wave list ssh-keys
```
You may add terse at the end of a list command for a CSV list instead of tabbed
tables

Show you Digital Ocean account balance. NOTE, you cannot add funds with this
tool
```
harbor-wave list money-left
```

For more info see either
```
man 1 harbor-wave
harbor-wave --help
```

harbor-wave
=============

STATUS: early-alpha. All commands now implemented, largely untested and
documentation and autocomplete not done

Harbor Wave is a Utility for the Digital Ocean(https://digitalocean.com), cloud
service, to rapidly spin up and destroy droplets based on custom templates.
Based on a digital Ocean API python lib:

https://github.com/koalalorenzo/python-digitalocean

created with custom templates created by disk-image-scripts in mind:
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

SSH key index, is a count-from-0 index

you are ready to start spawning VMs with

```
harbor-wave spawn <N>
```
N is optional. Its a count of machines to spin up

or delete with

```
harbor-wave destroy [vm-name]
```

List machines associated with harborwave, by tag(set tag)
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

Show you Digital Ocean account balance. NOTE, you cannot add funds via the API.
```
harbor-wave list money-left
```

For more info see either
```
man 1 harbor-wave
harbor-wave --help
```

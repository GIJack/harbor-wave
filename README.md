harbor-wave
=============

STATUS: in progress. get,set,print-config, and list commmands all implemented
and usable. TODO: create/destroy

Harbor Wave is a Utility for the Digital Ocean(https://digitalocean.com), cloud
service, to rapidly spin up and destroy custom templates. Based on a digital
ocean API python lib:

https://github.com/koalalorenzo/python-digitalocean

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
* Project(used as container)
* DNS(optional)
* API Key

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
harbor-wave set project <your_project_name>
harbor-wave set api-key <your_do_api_key>
harbor-wave set vm-base-name <base_name_for_vm>
```

you are ready to start spawning VMs with

```
harbor-wave spawn
```

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
```

Show you Digital Ocean account balance. NOTE, you cannot add funds via the API.
```
harbor-wave list money-left
```

For more info see either
```
man 1 harbor-wave
harbor-wave --help
```

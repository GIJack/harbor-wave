harbor-wave
=============

STATUS: MOCKUP. At this point, this is little more than a UI and config
mockup. Work in Progress

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

List VMs in project

```
harbor-wave list-machines
```
Avaible Templates:
```
harbor-wave list-templates
```

For more info see either
```
man 1 harbor-wave
harbor-wave --help
```

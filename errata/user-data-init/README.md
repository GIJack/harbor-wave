User Data Initialization
========================
Python script and cloud-init config for proccessing harbor-wave user-data.

You can build your application with this script and cloud-init config, to parse
harbor-wave user-config metadata

If you are using disk-image-scripts, be sure to throw
this in the rootoverlay/ folder

harborwave\_init_\meta.py -
This script does three things:
1. download metadata from digital ocean API
2. extract payload and save it as a file in /opt/harbor-wave/payload
3. add HARBORWAVE\_SEQUENCE and HARBORWAVE\_BASENAME and their corresponding
values to /etc/environment so they can easily be refrenced by an application
on the droplet/machine spawned

99\_harborwave-init.cfg -
Put this in /etc/cloud/cloud.cfg.d on your rootoverlay/ when you are building
your app. This will run the python script above on first boot
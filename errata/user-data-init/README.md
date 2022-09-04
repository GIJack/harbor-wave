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
2. extract payload and save it as a file in the /opt/harbor-wave/payload
directory. It is saved as its original filename if FILE: was in the payload. If
there was no filename, then the file is just named "data"
3. add HARBORWAVE\_SEQUENCE and HARBORWAVE\_BASENAME and their corresponding
values to /etc/environment so they can easily be refrenced by an application
on the droplet/machine spawned

HOW TO
-------

harborwave-runonce.service - put this in your systemd service folder and
enable it with systemctl.

normal systemd service folder - /usr/local/systemd/system.

harborwave\_init\_meta.py - install this as /root/harborwave\_init\_meta.py

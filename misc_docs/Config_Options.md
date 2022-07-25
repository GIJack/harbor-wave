CONFIG ITEMS
============

here is a list of items that can be configured. these work with get or set

**api-key**(*string*) - Digital Ocean Account API Key. Get this from the web interface


**domain**(*string*) DNS domain to use if **use-dns** is set True. This domain needs
to be already setup in Digital Ocean Networking for this to work.

**project**(*string*) Digital Ocean uses "projects" as subfolders for objects.
if this is not "" new machines will spawn in the configured project for easy
manager. Project must exist. default is unset

**payload**(*string* OR *file*) Input data from your local machine and made
availble over the Digital Ocean API, for use with cloud-init or other. This is a
string unless it starts with *FILE*:. In this case, file contents are uploaded

**region**(*string*) Digital Ocean region code. Droplets will spawn in this DO
region, but list will show all regions, and destroy terminate accross all regions.

Default: _nyc1_

**ssh-key-n**(*int*) Interger. Index of SSH-key on your digital ocean account
that will be used with new machines spawned.

**tag**(*string*) Droplet tag used to identify harborwave machines. spawn will
make droplets with this tag, and list and destroy will only match droplets with
this tag.  Default: harborwave

**vm-base-name**(*string*) Basename for VMs created with spawn and destroyed
with destroy. Indivual machines are named vm-base-name + N. destroy matches
against machines that have the correct tag and start with vm-base-name.

**vm-size**(*string*) Size code for new droplets. This will determine things
like Hard Disk, CPU and RAM. see **list vm-sizes** for codes and what they
do.

**vm-template**(*string*) ID of template for creating new machines with spawn.
See _list templates_ for valid entries

**use-dns**(*bool*) To use FQDNs and create DNS entries for machines spawned.
**domain** item also needs to be set.

default: *False*

Not currently implemented

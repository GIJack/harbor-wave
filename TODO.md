TODO
====

Items to implement

Needed
------
* DNS - implement --use-dns to make machines with FQDN. Big stopper is that IP
address is not returned from machine creation. Need new way of doing this
* Push image template - need way to push template that is local to Digital Ocean. This
means we need access to a spaces(S3-type bucket), and this is not in the python
module. this might be added to disk image scripts.

Brainstorming
-----
* Add support for Digital Ocean Projects, putting new VMs in specify project.
initially part of the design, but removed as there was no immediate way of doing
this
* Add support for custom cloud-init fields in droplet creation.
sequence=i will be added, so each droplet in a creation sequence will have a
unique identifer that is proccessed by cloud-init, and whatever custom scripts
and programs you have within the droplet.

this would also allow with the right program a machine/droplet to have the same
program, but execute diffrent roles based on position in the sequence, i.e.
the machine with sequence 1 can know to be the head node, and the rest would
know to connect to 1, or use other math based scheme for connecting to eachother

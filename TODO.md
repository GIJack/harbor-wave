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
* More intellegent spawn/destroy logic, more complex rules.
* perhaps more cloud-init custom data? Perhaps someway to feed applications at
spawn time, such as a parameter or switch?"

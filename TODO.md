TODO
====

Items to implement

Needed
------
* DNS - implement --use-dns to make machines with FQDN. Big stopper is that IP
address is not returned from machine creation. It is generally several seconds
perhaps 1 minuete until IP address is known to the UI. Need new way of doing this
* Projects - implement project code. Add new droplets/machines to account project
this will help declutter and management esepcially if you have other machines
that aren't harbor-wave applications. It would be a decent idea to just put them
in a harbor-wave specific project. Unlike previous design idea, this will NOT
limit delete or list, as these will be based on tags.
* Push image template - need way to push template that is local to Digital Ocean. This
means we need access to a spaces(S3-type bucket), and this is not in the python
module. this might be added to disk-image-scripts, being that if called from
a disk-image-scripts template, we could use metadata to create template images
on digital ocean. This information is lost once processed into an image.
* Setup packaging

Brainstorming
-----
* Add support for Digital Ocean Projects, putting new VMs in specify project.
initially part of the design, but removed as there was no immediate way of doing
this
* More intellegent spawn/destroy logic, more complex rules.
* Such as timer, instance lives for N Seconds/Minuetes
* Instance stops certain date-time
* Instance runs until X job is complete, does Y task to send data back to user
and then terminates the instance
* think of, and codify user_data metadata format. so far we have sequence=N.
Perhaps we want to add more stuff, such as parameters from config with set
or switch on the command line.
* use grouping of machines by name in list machines. perhaps an option for only
listing the base names, or first machine in a series, and then count of total
machines.
* better support for more than one application, besides simply specifying -n
in run time or scripting with set vm-base-name
* use multiple reigons for spawning new machines

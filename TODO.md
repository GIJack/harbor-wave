TODO
====

Items to implement

Needed
------
* DNS - implement --use-dns to make machines with FQDN. Big stopper is that IP
address is not returned from machine creation. It is generally several seconds
perhaps 1 minuete until IP address is known to the UI. Need new way of doing this
* Push image template - need way to push template that is local to Digital Ocean. This
means we need access to a spaces(S3-type bucket), and this is not in the python
module. this might be added to disk-image-scripts, being that if called from
a disk-image-scripts template, we could use metadata to create template images
on digital ocean. This information is lost once processed into an image.
* Setup python packaging?

Brainstorming
-----
* More intellegent spawn/destroy logic, more complex rules.
* Such as timer, instance lives for N Seconds/Minuetes
* Instance stops certain date-time
* Instance runs until X job is complete, does Y task to send data back to user
and then terminates the instance
* think of, and codify user_data metadata format. so far we have sequence=N.
Perhaps we want to add more stuff, such as parameters from config with set
or switch on the command line. payload?
* use grouping of machines by name in list machines. perhaps an option for only
listing the base names, or first machine in a series, and then count of total
machines.
* better support for more than one application, besides simply specifying -n
in run time or scripting with set vm-base-name
* use multiple reigons for spawning new machines
* cloud-init phone-home examples for passing notifications on donnage?

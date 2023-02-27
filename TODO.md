TODO
====

Items to implement

Needed
------
* Push image template - need way to push template that is local to Digital Ocean. This
means we need access to a spaces(S3-type bucket), and this is not in the python
module. this might be added to disk-image-scripts, being that if called from
a disk-image-scripts template, we could use metadata to create template images
on digital ocean. This information is lost once processed into an image.
* Mechanism/API for returning data to the command line(STDOUT/STDERR) from
droplet when done

Brainstorming
-----
* More intellegent spawn/destroy logic, more complex rules.
* Such as timer, instance lives for N Seconds/Minuetes
* Instance stops certain date-time
* Instance runs until X job is complete, does Y task to send data back to user
and then terminates the instance
* use grouping of machines by name in list machines. perhaps an option for only
listing the base names, or first machine in a series, and then count of total
machines.
* use multiple reigons for spawning new machines
* cloud-init phone-home examples for passing notifications on donnage?
* Ability to modify application/name space running without stop, i.e. delete/
respawn specific hosts/rage, grow or shrink the same series. - This requires
harbor-wave to be stateful, and it is currently stateless tho.
* Setup python packaging?

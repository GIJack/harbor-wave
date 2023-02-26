PASSING DATA
============

harbor-wave uses the Digital Ocean user-data field in the Droplet Metadata API
to pass information to droplets from the harbor-wave source computer.

API refrence: https://docs.digitalocean.com/reference/api/metadata-api/#operation/getUserData

Hostnames are generated as base-name + sequence. To eliminate any confusion,
these are listed as structured data in the API, as well as a payload, which was
designed to pass arbitrary data from the computer. This can be contents of a
file, as well as just an arbitrary text string.

JSON FIELDS
------------

harbor-wave data is a JSON array with five fields:

**sequence**	- is a number. This is so that a machine can tell where it was in
the spawn sequence, and if you were to write a swarm/mesh or even multi-machine
environment, the machine can use this number to determine its role, and identify
itself to other machines, and for multi-role machines with the same programming
can determine their role based on the sequence.

A big example,  is making sequence 0 the head machine, as it is guarunteed to
be there, and for whatever hub or cordinating data can be safely done by this
machine.

**base-name**	- the machine has a refrence name of the larger application
payload. This can be used

**domain**	- DNS domain name used on command line

**payload**	- arbitrary data from --payload or the payload setting. This
can be either a string entered, or the contents of a file specified with FILE:
in the payload field

**payload-filename**	- if "FILE:" was used for payload, the name of the file.
if "FILE:" was not used, this will be an empty string, ""

EXAMPLE
-------
a simple query of the API will look something like this. 
```
curl 169.254.169.254/metadata/v1/user-data
{
  "sequence": 0,
  "base-name": "saphire",
  "domain": "example.com"
  "payload": "",
  "payload-filename": ""
}
```

A ready to use script for parsing this data, saving the payload as a file, and
setting sequence and base-name as environment variables for linux is here:

https://github.com/GIJack/harbor-wave/tree/main/errata/user-data-init



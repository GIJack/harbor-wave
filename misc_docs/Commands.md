COMMANDS
========
harbor-wave revolves around 'spawn' and 'destroy'. spawn creates the environment
and destroy takes it down. Ideally, destroy will be taking down the machines
that were created by spawn. This is to make short lived user applications
worthwhile with min efforts

ACTIONS
-------

**SPAWN**  *N*		Where N is a interger. Creates N amount of virtual
machines using previously set settings, or --overide options. If N is not
specified, then 1 is the default.

if the -T,--terse option is used, then a comma seperated list of name:ip pairs.

e.g.
machine1:192.0.2.50,machine2:192.0.2.51

**DESTROY** *\<ALL\>*	Destroy all virtual machines that match "tag" from
settings, and their name begins with "base-name". if ALL in all caps is
specified, then all machines with matching "tag" are deleted, not just those
matching "base-name". The idea would be normally this will just take down only
the machines immediately spawned previously with spawn, or optionally with the
the --base-name/-n switch, a previous harbor-wave application

if the -T,--terse option is used, then just a list of machine names destroyed
is printed

CONFIGURATION
-------------
Configuration is saved and read from a JSON file in
~/.config/harbor-wave/harbor-wave.cfg

These are the commands to read and manipulate it.

**SET** *ITEM* *VALUE*	Set a configuration item.

**GET** *ITEM*		Retrieve a configuration item. Prints only the value

**PRINT-CCONFIG**	With no parameters. Prints a table with the config as
KEY and VALUE pairs. if used with -T,--terse, then the same data is printed
without table headers, and as CSVs.

**TOUCH**		Touches the config, and exits. This is for generating
a blank config file that can be further manipulated

**CHECK-CONFIG**	Checks that items are correct, can be used to
troubleshoot spawn/list/destroy. All items before Account are offline checks
of the config. Account checks if your API key returns an valid account. The
rest of the checks see if the corresponding item exists in your Digital Ocean
Account

OTHER
-----
**LIST** *TYPE*		List various kinds of items in your Digital Ocean that
you'd need to set as config items. The leftmost column is always the one that
harbor-wave needs for settings.

**HELP** *\<COMMAND\|CONFIG\>*		Prints the help message,
sub commands of command and config for just help with config or commands

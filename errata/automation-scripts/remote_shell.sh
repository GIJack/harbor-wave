#!/usr/bin/env bash

help_and_exit(){
  cat 1>&2 << EOF
remote_shell.sh:

spawn a VM with harbor-wave and ssh into it. Destroy when shell exits. Needs
harbor-wave setup and a template installed to DO that can ssh with key.
EOF
  exit 4
}

### Variables
name="" #set this to something unique
template="" # get from harbor-wave list templates
region="" # get from harbor-wave list templates
size="s-1vcpu-1gb" #get from harbor-wave list sizes
# for the VM, needs to have ssh key setup with same key that is on your DO
# account. If you don't know, use "root", with is cloud-init default
username="root" 
### /Variables

### CONSTANTS
N=1
wait_time=10
### /CONSTANTS

exit_with_error(){
  echo 1>&2 "remote_shell.sh: ERROR: ${2}"
  exit ${1}
}

_spawn(){
  extra_commands="${@}"
  harbor-wave spawn ${N} --terse --base-name "${name}" --template "${template}" --region "${region}" --size "${size}" ${extra_commands}
}
_destroy(){
  extra_commands="${@}"
  harbor-wave destroy --terse --base-name "${name}" > /dev/null
}

main(){
  # banner
  [[ ${1} == *help* ]] && help_and_exit
  # checks
  [ -z "${name}" ] && exit_with_error 2 "name not set"
  [ -z "${template}" ] && exit_with_error 2 "template not set"
  [ -z "${region}" ] && exit_with_error 2 "region not set"
  [ -z "${size}" ] && exit_with_error 2 "size not set"
  [ -z "${username}" ] && exit_with_error 2 "size not set"
  # emergency abort
  trap _destroy 2 3 6 9
  
  # Gemerate the machine
  host_ip=$(_spawn "${@}") || exit_with_error 1 "Could not start Digial Ocean VM, see harbor-wave output"
  # ssh to machine
  ip_address=$(cut -d ":" -f 2 <<<  ${host_ip})
  sleep ${wait_time} # wait to see if this resolves
  ssh -o "UserKnownHostsFile=/dev/null" -o "StrictHostKeyChecking=no" "${username}@${ip_address}"
  #cleanup when done
  _destroy
}

main "${@}"


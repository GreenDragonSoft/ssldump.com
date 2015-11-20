#!/bin/sh -eux

THIS_SCRIPT=$0
THIS_DIR=$(dirname ${THIS_SCRIPT})

cd ${THIS_DIR}
ansible-playbook -i hosts --limit=webservers playbook.yml

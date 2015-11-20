#!/bin/sh -eux

# USAGE: run.sh /path/to/virtualenv

THIS_SCRIPT=$0
THIS_DIR=$(dirname ${THIS_SCRIPT})

VENV_BASE_DIR=${1}

. ${THIS_DIR}/get_virtualenv_from_requirements_file.sh

activate_virtualenv() {
    VIRTUALENV=$(get_virtualenv_from_requirements_file ${VENV_BASE_DIR})
    set +u
    . ${VIRTUALENV}/bin/activate
    set -u
}

run_webapp() {
    ${THIS_DIR}/../app/main.py
}


activate_virtualenv
run_webapp

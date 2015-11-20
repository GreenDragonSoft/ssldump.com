#!/bin/sh -eux

# USAGE: create_virtualenv.sh /path/to/virtualenv-base-directory

THIS_SCRIPT=$0
THIS_DIR=$(dirname ${THIS_SCRIPT})

VENV_BASE_DIR=${1}

. ${THIS_DIR}/get_virtualenv_from_requirements_file.sh


create_and_activate_virtualenv() {
    VIRTUALENV=$(get_virtualenv_from_requirements_file ${VENV_BASE_DIR})

    if [ ! -d "${VIRTUALENV}" ]; then
        virtualenv -p $(which python3) "${VIRTUALENV}"
    fi

    set +u
    . ${VIRTUALENV}/bin/activate
    set -u
}

install_requirements() {
    pip install -r ${THIS_DIR}/../requirements.txt
}

create_and_activate_virtualenv
install_requirements

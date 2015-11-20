#!/bin/sh -eu

THIS_SCRIPT=$0
THIS_DIR=$(dirname ${THIS_SCRIPT})

get_virtualenv_from_requirements_file() {
    # Create the virtualenv based on the hash of the requirements file
    REQUIREMENTS_FILE=${THIS_DIR}/../requirements.txt
    REQUIREMENTS_HASH=$(sha256sum ${REQUIREMENTS_FILE} |cut '-d ' -f1)
    echo ${VENV_BASE_DIR}/ssldump_venv_${REQUIREMENTS_HASH}
}

#!/bin/bash
WORKSPACE_PATH=`pwd`
echo "${WORKSPACE_PATH}"
DEFAULT_FILE_SOURCE_PATH="${WORKSPACE_PATH}/default.cfg"
SPEC_FILE_PATH="${WORKSPACE_PATH}/ansible-gen.spec"
PACKAGE_OUTPUT_PATH="/usr/bin"
if [ ! -d "/etc/ansible-gen" ]; then
	mkdir /etc/ansible-gen
fi

DEFAULT_FILE_DEST_PATH="/etc/ansible-gen/"
echo "${DEFAULT_FILE_DEST_PATH}"
cp -f ${DEFAULT_FILE_SOURCE_PATH} ${DEFAULT_FILE_DEST_PATH}

if [ "which pyinstaller" ] ;then
	pyinstaller ${SPEC_FILE_PATH} --distpath ${PACKAGE_OUTPUT_PATH}
else
	if [ "which pip" ]; then
		echo "try install pyinstaller"
		pip install pyinstaller
		pyinstaller ${SPEC_FILE_PATH} --distpath ${PACKAGE_OUTPUT_PATH}
	else
		echo "Please install pip"
		exit 1
	fi
	echo "no pyinstaller"
fi

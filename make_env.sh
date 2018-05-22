#!/bin/sh

set -eu

which virtualenv > /dev/null 2>&1 || ( echo "Can't find virtualenv utility in PATH" ; exit 255 )

virtualenv -p python3 venv
. ./venv/bin/activate
pip install -r requirements.txt

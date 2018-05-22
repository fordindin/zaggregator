#!/bin/sh


. ./venv/bin/activate

set -eu

dir=$(dirname $0)/
cd $dir

SUDO=""
set +u
if [ "$1" = "-s" ]; then
    SUDO=$(which sudo)
else
    printf "Some tests require root priveleges, see test.log for details\nYou can run $0 -s for this functionality\n"
fi
set -u

$SUDO python3 -m zaggregator.tests

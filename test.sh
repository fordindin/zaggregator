#!/bin/sh

set -eu

ASYNCIO_WAIT=3
DAEMON_WAIT=5

dir=$(dirname $0)/
cd $dir
set +eu
. ./venv/bin/activate
set -eu

SUDO=""
set +u
if [ "$1" = "-s" ]; then
    SUDO=$(which sudo)
elif [ $(id -u) -eq 0 ]; then
    : ${0}
else
    printf "Some tests require root priveleges, see test.log for details\nYou can run $0 -s for this functionality\n"
fi
set -u

unittests(){
    $SUDO python3 -m zaggregator.tests
}


echo "Running daemon-mode tests"

killtest()
{
    set -eu

    eval _wait="\$${1}"
    sleep ${_wait}
    kill -15 $testpid
    set +eu
}

asyncio_test(){
    echo "$(($ASYNCIO_WAIT-1)) cycles with dummmy asyncio server"
    python3 ./zaggregator/tests/run_asyncio.py & testpid=$! && echo "PID: $testpid" && killtest ASYNCIO_WAIT &
    wait
    echo ""
}

daemon_test(){
    echo "$(($DAEMON_WAIT-1)) cycles with real zaggregator server"
    python3 -m zaggregator & testpid=$! && echo "PID: $testpid" && killtest DAEMON_WAIT &
    wait
    echo ""
}

_fkill(){
    kill -15 $testpid
}

trap _fkill 1 2 4 15
unittests
#asyncio_test
#daemon_test

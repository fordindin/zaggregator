#!/bin/sh


. ./venv/bin/activate

set -eu

dir=$(dirname $0)/
cd $dir
python3 -m zaggregator.tests

#!/bin/sh


. $(dirname $0)/venv/bin/activate
python3 -m zaggregator $@


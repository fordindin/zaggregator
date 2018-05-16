#!/bin/sh


. $(dirname $0)/venv/bin/activate
python3 $(dirname $0)/src/main.py $@


#!/bin/sh

BASE=$(dirname $0)
. ${BASE}/venv/bin/activate
echo "`date`:$@" >> /tmp/zag.log 2>&1
cd ${BASE} && python3 -m zaggregator $@ 2>&1 | tee -a /tmp/zag.log 


#!/bin/sh

BASE=$(dirname $0)
. ${BASE}/venv/bin/activate
cd ${BASE} && python3 -m zaggregator $@


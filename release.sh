#!/bin/sh

python3 setup.py egg_info -Db "" sdist bdist_egg upload

#!/bin/sh

set -eu

selfname=$(basename $0)
usage(){
    printf "
    ${selfname} <version>
    where <version> - release version

    example:

        ./${selfname} 1.2.3

    will create tag zaggregator-1.2.3-release, push this tag to origin;
    than build pip package for zaggregator and push it to pipy repo

"
}

if [ $# -lt 1 ]; then
    usage
    exit 1
fi

exit 1
python3 setup.py egg_info -Db "" sdist bdist_egg upload

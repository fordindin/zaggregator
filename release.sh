#!/bin/sh

set -eu

selfname=$(basename $0)
usage(){
    printf "
    ${selfname} <version>
    where <version> - release version

    example:

        ./${selfname}

    will create tag zaggregator-1.2.3-release, push this tag to origin;
    than build pip package for zaggregator and push it to pipy repo

"
}

set +u
if [ "$1" = "-h" -o "$1" = "--help" ]; then
    usage
    exit 1
fi
set -u

version=$(grep 'version=' setup.py | cut -d= -f 2 | tr -d '",')

git status | grep 'working tree clean' || ( echo "Clean working tree first (see 'git status' output)" && exit 1 )
git tag zaggregator-version-release
git push --tags
python3 setup.py egg_info -Db "" sdist bdist_egg upload

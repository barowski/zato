#!/bin/bash

#
# Taken from https://gist.github.com/josephwecker/2884332
#
CURDIR="${BASH_SOURCE[0]}";RL="readlink";([[ `uname -s`=='Darwin' ]] || RL="$RL -f")
while([ -h "${CURDIR}" ]) do CURDIR=`$RL "${CURDIR}"`; done
N="/dev/null";pushd .>$N;cd `dirname ${CURDIR}`>$N;CURDIR=`pwd`;popd>$N

function symlink_py {
    ln -s `python -c 'import '${1}', os.path, sys; sys.stdout.write(os.path.dirname('${1}'.__file__))'` $CURDIR/zato_extra_paths
}

rm -rf $CURDIR/bin
rm -rf $CURDIR/develop-eggs
rm -rf $CURDIR/downloads
rm -rf $CURDIR/eggs
rm -rf $CURDIR/include
rm -rf $CURDIR/.installed.cfg
rm -rf $CURDIR/lib
rm -rf $CURDIR/parts
rm -rf $CURDIR/zato_extra_paths

sudo yum install git bzr gcc-gfortran haproxy \
    rubygem-sass atlas-devel atlas blas-devel  \
    libevent-devel libgfortran lapack-devel lapack \
    libpqxx-devel libyaml-devel libxml2-devel libxslt-devel suitesparse \
    openssl python-devel m2crypto numpy python-pip \
    scipy python-zdaemon swig uuid-devel uuid

mkdir $CURDIR/zato_extra_paths

symlink_py 'M2Crypto'
symlink_py 'numpy'
symlink_py 'scipy'

sudo pip-python install --upgrade distribute
sudo pip-python install --upgrade virtualenv

virtualenv .

$CURDIR/bin/python bootstrap.py -v 1.7.0
$CURDIR/bin/buildout

echo
echo OK

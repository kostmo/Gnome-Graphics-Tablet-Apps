#!/bin/bash

. src/package_defines.mk

./clean_package_files.sh

cd src
dch -m
cd ..
cp -r src $RELEASE_NAME.orig
cd $RELEASE_NAME.orig
rm -r debian
cd ..
cp -r src $RELEASE_NAME
cd $RELEASE_NAME
debuild -S -sa
cd ..
rm -r $RELEASE_NAME


CHANGES_FILE=${DISTRIBUTABLE_NAME}-*_source.changes

echo "You might want to run 'dput ppa:kostmo/ppa $CHANGES_FILE' next"
echo "-or-"
echo "run 'dput revu $CHANGES_FILE'"

#!/bin/bash

. code/package_defines.mk

./clean_package_files.sh

cd code
dch -m
cd ..
cp -r code $RELEASE_NAME.orig
cd $RELEASE_NAME.orig
rm -r debian
cd ..
tar -cvf $RELEASE_NAME.orig.tar $RELEASE_NAME.orig

cp -r code $RELEASE_NAME
cd $RELEASE_NAME
debuild -S -sa
cd ..
rm -r $RELEASE_NAME


CHANGES_FILE=${DISTRIBUTABLE_NAME}-*_source.changes

echo "You might want to run 'dput ppa:kostmo/ppa $CHANGES_FILE' next"
echo "-or-"
echo "run 'dput revu $CHANGES_FILE'"

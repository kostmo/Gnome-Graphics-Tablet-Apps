#!/bin/bash

. src/package_defines.mk

./clean_package_files.sh

cp -r src $RELEASE_NAME.orig
cd $RELEASE_NAME.orig
rm -r debian
cd ..
cp -r src $RELEASE_NAME
cd $RELEASE_NAME
debuild
cd ..
rm -r $RELEASE_NAME

echo -n "Do you want to install the new .deb? [Y/n]: "
read character
case $character in
    [Yy] | "" ) echo "You responded in the affirmative."
	sudo gdebi *.deb
        ;;
    * ) echo "Fine, then."
esac

#!/bin/bash

# Create symlinks from ~/mitx_all/data or $ROOT/data, with root passed as first arg
# to all the test courses in mitx/common/test/data/

ROOT=$HOME/mitx_all

# If there is a parameter, and it's a dir, assuming that's the path to
# the edX root dir, with data and mitx inside it
if [ -d "$1" ]; then
   ROOT=$1
fi

if [ ! -d "$ROOT" ]; then
   echo "'$ROOT' is not a directory"
   exit 1
fi

if [ ! -d "$ROOT/mitx" ]; then
    echo "'$ROOT' is not the root mitx_all directory"
    exit 1
fi

if [ ! -d "$ROOT/data" ]; then
    echo "'$ROOT' is not the root mitx_all directory"
    exit 1
fi

echo "ROOT is $ROOT"

cd $ROOT/data
for course in `ls ../mitx/common/test/data/`
do
  # Get rid of the symlink if it already exists
   echo "Make link to '$course'"
   rm -f "$course"
   # Create it
   ln -s "../mitx/common/test/data/$course"
done

# go back to where we came from
cd -

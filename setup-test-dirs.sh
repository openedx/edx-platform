#!/usr/bin/env bash

# Create symlinks from ~/mitx_all/data or $ROOT/data, with root passed as first arg
# to all the test courses in mitx/common/test/data/

# posix compliant sanity check
if [ -z $BASH ] || [ $BASH = "/bin/sh" ]; then
echo "Please use the bash interpreter to run this script"
exit 1
fi

ROOT="${1:-$HOME/mitx_all}"

if [[ ! -d "$ROOT" ]]; then
   echo "'$ROOT' is not a directory"
   exit 1
fi

if [[ ! -d "$ROOT/mitx" ]]; then
    echo "'$ROOT' is not the root mitx_all directory"
    exit 1
fi

if [[ ! -d "$ROOT/data" ]]; then
    echo "'$ROOT' is not the root mitx_all directory"
    exit 1
fi

echo "ROOT is $ROOT"

cd $ROOT/data

for course in $(/bin/ls ../mitx/common/test/data/)
do
  # Get rid of the symlink if it already exists
   if [[ -L "$course" ]]; then
       echo "Removing link to '$course'"
       rm -f $course
   fi
   echo "Make link to '$course'"
   # Create it
   ln -s "../mitx/common/test/data/$course"
done

# go back to where we came from
cd -

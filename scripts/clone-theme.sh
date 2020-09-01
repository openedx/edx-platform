#!/usr/bin/env bash

set -e

theme_clone_path='/edx/src/philu-edx-theme'
if [ -e $theme_clone_path ]; then
    rm -rf $theme_clone_path
fi
sudo mkdir -p $theme_clone_path;
sudo chmod 755 -R /edx/src;
sudo chown -R jenkins:jenkins /edx/src;
git clone https://philanthropyu:${THEME_USER_PASSWORD}@github.com/philanthropy-u/philu-edx-theme.git $theme_clone_path

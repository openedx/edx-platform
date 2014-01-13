#!/bin/bash -e
#
# Copyright (C) 2013 edX <info@edx.org>
#
# Authors: Xavier Antoviaque <xavier@antoviaque.org>
#          David Baumgold <david@davidbaumgold.com>
#          Yarko Tymciurak <yarkot1@gmail.com>
#
# This software's license gives you freedom; you can copy, convey,
# propagate, redistribute and/or modify this program under the terms of
# the GNU Affero General Public License (AGPL) as published by the Free
# Software Foundation (FSF), either version 3 of the License, or (at your
# option) any later version of the AGPL published by the FSF.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program in a file in the toplevel directory called
# "AGPLv3".  If not, see <http://www.gnu.org/licenses/>.


###############################################################################

# vagrant-provisioning.sh:
#
# Script to setup base environment on Vagrant, based on `precise32` image
# Runs ./scripts/create-dev-env.sh for the actual setup
#
# This script is ran by `$ vagrant up`, see the README for more explanations

on_create()
{
    # APT - Packages ##############################################################

    apt-get update
    apt-get install -y python-software-properties vim


    # Curl - No progress bar ######################################################

    [[ -f ~vagrant/.curlrc ]] || echo "silent show-error" > ~vagrant/.curlrc
    chown vagrant.vagrant ~vagrant/.curlrc


    # SSH - Known hosts ###########################################################

    # Github
    ([[ -f ~vagrant/.ssh/known_hosts ]] && grep "zBX7bKA= ssh" ~vagrant/.ssh/known_hosts) || {
	echo "|1|4DtBcMsTM4zgl/jTS7h3ZkmS/Vc=|XkRnn2xEhr8ixOxeskJAzBX7bKA= ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAq2A7hRGmdnm9tUDbO9IDSwBK6TbQa+PXYPCPy6rbTrTtw7PHkccKrpp0yVhp5HdEIcKr6pLlVDBfOLX9QUsyCOV0wzfjIJNlGEYsdlLJizHhbn2mUjvSAHQqZETYP81eFzLQNnPHt4EVVUh7VfDESU84KezmD5QlWpXLmvU31/yMf+Se8xhHTvKSCZIFImWwoG6mbUoWf9nzpIoaSjB+weqqUUmpaaasXVal72J+UX2B+2RPW3RcT0eOzQgqlJL3RKrTJvdsjE3JEAvGq3lGHSZXy28G3skua2SmVi/w4yCE6gbODqnTWlg7+wC604ydGXA8VJiS5ap43JXiUFFAaQ==" >> ~vagrant/.ssh/known_hosts
    }
    ([[ -f ~vagrant/.ssh/known_hosts ]] && grep "jO3J5bvw= ssh" ~vagrant/.ssh/known_hosts) || {
	echo "|1|9rANf/qOAPgKH/TXpGuZCAgGxMs=|x9VYWEDI8kiotbhhNXqjO3J5bvw= ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAq2A7hRGmdnm9tUDbO9IDSwBK6TbQa+PXYPCPy6rbTrTtw7PHkccKrpp0yVhp5HdEIcKr6pLlVDBfOLX9QUsyCOV0wzfjIJNlGEYsdlLJizHhbn2mUjvSAHQqZETYP81eFzLQNnPHt4EVVUh7VfDESU84KezmD5QlWpXLmvU31/yMf+Se8xhHTvKSCZIFImWwoG6mbUoWf9nzpIoaSjB+weqqUUmpaaasXVal72J+UX2B+2RPW3RcT0eOzQgqlJL3RKrTJvdsjE3JEAvGq3lGHSZXy28G3skua2SmVi/w4yCE6gbODqnTWlg7+wC604ydGXA8VJiS5ap43JXiUFFAaQ==" >> ~vagrant/.ssh/known_hosts
    }
    chown vagrant.vagrant ~vagrant/.ssh/known_hosts


    # edX - Development environment ###############################################

    # Node modules require a filesystem with symlinks (Windows support)
    mkdir -p /opt/edx/node_modules /opt/edx/edx-platform/node_modules
    ([[ -f /etc/fstab ]] && grep '/opt/edx/node_modules' /etc/fstab) || {
        echo '/opt/edx/node_modules /opt/edx/edx-platform/node_modules none bind,noauto 0 0' >> /etc/fstab
        mount /opt/edx/node_modules
    }
    # Must be mounted *after* the NFS mount, made manually by Vagrant
    ([[ -f /etc/cron.d/nodemodules ]] && grep '/opt/edx/node_modules' /etc/cron.d/nodemodules) || {
        echo '@reboot root until [ -n "`mount |grep "/opt/edx/edx-platform type"`" ]; do sleep 1; done; mount /opt/edx/node_modules' > /etc/cron.d/nodemodules
    }

    # Force rechecking all prerequisites (could have been fetched outside of the VM)
    rm -rf /opt/edx/edx-platform/.prereqs_cache

    # Permissions
    chown vagrant.vagrant /opt/edx /opt/edx/node_modules /opt/edx/edx-platform/node_modules

    # For convenience with `vagrant ssh`, the `edx-platform` virtualenv is always
    # loaded after the first run, so we need to deactivate that behavior to run
    # `create-dev-env.sh`.
    [[ -f ~vagrant/.bash_profile ]] && {
	mv ~vagrant/.bash_profile ~vagrant/.bash_profile.bak
    }
    sudo -u vagrant -i bash -c "cd /opt/edx/edx-platform && PROJECT_HOME=/opt/edx ./scripts/create-dev-env.sh -ynq"

    # Load .bashrc ################################################################
    ([[ -f ~vagrant/.bash_profile ]] && grep ".bashrc" ~vagrant/.bash_profile) || {
	echo ". /home/vagrant/.bashrc" >> ~vagrant/.bash_profile
    }


    # Virtualenv - Always load ####################################################

    ([[ -f ~vagrant/.bash_profile ]] && grep "edx-platform/bin/activate" ~vagrant/.bash_profile) || {
	echo ". /home/vagrant/.virtualenvs/edx-platform/bin/activate" >> ~vagrant/.bash_profile
    }


    # Directory ###################################################################

    grep "cd /opt/edx/edx-platform" ~vagrant/.bash_profile || {
	echo "cd /opt/edx/edx-platform" >> ~vagrant/.bash_profile
    }

    # Permissions
    chown vagrant.vagrant ~vagrant/.bash_profile

    # Install completed entirely & successfully - set flag to skip in future runs
    touch /opt/edx/.install_succeeded

    cat << EOF
==============================================================================
Success - Created your development environment!
==============================================================================

EOF
}    # End on_create() ########################################################

## only initialize / setup the development environment once: 
[[ -f /opt/edx/.install_succeeded ]] || on_create

# grab what the Vagrantfile spec'd our IP to be:
#  expecting:
#  - relevant ip on eth1;
#  - line of interest to look like:
#    inet 192.168.20.40/24 brd 192.168.20.255 scope global eth1
MY_IP=$(ip addr show dev eth1 | sed -n '/inet /{s/.*[ ]\(.*\)\/.*/\1/;p}')

cat << EOF
Connect to your virtual machine with "vagrant ssh".
Some examples you can use from your virtual machine:

- Start Learning management system (LMS):
    $ paver lms --settings=cms.dev
    =>  http://${MY_IP}:8000/

- Start Studio:
    $ paver studio --settings=dev
    => http://${MY_IP}:8001/

See the README for more.

EOF

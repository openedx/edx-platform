#!/usr/bin/env bash

# posix compliant sanity check
if [ -z $BASH ] || [  $BASH = "/bin/sh" ]; then
    echo "Please use the bash interpreter to run this script"
    exit 1
fi

error() {
      printf '\E[31m'; echo "$@"; printf '\E[0m'
}
output() {
      printf '\E[36m'; echo "$@"; printf '\E[0m'
}


### START

SELF_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REQUIREMENTS_DIR="$SELF_DIR/../requirements/system"
BREW_FILE=$REQUIREMENTS_DIR/"mac_os_x/brew-formulas.txt"
APT_REPOS_FILE=$REQUIREMENTS_DIR/"ubuntu/apt-repos.txt"
APT_PKGS_FILE=$REQUIREMENTS_DIR/"ubuntu/apt-packages.txt"

case `uname -s` in
    [Ll]inux)
        command -v lsb_release &>/dev/null || {
            error "Please install lsb-release."
            exit 1
        }

        distro=`lsb_release -cs`
        case $distro in
            #Tries to install the same 
            squeeze|wheezy|jessie|maya|lisa|olivia|nadia|natty|oneiric|precise|quantal|raring)
                output "Installing Debian family requirements"

                # add repositories
                cat $APT_REPOS_FILE | xargs -n 1 sudo add-apt-repository -y
                sudo apt-get -yq update
                sudo DEBIAN_FRONTEND=noninteractive apt-get -yq install gfortran graphviz \
                            libgraphviz-dev graphviz-dev libatlas-dev libblas-dev
                # install packages listed in APT_PKGS_FILE
                cat $APT_PKGS_FILE | xargs sudo DEBIAN_FRONTEND=noninteractive apt-get -yq install
                ;;
            *)
                error "Unsupported distribution - $distro"
                exit 1
               ;;
        esac
        ;;
    Darwin)

        if [[ ! -w /usr/local ]]; then
            cat<<EO

        You need to be able to write to /usr/local for
        the installation of brew and brew packages.

        Either make sure the group you are in (most likely 'staff')
        can write to that directory or simply execute the following
        and re-run the script:

        $ sudo chown -R $USER /usr/local
EO

            exit 1

        fi

        output "Installing OSX requirements"
#        if [[ ! -r $BREW_FILE ]]; then
#            error "$BREW_FILE does not exist, please include the brew formulas file in the requirements/system/mac_os_x directory"
#            exit 1
 #       fi

        # for some reason openssl likes to be installed by itself first
        brew install openssl

        # brew errors if the package is already installed
        for pkg in $(cat $BREW_FILE); do
            grep $pkg <(brew list) &>/dev/null || {
                output "Installing $pkg"
                brew install $pkg
            }
        done

        # paths where brew likes to install python scripts
        PATH=/usr/local/share/python:/usr/local/bin:$PATH

        command -v pip &>/dev/null || {
            output "Installing pip"
            easy_install pip
        }

        if ! grep -Eq ^1.7 <(virtualenv --version 2>/dev/null); then
            output "Installing virtualenv >1.7"
            pip install 'virtualenv>1.7' virtualenvwrapper
        fi

        command -v coffee &>/dev/null || {
            output "Installing coffee script"
            curl --insecure https://npmjs.org/install.sh | sh
            npm install -g coffee-script
        }
        ;;
    *)
        error "Unsupported platform"
        exit 1
        ;;
esac

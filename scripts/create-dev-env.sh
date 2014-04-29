#!/usr/bin/env bash

#Exit if any commands return a non-zero status
set -e

# posix compliant sanity check
if [ -z $BASH ] || [  $BASH = "/bin/sh" ]; then
    echo "Please use the bash interpreter to run this script"
    exit 1
fi

trap "ouch" ERR

ouch() {
    printf '\E[31m'

    cat<<EOL

    !! ERROR !!

    The last command did not complete successfully,
    For more details or trying running the
    script again with the -v flag.

    Output of the script is recorded in $LOG

EOL
    printf '\E[0m'

}

#Setting error color to red before reset
error() {
      printf '\E[31m'; echo "$@"; printf '\E[0m'
}

#Setting warning color to magenta before reset
warning() {
      printf '\E[35m'; echo "$@"; printf '\E[0m'
}

#Setting output color to cyan before reset
output() {
      printf '\E[36m'; echo "$@"; printf '\E[0m'
}

usage() {
    cat<<EO

    Usage: $PROG [-c] [-v] [-h]

            -y        non interactive mode (no prompt, proceed immediately)
            -c        compile scipy and numpy
            -n        do not attempt to pull edx-platform
            -s        give access to global site-packages for virtualenv
            -q        be more quiet (removes info at beginning & end)
            -v        set -x + spew
            -h        this

EO
    info
}

info() {
    cat<<EO
    edX base dir : $BASE
    Python virtualenv dir : $PYTHON_DIR
    Ruby rbenv dir : $RBENV_ROOT
    Ruby ver : $RUBY_VER

EO
}

change_git_push_defaults() {

    #Set git push defaults to upstream rather than master
    output "Changing git defaults"
    git config --global push.default upstream

}

clone_repos() {

    cd "$BASE"

    if [[ ! $nopull ]]; then
        change_git_push_defaults

        if [[ -d "$BASE/edx-platform/.git" ]]; then
            output "Pulling edx platform"
            cd "$BASE/edx-platform"
            git pull
        else
            output "Cloning edx platform"
            if [[ -d "$BASE/edx-platform" ]]; then
                output "Creating backup for existing edx platform"
                mv "$BASE/edx-platform" "${BASE}/edx-platform.bak.$$"
            fi
            git clone https://github.com/edx/edx-platform.git
        fi
    fi
}

set_base_default() {  # if PROJECT_HOME not set
    # 2 possibilities: this is from cloned repo, or not

    # See if remote's url is named edx-platform (this works for forks too, but
    # not if the name was changed).
    cd "$( dirname "${BASH_SOURCE[0]}" )"
    this_repo=$(basename $(git ls-remote --get-url 2>/dev/null) 2>/dev/null) ||
        echo -n ""

    if [[ "x$this_repo" = "xedx-platform.git" ]]; then
        # We are in the edx repo and already have git installed. Let git do the
        # work of finding base dir:
        echo "$(dirname $(git rev-parse --show-toplevel))"
    else
        echo "$HOME/edx_all"
    fi
}


### START

PROG=${0##*/}

# Adjust this to wherever you'd like to place the codebase
BASE="${PROJECT_HOME:-$(set_base_default)}"

# Use a sensible default (~/.virtualenvs) for your Python virtualenvs
# unless you've already got one set up with virtualenvwrapper.
PYTHON_DIR=${WORKON_HOME:-"$HOME/.virtualenvs"}

# Find rbenv root (~/.rbenv by default)
if [ -z "${RBENV_ROOT}" ]; then
  RBENV_ROOT="${HOME}/.rbenv"
else
  RBENV_ROOT="${RBENV_ROOT%/}"
fi
# Let the repo override the version of Ruby to install
if [[ -r $BASE/edx-platform/.ruby-version ]]; then
  RUBY_VER=`cat $BASE/edx-platform/.ruby-version`
fi

LOG="/var/tmp/install-$(date +%Y%m%d-%H%M%S).log"

# Make sure the user's not about to do anything dumb
if [[ $EUID -eq 0 ]]; then
    error "This script should not be run using sudo or as the root user"
    usage
    exit 1
fi

# If in an existing virtualenv, bail
if [[ "x$VIRTUAL_ENV" != "x" ]]; then
    envname=`basename $VIRTUAL_ENV`
    error "Looks like you're already in the \"$envname\" virtual env."
    error "Run \`deactivate\` and then re-run this script."
    usage
    exit 1
fi

# Read arguments
ARGS=$(getopt "cvhsynq" "$*")
if [[ $? != 0 ]]; then
    usage
    exit 1
fi
eval set -- "$ARGS"
while true; do
    case $1 in
        -c)
            compile=true
            shift
            ;;
        -s)
            systempkgs=true
            shift
            ;;
        -v)
            set -x
            verbose=true
            shift
            ;;
        -y)
            noninteractive=true
            shift
            ;;
        -q)
            quiet=true
            shift
            ;;
        -n)
            nopull=true
            shift
            ;;
        -h)
            usage
            exit 0
            ;;
        --)
            shift
            break
            ;;
    esac
done

if [[ ! $quiet ]]; then
    cat<<EO

  This script will setup a local edX environment, this
  includes

       * Django
       * A local copy of Python and library dependencies
       * A local copy of Ruby and library dependencies

  It will also attempt to install operating system dependencies
  with apt(debian) or brew(OSx).

  To compile scipy and numpy from source use the -c option

  !!! Do not run this script from an existing virtualenv !!!

  If you are in a ruby/python virtualenv please start a new
  shell.

EO
fi
    info

if [[ ! $noninteractive ]]; then
    output "Press return to begin or control-C to abort"
    read dummy
fi

# Log all stdout and stderr

exec > >(tee $LOG)
exec 2>&1


# Install basic system requirements

mkdir -p $BASE
case `uname -s` in
    [Ll]inux)
        command -v lsb_release &>/dev/null || {
            error "Please install lsb-release."
            exit 1
        }

        distro=`lsb_release -cs`
        case $distro in
            wheezy|jessie|maya|olivia|nadia|precise|quantal)
                if [[ ! $noninteractive ]]; then
                    warning "
                            Debian support is not fully debugged. Assuming you have standard
                            development packages already working like scipy, the
                            installation should go fine, but this is still a work in progress.

                            Please report issues you have and let us know if you are able to figure
                            out any workarounds or solutions

                            Press return to continue or control-C to abort"

                    read dummy
                fi
                sudo apt-get install -yq git ;;
            squeeze|lisa|katya|oneiric|natty|raring)
                if [[ ! $noninteractive ]]; then
                    warning "
                              It seems like you're using $distro which has been deprecated.
                              While we don't technically support this release, the install
                              script will probably still work.

                              Press return to continue or control-C to abort"
                    read dummy
                fi
                sudo apt-get install -yq git
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

        command -v brew &>/dev/null || {
            output "Installing brew"
            /usr/bin/ruby -e "$(curl -fsSL https://raw.github.com/Homebrew/homebrew/go/install)"
        }
        command -v git &>/dev/null || {
            output "Installing git"
            brew install git
        }

        ;;
    *)
        error "Unsupported platform. Try switching to either Mac or a Debian-based linux distribution (Ubuntu, Debian, or Mint)"
        exit 1
        ;;
esac


# Clone edx repositories

clone_repos

# Sanity check to make sure the repo layout hasn't changed
if [[ -d $BASE/edx-platform/scripts ]]; then
    output "Installing system-level dependencies"
    bash $BASE/edx-platform/scripts/install-system-req.sh
else
    error "It appears that our directory structure has changed and somebody failed to update this script.
            raise an issue on Github and someone should fix it."
    exit 1
fi

# Install system-level dependencies
if [[ ! -d $RBENV_ROOT ]]; then
    output "Installing rbenv"
    git clone https://github.com/sstephenson/rbenv.git $RBENV_ROOT
fi
if [[ ! -d $RBENV_ROOT/plugins/ruby-build ]]; then
    output "Installing ruby-build"
    git clone https://github.com/sstephenson/ruby-build.git $RBENV_ROOT/plugins/ruby-build
fi
shelltype=$(basename $SHELL)
if ! hash rbenv 2>/dev/null; then
    output "Adding rbenv to \$PATH in ~/.${shelltype}rc"
    echo "export PATH=\"$RBENV_ROOT/bin:\$PATH\"" >> $HOME/.${shelltype}rc
    echo 'eval "$(rbenv init -)"' >> $HOME/.${shelltype}rc
    export PATH="$RBENV_ROOT/bin:$PATH"
    eval "$(rbenv init -)"
fi

if [[ ! -d $RBENV_ROOT/versions/$RUBY_VER ]]; then
    output "Installing Ruby $RUBY_VER"
    rbenv install $RUBY_VER
    rbenv global $RUBY_VER
fi

if ! hash bundle 2>/dev/null; then
    output "Installing gem bundler"
    gem install bundler
fi
rbenv rehash

output "Installing ruby packages"
bundle install --gemfile $BASE/edx-platform/Gemfile

# Install Python virtualenv
output "Installing python virtualenv"

case `uname -s` in
    Darwin)
        # Add brew's path
        PATH=/usr/local/share/python:/usr/local/bin:$PATH
        ;;
esac

# virtualenvwrapper uses the $WORKON_HOME env var to determine where to place
# virtualenv directories. Make sure it matches the selected $PYTHON_DIR.
export WORKON_HOME=$PYTHON_DIR

# Load in the mkvirtualenv function if needed
if [[ `type -t mkvirtualenv` != "function" ]]; then
    case `uname -s` in
        Darwin)
            VEWRAPPER=`which virtualenvwrapper.sh`
        ;;

        [Ll]inux)
        if [[ -f "/etc/bash_completion.d/virtualenvwrapper" ]]; then
            VEWRAPPER=/etc/bash_completion.d/virtualenvwrapper
        else
            error "Could not find virtualenvwrapper"
            exit 1
        fi
        ;;
    esac
fi

source $VEWRAPPER
# Create edX virtualenv and link it to repo
# virtualenvwrapper automatically sources the activation script
if [[ $systempkgs ]]; then
    mkvirtualenv -q -a "$WORKON_HOME" --system-site-packages edx-platform || {
      error "mkvirtualenv exited with a non-zero error"
      return 1
    }
else
    # default behavior for virtualenv>1.7 is
    # --no-site-packages
    mkvirtualenv -q -a "$WORKON_HOME" edx-platform || {
      error "mkvirtualenv exited with a non-zero error"
      return 1
    }
fi


# compile numpy and scipy if requested

NUMPY_VER="1.6.2"
SCIPY_VER="0.10.1"

if [[ -n $compile ]]; then
    output "Downloading numpy and scipy"
    curl -sSL -o numpy.tar.gz http://downloads.sourceforge.net/project/numpy/NumPy/${NUMPY_VER}/numpy-${NUMPY_VER}.tar.gz
    curl -sSL -o scipy.tar.gz http://downloads.sourceforge.net/project/scipy/scipy/${SCIPY_VER}/scipy-${SCIPY_VER}.tar.gz
    tar xf numpy.tar.gz
    tar xf scipy.tar.gz
    rm -f numpy.tar.gz scipy.tar.gz
    output "Compiling numpy"
    cd "$BASE/numpy-${NUMPY_VER}"
    python setup.py install
    output "Compiling scipy"
    cd "$BASE/scipy-${SCIPY_VER}"
    python setup.py install
    cd "$BASE"
    rm -rf numpy-${NUMPY_VER} scipy-${SCIPY_VER}
fi

# building correct version of distribute from source
DISTRIBUTE_VER="0.6.28"
output "Building Distribute"
SITE_PACKAGES="$WORKON_HOME/edx-platform/lib/python2.7/site-packages"
cd "$SITE_PACKAGES"
curl -sSLO http://pypi.python.org/packages/source/d/distribute/distribute-${DISTRIBUTE_VER}.tar.gz
tar -xzvf distribute-${DISTRIBUTE_VER}.tar.gz
cd distribute-${DISTRIBUTE_VER}
python setup.py install
cd ..
rm distribute-${DISTRIBUTE_VER}.tar.gz

DISTRIBUTE_VERSION=`pip freeze | grep distribute`

if [[ "$DISTRIBUTE_VERSION" == "distribute==0.6.28" ]]; then
  output "Distribute successfully installed"
else
  error "Distribute failed to build correctly. This script requires a working version of Distribute 0.6.28 in your virtualenv's python installation"
  exit 1
fi

case `uname -s` in
    Darwin)
        # on mac os x get the latest distribute and pip
        pip install -U pip
        # need latest pytz before compiling numpy and scipy
        pip install -U pytz
        pip install numpy
        # scipy needs cython
        pip install cython
        # fixes problem with scipy on 10.8
        pip install -e git+https://github.com/scipy/scipy#egg=scipy-dev
        ;;
esac

output "Installing edX pre-requirements"
pip install -r $BASE/edx-platform/requirements/edx/pre.txt

output "Installing edX paver-requirements"
pip install -r $BASE/edx-platform/requirements/edx/paver.txt


output "Installing edX requirements"
# Install prereqs
cd $BASE/edx-platform
paver install_prereqs

# Final dependecy
output "Finishing Touches"
cd $BASE
pip install argcomplete
cd $BASE/edx-platform
bundle install
paver install_prereqs

mkdir -p "$BASE/log"
mkdir -p "$BASE/db"
mkdir -p "$BASE/data"

./manage.py lms syncdb --noinput --migrate
./manage.py cms syncdb --noinput --migrate

# Configure Git

output "Fixing your git default settings"
git config --global push.default current


### DONE

if [[ ! $quiet ]]; then
    cat<<END
   Success!!

   To start using Django you will need to activate the local Python
   environment. Ensure the following lines are added to your
   login script, and source your login script if needed:

        source $VEWRAPPER

   Then, every time you're ready to work on the project, just run

        $ workon edx-platform

   To start the Django on port 8000

        $ paver lms

   Or to start Django on a different <port#>

        $ ./manage.py lms runserver <port#>

  If the  Django development server starts properly you
  should see:

      Development server is running at http://127.0.0.1:<port#>/
      Quit the server with CONTROL-C.

  Connect your browser to http://127.0.0.1:<port#> to
  view the Django site.


END
fi

exit 0

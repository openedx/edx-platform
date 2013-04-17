#!/usr/bin/env bash
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
error() {
      printf '\E[31m'; echo "$@"; printf '\E[0m'
}
output() {
      printf '\E[36m'; echo "$@"; printf '\E[0m'
}
usage() {
    cat<<EO

    Usage: $PROG [-c] [-v] [-h]

            -c        compile scipy and numpy
            -s        give access to global site-packages for virtualenv
            -v        set -x + spew
            -h        this

EO
    info
}

info() {

    cat<<EO
    MITx base dir : $BASE
    Python dir : $PYTHON_DIR
    Ruby dir : $RUBY_DIR
    Ruby ver : $RUBY_VER

EO
}

clone_repos() {
    cd "$BASE"

    if [[ -d "$BASE/mitx/.git" ]]; then
        output "Pulling mitx"
        cd "$BASE/mitx"
        git pull
    else
        output "Cloning mitx"
        if [[ -d "$BASE/mitx" ]]; then
            mv "$BASE/mitx" "${BASE}/mitx.bak.$$"
        fi
        git clone git@github.com:MITx/mitx.git
    fi

    # By default, dev environments start with a copy of 6.002x
    cd "$BASE"
    mkdir -p "$BASE/data"
    REPO="content-mit-6002x"
    if [[ -d "$BASE/data/$REPO/.git" ]]; then
        output "Pulling $REPO"
        cd "$BASE/data/$REPO"
        git pull
    else
        output "Cloning $REPO"
        if [[ -d "$BASE/data/$REPO" ]]; then
            mv "$BASE/data/$REPO" "${BASE}/data/$REPO.bak.$$"
        fi
	cd "$BASE/data"
        git clone git@github.com:MITx/$REPO
    fi
}

### START

PROG=${0##*/}
BASE="$HOME/mitx_all"
PYTHON_DIR="$BASE/python"
RUBY_DIR="$BASE/ruby"
RUBY_VER="1.9.3"
LOG="/var/tmp/install-$(date +%Y%m%d-%H%M%S).log"


# Read arguments

if [[ $EUID -eq 0 ]]; then
    error "This script should not be run using sudo or as the root user"
    usage
    exit 1
fi
ARGS=$(getopt "cvhs" "$*")
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

cat<<EO

  This script will setup a local MITx environment, this
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
info
output "Press return to begin or control-C to abort"
read dummy


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
            maya|lisa|natty|oneiric|precise|quantal)
                sudo apt-get install git
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
            /usr/bin/ruby <(curl -fsSkL raw.github.com/mxcl/homebrew/go)
        }
        command -v git &>/dev/null || {
            output "Installing git"
            brew install git
        }

        ;;
    *)
        error "Unsupported platform"
        exit 1
        ;;
esac


# Clone MITx repositories

clone_repos


# Install system-level dependencies

bash $BASE/mitx/install-system-req.sh


# Install Ruby RVM

output "Installing rvm and ruby"

if ! grep -q "export rvm_path=$RUBY_DIR" ~/.rvmrc; then
    if [[ -f $HOME/.rvmrc ]]; then
        output "Copying existing .rvmrc to .rvmrc.bak"
        cp $HOME/.rvmrc $HOME/.rvmrc.bak
    fi
    output "Creating $HOME/.rvmrc so rvm uses $RUBY_DIR"
    echo "export rvm_path=$RUBY_DIR" > $HOME/.rvmrc
fi

curl -sL get.rvm.io | bash -s -- --version 1.15.7
source $RUBY_DIR/scripts/rvm
LESS="-E" rvm install $RUBY_VER --with-readline

output "Installing gem bundler"
gem install bundler

output "Installing ruby packages"
# hack :(
cd $BASE/mitx  || true
bundle install


# Install Python virtualenv

output "Installing python virtualenv"

case `uname -s` in
    Darwin)
        # Add brew's path
        PATH=/usr/local/share/python:/usr/local/bin:$PATH
        ;;
esac

if [[ $systempkgs ]]; then
    virtualenv --system-site-packages "$PYTHON_DIR"
else
    # default behavior for virtualenv>1.7 is
    # --no-site-packages
    virtualenv  "$PYTHON_DIR"
fi

# activate mitx python virtualenv
source $PYTHON_DIR/bin/activate

# compile numpy and scipy if requested

NUMPY_VER="1.6.2"
SCIPY_VER="0.10.1"

if [[ -n $compile ]]; then
    output "Downloading numpy and scipy"
    curl -sL -o numpy.tar.gz http://downloads.sourceforge.net/project/numpy/NumPy/${NUMPY_VER}/numpy-${NUMPY_VER}.tar.gz
    curl -sL -o scipy.tar.gz http://downloads.sourceforge.net/project/scipy/scipy/${SCIPY_VER}/scipy-${SCIPY_VER}.tar.gz
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

case `uname -s` in
    Darwin)
        # on mac os x get the latest distribute and pip
        curl http://python-distribute.org/distribute_setup.py | python
        pip install -U pip
        # need latest pytz before compiling numpy and scipy
        pip install -U pytz
        pip install numpy
        # fixes problem with scipy on 10.8
        pip install -e git+https://github.com/scipy/scipy#egg=scipy-dev
        ;;
esac

output "Installing MITx pre-requirements"
pip install -r $BASE/mitx/pre-requirements.txt

output "Installing MITx requirements"
# Need to be in the mitx dir to get the paths to local modules right
cd $BASE/mitx
pip install -r requirements.txt

mkdir "$BASE/log" || true
mkdir "$BASE/db" || true


# Configure Git

output "Fixing your git default settings"
git config --global push.default current


### DONE

cat<<END
   Success!!

   To start using Django you will need to activate the local Python
   and Ruby environment (at this time rvm only supports bash) :

        $ source $RUBY_DIR/scripts/rvm
        $ source $PYTHON_DIR/bin/activate

   To initialize Django

        $ cd $BASE/mitx
        $ rake django-admin[syncdb]
        $ rake django-admin[migrate]

   To start the Django on port 8000

        $ rake lms

   Or to start Django on a different <port#>

        $ rake django-admin[runserver,lms,dev,<port#>]

  If the  Django development server starts properly you
  should see:

      Development server is running at http://127.0.0.1:<port#>/
      Quit the server with CONTROL-C.

  Connect your browser to http://127.0.0.1:<port#> to
  view the Django site.


END
exit 0

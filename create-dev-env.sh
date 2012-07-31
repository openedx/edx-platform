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
            -s        do _not_ set --no-site-packages for virtualenv
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
    
    cd "$BASE"
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

PROG=${0##*/}
BASE="$HOME/mitx_all"
PYTHON_DIR="$BASE/python"
RUBY_DIR="$BASE/ruby"
RUBY_VER="1.9.3"
NUMPY_VER="1.6.2"
SCIPY_VER="0.10.1"
BREW_FILE="$BASE/mitx/brew-formulas.txt"
LOG="/var/tmp/install-$(date +%Y%m%d-%H%M%S).log"
APT_PKGS="curl git python-virtualenv build-essential python-dev gfortran liblapack-dev libfreetype6-dev libpng12-dev libxml2-dev libxslt-dev yui-compressor coffeescript"

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

EO
info
output "Press return to begin or control-C to abort"
read dummy

# log all stdout and stderr 
exec > >(tee $LOG)
exec 2>&1

if [[ -f $HOME/.rvmrc ]]; then
    output "$HOME/.rvmrc alredy exists, not adding $RUBY_DIR"
else
    output "Creating $HOME/.rmrc so rvm uses $RUBY_DIR"
    echo "export rvm_path=$RUBY_DIR" > $HOME/.rvmrc
fi
mkdir -p $BASE
case `uname -s` in
    [Ll]inux)
        command -v lsb_release &>/dev/null || {
            error "Please install lsb-release."
            exit 1
        }
        distro=`lsb_release -cs`
        case $distro in
            lisa|natty|oneiric|precise)
                output "Installing ubuntu requirements"
                sudo apt-get -y update
                sudo apt-get -y install $APT_PKGS 
                clone_repos
                ;;
            *)
                error "Unsupported distribution - $distro"
                exit 1
               ;;
        esac
        ;;
    Darwin)
        command -v brew &>/dev/null || { 
            output "Installing brew"
            /usr/bin/ruby -e "$(curl -fsSL https://raw.github.com/mxcl/homebrew/master/Library/Contributions/install_homebrew.rb)" 
        } 
        command -v git &>/dev/null || {
            output "Installing git"
            brew install git 
        }

        clone_repos

        output "Installing OSX requirements"
        if [[ ! -r $BREW_FILE ]]; then
            error "$BREW_FILE does not exist, needed to install brew deps"
            exit 1
        fi
        # brew errors if the package is already installed
        for pkg in $(cat $BREW_FILE); do
            grep $pkg <(brew list) &>/dev/null || {
                output "Installing $pkg"
                brew install $pkg  
            }
        done
        command -v pip &>/dev/null || {
            output "Installing pip"
            sudo easy_install pip  
        }
        command -v virtualenv &>/dev/null || {
            output "Installing virtualenv"
            sudo pip install virtualenv virtualenvwrapper 
        }
        command -v coffee &>/dev/null || {
            output "Installing coffee script"
            curl http://npmjs.org/install.sh | sh
            npm install -g coffee-script
        }
        ;;
    *)
        error "Unsupported platform"
        exit 1
        ;;
esac

output "Installing rvm and ruby"
curl -sL get.rvm.io | bash -s stable
source $RUBY_DIR/scripts/rvm
# skip the intro 
LESS="-E" rvm install $RUBY_VER
if [[ -n $systempkgs ]]; then
    virtualenv "$PYTHON_DIR"
else
    virtualenv --no-site-packages "$PYTHON_DIR"
fi
source $PYTHON_DIR/bin/activate
output "Installing gem bundler"
gem install bundler
output "Installing ruby packages"
# hack :(
cd $BASE/mitx  || true
bundle install

cd $BASE

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

output "Installing MITx pre-requirements"
pip install -r mitx/pre-requirements.txt 
# Need to be in the mitx dir to get the paths to local modules right
output "Installing MITx requirements"
cd mitx
pip install -r requirements.txt 

mkdir "$BASE/log" || true
mkdir "$BASE/db" || true

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

  If the Django development server starts properly you 
  should see:

      Development server is running at http://127.0.0.1:<port#>/
      Quit the server with CONTROL-C.

  Connect your browser to http://127.0.0.1:<port#> to 
  view the Django site.


END
exit 0


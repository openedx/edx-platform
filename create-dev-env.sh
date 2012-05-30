#!/bin/bash
set -e

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



PROG=${0##*/}
BASE="$HOME/mitx_all"
PYTHON_DIR="$BASE/python"
RUBY_DIR="$BASE/ruby"
RUBY_VER="1.9.3"
NUMPY_VER="1.6.2"
SCIPY_VER="0.10.1"
LOG="/var/tmp/install.log"
BREW_PKGS="readline sqlite gdbm pkg-config gfortran mercurial python yuicompressor node"
APT_PKGS="curl git mercurial python-virtualenv build-essential python-dev gfortran liblapack-dev libfreetype6-dev libpng12-dev libxml2-dev libxslt-dev yui-compressor coffeescript"

if [[ $EUID -eq 0 ]]; then
    error "This script should not be run using sudo or as the root user"
    usage
    exit 1
fi

ARGS=$(getopt "cvh" "$*")
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

if [[ -f $HOME/.rvmrc ]]; then
    output "$HOME/.rvmrc alredy exists, not adding $RUBY_DIR"
else
    output "Creating $HOME/.rmrc so rvm uses $RUBY_DIR"
    echo "export rvm_path=$RUBY_DIR" > $HOME/.rvmrc
fi
mkdir -p $BASE
rm -f $LOG
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
            /usr/bin/ruby -e "$(curl -fsSL https://raw.github.com/mxcl/homebrew/master/Library/Contributions/install_homebrew.rb)" >>$LOG 
        } 
        output "Installing OSX requirements"
        # brew errors if the package is already installed
        for pkg in $BREW_PKGS; do
            grep $pkg <(brew list) &>/dev/null || {
                output "Installing $pkg"
                brew install $pkg  >>$LOG 
            }
        done
        command -v pip &>/dev/null || {
            output "Installing pip"
            sudo easy_install pip  >>$LOG 
        }
        command -v virtualenv &>/dev/null || {
            output "Installing virtualenv"
            sudo pip install virtualenv virtualenvwrapper >> $LOG
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
rvm install $RUBY_VER
virtualenv "$PYTHON_DIR"
source $PYTHON_DIR/bin/activate
output "Installing ruby packages"
gem install --version '0.8.3' rake
gem install --version '3.1.15' sass
gem install --version '1.3.6' bourbon
cd "$BASE"
output "Cloning mitx, askbot and data repos"
if [[ -d "$BASE/mitx" ]]; then
    mv "$BASE/mitx" "${BASE}/mitx.bak.$$"
fi
git clone git@github.com:MITx/mitx.git >>$LOG 
if [[ -d "$BASE/askbot-devel" ]]; then
    mv "$BASE/askbot-devel" "${BASE}/askbot-devel.bak.$$"
fi
git clone git@github.com:MITx/askbot-devel >>$LOG 
if [[ -d "$BASE/data" ]]; then
    mv "$BASE/data" "${BASE}/data.bak.$$"
fi
hg clone ssh://hg-content@gp.mitx.mit.edu/data >>$LOG 

if [[ -n $compile ]]; then
    output "Downloading numpy and scipy"
    curl -sL -o numpy.tar.gz http://downloads.sourceforge.net/project/numpy/NumPy/${NUMPY_VER}/numpy-${NUMPY_VER}.tar.gz
    curl -sL -o scipy.tar.gz http://downloads.sourceforge.net/project/scipy/scipy/${SCIPY_VER}/scipy-${SCIPY_VER}.tar.gz
    tar xf numpy.tar.gz
    tar xf scipy.tar.gz
    rm -f numpy.tar.gz scipy.tar.gz
    output "Compiling numpy"
    cd "$BASE/numpy-${NUMPY_VER}"
    python setup.py install >>$LOG  2>&1
    output "Compiling scipy"
    cd "$BASE/scipy-${SCIPY_VER}"
    python setup.py install >>$LOG  2>&1
    cd "$BASE"
    rm -rf numpy-${NUMPY_VER} scipy-${SCIPY_VER}
fi

output "Installing askbot requirements"
pip install -r askbot-devel/askbot_requirements.txt >>$LOG 
pip install -r askbot-devel/askbot_requirements_dev.txt >>$LOG 
output "Installing MITx requirements"
pip install -r mitx/pre-requirements.txt >> $LOG
pip install -r mitx/requirements.txt >>$LOG 

mkdir "$BASE/log" || true
mkdir "$BASE/db" || true

cat<<END
   
   Success!!

   To start using Django you will need
   to activate the local Python and Ruby
   environment:

        $ source $RUBY_DIR/scripts/rvm
        $ source $PYTHON_DIR/bin/activate
  
   To initialize and start a local instance of Django:
        
        $ cd $BASE/mitx
        $ django-admin.py syncdb --settings=envs.dev --pythonpath=.
        $ django-admin.py migrate --settings=envs.dev --pythonpath=.
        $ django-admin.py runserver --settings=envs.dev --pythonpath=.   
       
END
exit 0


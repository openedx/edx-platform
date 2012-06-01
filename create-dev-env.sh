#!/bin/bash
set -e
trap "ouch" ERR

ouch() {
    printf '\E[31m'

    cat<<EOL
    
    !! ERROR !!

    The last command did not complete successfully, 
    see $LOG for more details or trying running the
    script again with the -v flag.  

EOL

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
    output "Cloning mitx"
    if [[ -d "$BASE/mitx" ]]; then
        mv "$BASE/mitx" "${BASE}/mitx.bak.$$"
    fi
    git clone git@github.com:MITx/mitx.git >>$LOG 
    output "Cloning askbot-devel"
    if [[ -d "$BASE/askbot-devel" ]]; then
        mv "$BASE/askbot-devel" "${BASE}/askbot-devel.bak.$$"
    fi
    git clone git@github.com:MITx/askbot-devel >>$LOG 
    output "Cloning data"
    if [[ -d "$BASE/data" ]]; then
        mv "$BASE/data" "${BASE}/data.bak.$$"
    fi
    hg clone ssh://hg-content@gp.mitx.mit.edu/data >>$LOG 
}

PROG=${0##*/}
BASE="$HOME/mitx_all"
PYTHON_DIR="$BASE/python"
RUBY_DIR="$BASE/ruby"
RUBY_VER="1.9.3"
NUMPY_VER="1.6.2"
SCIPY_VER="0.10.1"
BREW_FILE="$BASE/mitx/brew-formulas.txt"
LOG="/var/tmp/install.log"
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

  STDOUT is redirected to /var/tmp/install.log, run
  $ tail -f /var/tmp/install.log
  to monitor progress

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
            brew install git >> $LOG
        }
        command -v hg &>/dev/null || {
            output "Installaing mercurial"
            brew install mercurial >> $LOG
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
rvm install $RUBY_VER
virtualenv "$PYTHON_DIR"
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


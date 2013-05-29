#!/usr/bin/env bash

BASE=$HOME/edx_all
PLATFORM_REPO=$BASE/edx-platform
PYTHON_BIN=/usr/local/bin/python
PYTHON_SHARE=/usr/local/share/python

#Add python directory to $PATH for this session
$PATH=$PYTHON_SHARE:$PATH

# Create a directory to store everything
echo "Creating $BASE directory"
mkdir -p $BASE

# Install HomeBrew
echo "Installing HomeBrew"
ruby -e "$(curl -fsSL https://raw.github.com/mxcl/homebrew/go)"

#Install git
echo "Installing Git Version Control"
brew install git

# Clone the edx-platform repository
echo "Cloning edx-platform repo"
cd $BASE
git clone https://github.com/edx/edx-platform.git

# Install system prereqs
echo "Installing Mac OS X prereqs"
BREW_FILE=$PLATFORM_REPO/requirements/system/mac_os_x/brew-formulas.txt
for pkg in $(cat $BREW_FILE); do
    grep $pkg <(brew list) &>/dev/null || {
        echo "Installing $pkg"
        brew install $pkg
    }
done

# Manually Installing Ruby prereqs
brew install openssl

# Install Ruby virtual environment
curl -L https://get.rvm.io | bash stable --ruby
source $HOME/.rvm/scripts/rvm
rvm install ruby-1.9.3-p374
rvm use 1.9.3-p374
rvm rubygems latest

gem install bundler
bundle install --gemfile $PLATFORM_REPO/Gemfile

# Install Python virtual environment
echo "Installing Python virtualenv"
sudo pip install virtualenvwrapper
export VIRTUALENVWRAPPER_PYTHON=$PYTHON_BIN
export VIRTUALENV_DISTRIBUTE=true
source $PYTHON_SHARE/virtualenvwrapper.sh
mkvirtualenv -a edx-platform --system-site-packages edx-platform

# Install numpy and scipy
NUMPY_VER="1.6.2"
SCIPY_VER="0.10.1"

echo "Downloading numpy and scipy"
curl -sL -o numpy.tar.gz http://downloads.sourceforge.net/project/numpy/NumPy/${NUMPY_VER}/numpy-${NUMPY_VER}.tar.gz
curl -sL -o scipy.tar.gz http://downloads.sourceforge.net/project/scipy/scipy/${SCIPY_VER}/scipy-${SCIPY_VER}.tar.gz
tar xf numpy.tar.gz
tar xf scipy.tar.gz
rm -f numpy.tar.gz scipy.tar.gz
echo "Compiling numpy"
cd "$BASE/numpy-${NUMPY_VER}"
python setup.py install
echo "Compiling scipy"
cd "$BASE/scipy-${SCIPY_VER}"
python setup.py install
cd "$BASE"
rm -rf numpy-${NUMPY_VER} scipy-${SCIPY_VER}

# building correct version of distribute from source
echo "Building Distribute"
SITE_PACKAGES=$HOME/.virtualenvs/edx-platform/lib/python2.7/site-packages
cd $SITE_PACKAGES
curl -O http://pypi.python.org/packages/source/d/distribute/distribute-0.6.28.tar.gz
tar -xzvf distribute-0.6.28.tar.gz
cd distribute-0.6.28
python setup.py install
cd ..
rm distribute-0.6.28.tar.gz
rm -rf distribute-0.6.28-py*

# on mac os x get the latest pip
pip install -U pip
# need latest pytz before compiling numpy and scipy
pip install -U pytz
pip install -U numpy
# scipy needs cython
pip install cython
# fixes problem with scipy on 10.8
pip install -e git+https://github.com/scipy/scipy#egg=scipy-dev


# Install prereqs
echo "Installing prereqs"
cd $PLATFORM_REPO
rvm use 1.9.3-p374
rake install_prereqs

# Activate the new Virtualenv for pip fixes
VIRTUALENV=$HOME/.virtualenvs/edx-platform/bin
cd $VIRTUALENV
source activate

# Final dependecy
echo "Finishing Touches"
cd $BASE
pip install argcomplete
cd $PLATFORM_REPO
bundle install

# Make required directories
cd $BASE
mkdir data log db

# Finished
echo "Success!"
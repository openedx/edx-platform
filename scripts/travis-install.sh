rm -rf ~/.nvm && git clone https://github.com/creationix/nvm.git ~/.nvm && (cd ~/.nvm && git checkout `git describe --abbrev=0 --tags`) && source ~/.nvm/nvm.sh && nvm install 6.9.4
npm install

pip install setuptools
pip install --exists-action w -r requirements/edx/paver.txt

# Mirror what paver install_prereqs does.
# After a successful build, Travis will
# cache the virtualenv at that state, so that
# the next build will not need to install them
# from scratch again.
pip install --exists-action w -r requirements/edx/pre.txt
pip install --exists-action w -r requirements/edx/github.txt
pip install --exists-action w -r requirements/edx/local.txt

# HACK: within base.txt stevedore had a
# dependency on a version range of pbr.
# Install a version which falls within that range.
pip install --exists-action w pbr==0.9.0
pip install --exists-action w -r requirements/edx/base.txt
sudo apt-get update
sudo apt-get install libxmlsec1-dev
sudo apt-get install swig
if [ -e requirements/edx/post.txt ]; then pip install --exists-action w -r requirements/edx/post.txt ; fi

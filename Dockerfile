# docker build . -t edxops/edxapp:devstack-slim
FROM clintonb/edx-base:python-2.7-slim
ENV DJANGO_SETTINGS_MODULE devstack_docker
ENV NO_PYTHON_UNINSTALL 1
ENV PIP_USE_WHEEL 1
ENV PIP_FIND_LINKS /wheelhouse

# Inform edxapp where to read configuration
ENV CONFIG_ROOT /config

WORKDIR /code

# Install OS libs
RUN apt-get update && \
    apt-get install -y \
        apparmor-utils \
        gfortran \
        graphviz \
        graphviz-dev \
        # Iceweasel is the Debian name for Firefox
        iceweasel \
        ipython \
        libfreetype6-dev \
        libgeos-dev \
        liblapack-dev \
        libpng12-dev \
        libxml2-dev \
        libxmlsec1-dev \
        libxslt1-dev \
        pkg-config \
        ntp \
        s3cmd \
        swig \
        xvfb

COPY package.json /code/
COPY requirements/ /code/requirements/
COPY .docker/wheelhouse/ /wheelhouse/
COPY .docker/node_modules/ /code/node_modules/

RUN npm install
RUN pip install -r requirements/edx/pre.txt
RUN pip install -r requirements/edx/base.txt
RUN pip install -r requirements/edx/paver.txt
RUN pip install -r requirements/edx/post.txt
RUN pip install -r requirements/edx/github.txt

ADD . /code/

# We wait to install local requirments because they rely on the codebase
RUN pip install -r requirements/edx/local.txt

# We delay adding the configuration for as long as possible so changes here won't bust
# the Docker cache. This configuration is only needed for Django management commands, which
# we run to update assets.
COPY .docker/config /config/

RUN NO_PREREQ_INSTALL=1 paver update_assets --settings devstack_docker

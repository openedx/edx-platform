FROM ubuntu:focal as base

# Warning: This file is experimental.
#
# Short-term goals:
# * Be a suitable replacement for the `edxops/edxapp` image in devstack (in progress).
# * Take advantage of Docker caching layers: aim to put commands in order of
#   increasing cache-busting frequency.
# * Related to ^, use no Ansible or Paver.
# Long-term goal:
# * Be a suitable base for production LMS and CMS images (THIS IS NOT YET THE CASE!).
#
# Install system requirements.
# We update, upgrade, and delete lists all in one layer
# in order to reduce total image size.
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install --yes \
        # Global requirements
        build-essential \
        curl \
        # If we don't need gcc, we should remove it.
        g++ \
        gcc \
        git \
        git-core \
        language-pack-en \
        libfreetype6-dev \
        libmysqlclient-dev \
        libssl-dev \
        libxml2-dev \
        libxmlsec1-dev \
        libxslt1-dev \
        swig \
        # openedx requirements
        gettext \
        gfortran \
        graphviz \
        libffi-dev \
        libfreetype6-dev \
        libgeos-dev \
        libgraphviz-dev \
        libjpeg8-dev \
        liblapack-dev \
        libpng-dev \
        libsqlite3-dev \
        libxml2-dev \
        libxmlsec1-dev \
        libxslt1-dev \
        # lynx: Required by https://github.com/openedx/edx-platform/blob/b489a4ecb122/openedx/core/lib/html_to_text.py#L16
        lynx \
        ntp \
        pkg-config \
        python3-dev \
        python3-venv && \
    rm -rf /var/lib/apt/lists/*

# Set locale.
RUN locale-gen en_US.UTF-8

# Env vars: locale
ENV LANG='en_US.UTF-8'
ENV LANGUAGE='en_US:en'
ENV LC_ALL='en_US.UTF-8'

# Env vars: configuration
ENV CONFIG_ROOT='/edx/etc'
ENV LMS_CFG="$CONFIG_ROOT/lms.yml"
ENV CMS_CFG="$CONFIG_ROOT/cms.yml"
ENV EDX_PLATFORM_SETTINGS='production'

# Env vars: path
ENV VIRTUAL_ENV='/edx/app/edxapp/venvs/edxapp'
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PATH="/edx/app/edxapp/edx-platform/node_modules/.bin:${PATH}"
ENV PATH="/edx/app/edxapp/edx-platform/bin:${PATH}"
ENV PATH="/edx/app/edxapp/nodeenv/bin:${PATH}"

# Create config directory. Create, define, and switch to working directory.
RUN mkdir -p "$CONFIG_ROOT"
WORKDIR /edx/app/edxapp/edx-platform

# Env vars: paver
# We intentionally don't use paver in this Dockerfile, but Devstack may invoke paver commands
# during provisioning. Enabling NO_PREREQ_INSTALL tells paver not to re-install Python
# requirements for every paver command, potentially saving a lot of developer time.
ENV NO_PREREQ_INSTALL='1'

# Set up a Python virtual environment.
# It is already 'activated' because $VIRTUAL_ENV/bin was put on $PATH.
RUN python3.8 -m venv "$VIRTUAL_ENV"

# Install Python requirements.
# Requires copying over requirements files, but not entire repository.
COPY requirements requirements
RUN pip install -r requirements/pip.txt
RUN pip install -r requirements/edx/base.txt

# Set up a Node environment and install Node requirements.
# Must be done after Python requirements, since nodeenv is installed
# via pip.
# The node environment is already 'activated' because its .../bin was put on $PATH.
RUN nodeenv /edx/app/edxapp/nodeenv --node=16.14.0 --prebuilt
RUN npm install -g npm@8.5.x
COPY package.json package.json
COPY package-lock.json package-lock.json
RUN npm set progress=false && npm install

# Copy over remaining parts of repository (including all code).
COPY . .

# Install Python requirements again in order to capture local projects
RUN pip install -e .

##################################################
# Define LMS docker-based non-dev target.
FROM base as lms-docker
ENV SERVICE_VARIANT lms
ARG LMS_CFG_OVERRIDE
RUN echo "$LMS_CFG_OVERRIDE"
ENV LMS_CFG="${LMS_CFG_OVERRIDE:-$LMS_CFG}"
RUN echo "$LMS_CFG"
ENV EDX_PLATFORM_SETTINGS='docker-production'
ENV DJANGO_SETTINGS_MODULE="lms.envs.$EDX_PLATFORM_SETTINGS"
EXPOSE 8000
CMD gunicorn \
    -c /edx/app/edxapp/edx-platform/lms/docker_lms_gunicorn.py \
    --name lms \
    --bind=0.0.0.0:8000 \
    --max-requests=1000 \
    --access-logfile \
    - lms.wsgi:application

##################################################
# Define LMS non-dev target.
FROM base as lms
ENV LMS_CFG="$CONFIG_ROOT/lms.yml"
ENV SERVICE_VARIANT lms
ENV DJANGO_SETTINGS_MODULE="lms.envs.$EDX_PLATFORM_SETTINGS"
EXPOSE 8000
CMD gunicorn \
    -c /edx/app/edxapp/edx-platform/lms/docker_lms_gunicorn.py \
    --name lms \
    --bind=0.0.0.0:8000 \
    --max-requests=1000 \
    --access-logfile \
    - lms.wsgi:application


##################################################
# Define CMS non-dev target.
FROM base as cms
ENV SERVICE_VARIANT cms
ENV EDX_PLATFORM_SETTINGS='production'
ENV DJANGO_SETTINGS_MODULE="cms.envs.$EDX_PLATFORM_SETTINGS"
EXPOSE 8010
CMD gunicorn \
    -c /edx/app/edxapp/edx-platform/cms/docker_cms_gunicorn.py \
    --name cms \
    --bind=0.0.0.0:8010 \
    --max-requests=1000 \
    --access-logfile \
    - cms.wsgi:application


##################################################
# Define intermediate dev target for LMS/CMS.
#
# Although it might seem more logical to forego the `dev` stage
# and instead base `lms-dev` and `cms-dev` off of `lms` and
# `cms`, respectively, we choose to have this `dev` stage
# so that the installed development requirements are contained
# in a single layer, shared between `lms-dev` and `cms-dev`.
FROM base as dev
RUN pip install -r requirements/edx/development.txt

# Link configuration YAMLs and set EDX_PLATFORM_SE1TTINGS.
ENV EDX_PLATFORM_SETTINGS='devstack_docker'
RUN ln -s "$(pwd)/lms/envs/devstack-experimental.yml" "$LMS_CFG"
RUN ln -s "$(pwd)/cms/envs/devstack-experimental.yml" "$CMS_CFG"

# Temporary compatibility hack while devstack is supporting
# both the old `edxops/edxapp` image and this image:
# Add in a dummy ../edxapp_env file.
# The edxapp_env file was originally needed for sourcing to get
# environment variables like LMS_CFG, but now we just set
# those variables right in the Dockerfile.
RUN touch ../edxapp_env


##################################################
#  Define LMS dev target.
FROM dev as lms-dev
ENV SERVICE_VARIANT lms
ENV DJANGO_SETTINGS_MODULE="lms.envs.$EDX_PLATFORM_SETTINGS"
EXPOSE 18000
CMD while true; do python ./manage.py lms runserver 0.0.0.0:18000; sleep 2; done


##################################################
#  Define CMS dev target.
FROM dev as cms-dev
ENV SERVICE_VARIANT cms
ENV DJANGO_SETTINGS_MODULE="cms.envs.$EDX_PLATFORM_SETTINGS"
EXPOSE 18010
CMD while true; do python ./manage.py cms runserver 0.0.0.0:18010; sleep 2; done

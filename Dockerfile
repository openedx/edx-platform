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
ARG APT_MANDATORY_REQUIREMENTS="python3 python3.8 python3.8-minimal libpython3.8 libpython3.8-stdlib python3-venv lynx ntp gettext gfortran graphviz locales swig"
ARG APT_BUILD_REQUIREMENTS="build-essential curl git git-core pkg-config libfreetype6-dev libmysqlclient-dev libssl-dev libxml2-dev libxmlsec1-dev libxslt1-dev python3-dev \
                            libffi-dev libfreetype6-dev libgeos-dev libgraphviz-dev libjpeg8-dev liblapack-dev libpng-dev libsqlite3-dev libxml2-dev libxmlsec1-dev libxslt1-dev"

ARG DEBIAN_FRONTEND=noninteractive

# Env vars: paver
# We intentionally don't use paver in this Dockerfile, but Devstack may invoke paver commands
# during provisioning. Enabling NO_PREREQ_INSTALL tells paver not to re-install Python
# requirements for every paver command, potentially saving a lot of developer time.
ARG NO_PREREQ_INSTALL='1'

# Env vars: locale
ENV LANG='en_US.UTF-8'
ENV LANGUAGE='en_US:en'
ENV LC_ALL='en_US.UTF-8'

# Env vars: configuration
ENV EDX_PLATFORM_SETTINGS='production'

# Env vars: path
ENV VIRTUAL_ENV="/edx/app/edxapp/venvs/edxapp"
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"
ENV PATH="/edx/app/edxapp/edx-platform/node_modules/.bin:${PATH}"
ENV PATH="/edx/app/edxapp/edx-platform/bin:${PATH}"
ENV PATH="/edx/app/edxapp/nodeenv/bin:${PATH}"

WORKDIR /edx/app/edxapp/edx-platform

COPY . .

RUN set -eux; \
    apt-get update; \
    apt-get -y dist-upgrade; \
    echo "locales locales/default_environment_locale select en_US.UTF-8" | debconf-set-selections; \
    echo "locales locales/locales_to_be_generated multiselect en_US.UTF-8 UTF-8" | debconf-set-selections; \
    apt-get --yes install --no-install-recommends ${APT_MANDATORY_REQUIREMENTS}; \
    savedAptMark="$(apt-mark showmanual)"; \
    apt-mark auto '.*' > /dev/null; \
    apt-mark manual $savedAptMark > /dev/null; \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false; \
    savedAptMark="$(apt-mark showmanual)"; \
    apt-get --yes install --no-install-recommends ${APT_BUILD_REQUIREMENTS}; \
    # Set up a Python virtual environment.
    # It is already 'activated' because $VIRTUAL_ENV/bin was put on $PATH.
    python3.8 -m venv "${VIRTUAL_ENV}"; \
    pip install -r requirements/pip.txt; \
    pip install -r requirements/edx/base.txt; \
    # Set up a Node environment and install Node requirements.
    # Must be done after Python requirements, since nodeenv is installed
    # via pip.
    # The node environment is already 'activated' because its .../bin was put on $PATH.
    nodeenv /edx/app/edxapp/nodeenv --node=16.14.0 --prebuilt; \
    npm install -g npm@8.5.x; \
    npm set progress=false && npm install; \
    # Install Python requirements again in order to capture local projects
    pip install -e .; \
    pip cache purge; \
    apt-get --yes remove --purge ${APT_BUILD_REQUIREMENTS}; \
    apt-get --yes autoremove; \
    rm -rf /var/lib/apt/*

RUN useradd -m --shell /bin/false app

USER app

# ##################################################
# # Define LMS docker-based non-dev target.
# FROM base as lms-docker
# ENV SERVICE_VARIANT lms
# ARG LMS_CFG_OVERRIDE
# RUN echo "$LMS_CFG_OVERRIDE"
# ENV LMS_CFG="${LMS_CFG_OVERRIDE:-$LMS_CFG}"
# RUN echo "$LMS_CFG"
# ENV EDX_PLATFORM_SETTINGS='docker-production'
# ENV DJANGO_SETTINGS_MODULE="lms.envs.$EDX_PLATFORM_SETTINGS"
# EXPOSE 8000
# CMD gunicorn \
#     -c /edx/app/edxapp/edx-platform/lms/docker_lms_gunicorn.py \
#     --name lms \
#     --bind=0.0.0.0:8000 \
#     --max-requests=1000 \
#     --access-logfile \
#     - lms.wsgi:application

# ##################################################
# # Define LMS non-dev target.
# FROM base as lms
# ENV LMS_CFG="$CONFIG_ROOT/lms.yml"
# ENV SERVICE_VARIANT lms
# ENV DJANGO_SETTINGS_MODULE="lms.envs.$EDX_PLATFORM_SETTINGS"
# EXPOSE 8000
# CMD gunicorn \
#     -c /edx/app/edxapp/edx-platform/lms/docker_lms_gunicorn.py \
#     --name lms \
#     --bind=0.0.0.0:8000 \
#     --max-requests=1000 \
#     --access-logfile \
#     - lms.wsgi:application


# ##################################################
# # Define CMS non-dev target.
# FROM base as cms
# ENV SERVICE_VARIANT cms
# ENV EDX_PLATFORM_SETTINGS='production'
# ENV DJANGO_SETTINGS_MODULE="cms.envs.$EDX_PLATFORM_SETTINGS"
# EXPOSE 8010
# CMD gunicorn \
#     -c /edx/app/edxapp/edx-platform/cms/docker_cms_gunicorn.py \
#     --name cms \
#     --bind=0.0.0.0:8010 \
#     --max-requests=1000 \
#     --access-logfile \
#     - cms.wsgi:application


# ##################################################
# # Define intermediate dev target for LMS/CMS.
# #
# # Although it might seem more logical to forego the `dev` stage
# # and instead base `lms-dev` and `cms-dev` off of `lms` and
# # `cms`, respectively, we choose to have this `dev` stage
# # so that the installed development requirements are contained
# # in a single layer, shared between `lms-dev` and `cms-dev`.
# FROM base as dev
# RUN pip install -r requirements/edx/development.txt

# # Link configuration YAMLs and set EDX_PLATFORM_SE1TTINGS.
# ENV EDX_PLATFORM_SETTINGS='devstack_docker'
# RUN ln -s "$(pwd)/lms/envs/devstack-experimental.yml" "$LMS_CFG"
# RUN ln -s "$(pwd)/cms/envs/devstack-experimental.yml" "$CMS_CFG"

# # Temporary compatibility hack while devstack is supporting
# # both the old `edxops/edxapp` image and this image:
# # Add in a dummy ../edxapp_env file.
# # The edxapp_env file was originally needed for sourcing to get
# # environment variables like LMS_CFG, but now we just set
# # those variables right in the Dockerfile.
# RUN touch ../edxapp_env


# ##################################################
# #  Define LMS dev target.
# FROM dev as lms-dev
# ENV SERVICE_VARIANT lms
# ENV DJANGO_SETTINGS_MODULE="lms.envs.$EDX_PLATFORM_SETTINGS"
# EXPOSE 18000
# CMD while true; do python ./manage.py lms runserver 0.0.0.0:18000; sleep 2; done


# ##################################################
# #  Define CMS dev target.
# FROM dev as cms-dev
# ENV SERVICE_VARIANT cms
# ENV DJANGO_SETTINGS_MODULE="cms.envs.$EDX_PLATFORM_SETTINGS"
# EXPOSE 18010
# CMD while true; do python ./manage.py cms runserver 0.0.0.0:18010; sleep 2; done

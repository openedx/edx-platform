FROM ubuntu:16.04

############ common to lms & cms

# Install system requirements
RUN apt update && \
    # Global requirements
    apt install -y language-pack-en git python-virtualenv build-essential software-properties-common curl git-core libxml2-dev libxslt1-dev python-pip libmysqlclient-dev python-apt python-dev libxmlsec1-dev libfreetype6-dev swig gcc g++ \
    # openedx requirements
    gettext gfortran graphviz graphviz-dev libffi-dev libfreetype6-dev libgeos-dev libjpeg8-dev liblapack-dev libpng12-dev libsqlite3-dev libxml2-dev libxmlsec1-dev libxslt1-dev nodejs npm ntp pkg-config lynx \
    # Our requirements
    mysql-client locales unzip \
    && rm -rf /var/lib/apt/lists/*

# Setup system locales, this is used to fix accent in code
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Dockerize will be useful to wait for mysql DB availability
ARG DOCKERIZE_VERSION=v0.6.1
RUN curl -L -o /tmp/dockerize.tar.gz https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf /tmp/dockerize.tar.gz \
    && rm /tmp/dockerize.tar.gz

## Checkout edx-platform code
ADD . /openedx/edx-platform
WORKDIR /openedx/edx-platform

# Install python requirements (clone source repos in a separate dir, otherwise
# they will be overwritten when we mount edx-platform)
ENV NO_PYTHON_UNINSTALL 1
RUN pip install --src ../venv/src -r requirements/edx/base.txt

# Remove the original versions of ora2 and edx-sga
RUN pip uninstall -y ora2 edx-sga

# Manually update pytz (Timezones)
RUN pip install pytz --upgrade

# Install a recent version of nodejs
RUN nodeenv /openedx/nodeenv --node=8.9.3 --prebuilt
ENV PATH /openedx/nodeenv/bin:${PATH}

# Install nodejs requirements
RUN npm set progress=false \
    && npm install
ENV PATH ./node_modules/.bin:${PATH}

# Copy scripts
COPY .github/build/bin /openedx/bin
ENV PATH /openedx/bin:${PATH}

# Create folder that will store *.env.json and *.auth.json files, as well as
# the settings files.
COPY .github/build/settings/lms/*.py ./lms/envs/prod/
COPY .github/build/settings/cms/*.py ./cms/envs/prod/
RUN mkdir -p /openedx/config ./lms/envs/prod ./cms/envs/prod
ENV CONFIG_ROOT /openedx/config

# Collect production assets. By default, only assets from the default theme
# will be processed. This makes the docker image lighter and faster to build.
# Only the custom themes added to /openedx/themes will be compiled.
# Here, we don't run "paver update_assets" which is slow, compiles all themes
# and requires a complex settings file. Instead, we decompose the commands
# and run each one individually to collect the production static assets to
# /openedx/staticfiles.
RUN openedx-assets xmodule \
    && openedx-assets npm \
    && openedx-assets webpack --env=prod \
    && openedx-assets common

# service variant is "lms" or "cms"
ENV SERVICE_VARIANT lms
ENV SETTINGS prod.production

# Entrypoint will fix permissions of all files and run commands as openedx
ENTRYPOINT ["docker-entrypoint.sh"]

# Run server
EXPOSE 8000
CMD gunicorn --name ${SERVICE_VARIANT} --workers ${WORKER_COUNT:-1} --bind=0.0.0.0:8000 --max-requests=${MAX_REQUESTS:-1000} --preload ${SERVICE_VARIANT}.wsgi:application

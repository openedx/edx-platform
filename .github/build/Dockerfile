FROM ubuntu:16.04 as base

############ common to lms & cms
ARG EDX_PLATFORM_VERSION=undefined

# Install system requirements
RUN apt update \
    # Global requirements
    && apt install -yq language-pack-en git build-essential software-properties-common curl git-core libxml2-dev libxslt1-dev libmysqlclient-dev libxmlsec1-dev libfreetype6-dev libssl-dev swig gcc g++ \
    # openedx requirements
    gettext gfortran graphviz libgraphviz-dev libffi-dev libfreetype6-dev libgeos-dev libjpeg8-dev liblapack-dev libpng-dev libsqlite3-dev libxml2-dev libxmlsec1-dev libxslt1-dev ntp pkg-config python3.5 python3-dev python3-pip lynx \
    # Our requirements
    mysql-client locales unzip \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/pip3 /usr/bin/pip \
    && ln -s /usr/bin/python3 /usr/bin/python

# Setup system locales, this is used to fix accent in code
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
# https://github.com/pypa/setuptools/issues/2352 , https://setuptools.readthedocs.io/en/latest/history.html#v50-0-0
ENV SETUPTOOLS_USE_DISTUTILS stdlib

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
# Also update boto from 2.39.0 to 2.40.0 as it has an exception on python3
# Finally, install a compatibility layer for s3 (VIDEO_TRANSCRIPTS_SETTINGS save has an ASCII error on data)
ENV NO_PYTHON_UNINSTALL 1
RUN pip install pip==20.0.2 \
  && pip install --src ../venv/src -r requirements/edx/base.txt \
  && pip install boto==2.40.0 \
  && pip install -e git+https://github.com/eol-uchile/edx-s3-compatibility@ad317969c073f8348da719cdda7b430bcfafb706#egg=edx_s3_compatiblity

# Remove the original versions of ora2 and edx-sga
RUN pip uninstall -y ora2 edx-sga

# Manually update pytz (Timezones)
RUN pip install pytz --upgrade

# Install a recent version of nodejs
RUN nodeenv /openedx/nodeenv --node=12.13.0 --prebuilt
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
RUN mkdir -p /openedx/config ./lms/envs/prod ./cms/envs/prod \
  && echo "EDX_PLATFORM_REVISION: ${EDX_PLATFORM_VERSION}" > /openedx/config/revision.yml

ENV CONFIG_ROOT /openedx/config
ENV LMS_CFG /openedx/config/lms.yml
ENV STUDIO_CFG /openedx/config/cms.yml
ENV REVISION_CFG /openedx/config/revision.yml

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
CMD gunicorn --name ${SERVICE_VARIANT} --workers ${WORKER_COUNT:-1} --max-requests-jitter=50 --bind=0.0.0.0:8000 --max-requests=${MAX_REQUESTS:-1000} --preload ${SERVICE_VARIANT}.wsgi:application

FROM base as testing

# Install testing packages
RUN grep -v -x -f /openedx/edx-platform/requirements/edx/base.txt /openedx/edx-platform/requirements/edx/development.txt > /tmp/requirements.txt \
    && pip install -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

## Update sqlite3 to prevent segfaults on tests
RUN cd /tmp \
    && curl -O https://sqlite.org/2016/sqlite-autoconf-3140100.tar.gz \
    && tar -xzvf sqlite-autoconf-3140100.tar.gz \
    && cd sqlite-autoconf-3140100 \
    && ./configure --prefix=/usr --disable-static CFLAGS="-g" \
    && make \
    && make install \
    && cd \
    && rm -rf /tmp/sqlite-autoconf-3140100.tar.gz /tmp/sqlite-autoconf-3140100

ENV LD_LIBRARY_PATH /usr/lib

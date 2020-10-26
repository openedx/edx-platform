FROM ubuntu:focal as base

# Warning: This file is experimental.

# Install system requirements
RUN apt-get update && \
    # Global requirements
    DEBIAN_FRONTEND=noninteractive apt-get install --yes \
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
    ntp \
    pkg-config \
    python3-dev \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

WORKDIR /edx/app/edxapp/edx-platform

ENV PATH /edx/app/edxapp/nodeenv/bin:${PATH}
ENV PATH ./node_modules/.bin:${PATH}
ENV CONFIG_ROOT /edx/etc/
ENV PATH /edx/app/edxapp/edx-platform/bin:${PATH}
ENV SETTINGS production
RUN mkdir -p /edx/etc/

ENV VIRTUAL_ENV=/edx/app/edxapp/venvs/edxapp
RUN python3.8 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python requirements
COPY setup.py setup.py
COPY common common
COPY openedx openedx
COPY lms lms
COPY cms cms
COPY requirements/pip.txt requirements/pip.txt
COPY requirements/edx/base.txt requirements/edx/base.txt
RUN pip install -r requirements/pip.txt
RUN pip install -r requirements/edx/base.txt

# Copy just JS requirements and install them.
COPY package.json package.json
COPY package-lock.json package-lock.json
RUN nodeenv /edx/app/edxapp/nodeenv --node=12.11.1 --prebuilt
RUN npm set progress=false && npm install

ENV LMS_CFG /edx/etc/lms.yml
ENV STUDIO_CFG /edx/etc/studio.yml
COPY lms/devstack.yml /edx/etc/lms.yml
COPY cms/devstack.yml /edx/etc/studio.yml

# Copy over remaining code.
# We do this as late as possible so that small changes to the repo don't bust
# the requirements cache.
COPY . .

FROM base as lms
ENV SERVICE_VARIANT lms
ENV DJANGO_SETTINGS_MODULE lms.envs.production
EXPOSE 8000
CMD gunicorn -c /edx/app/edxapp/edx-platform/lms/docker_lms_gunicorn.py --name lms --bind=0.0.0.0:8000 --max-requests=1000 --access-logfile - lms.wsgi:application

FROM lms as lms-newrelic
RUN pip install newrelic
CMD newrelic-admin run-program gunicorn -c /edx/app/edxapp/edx-platform/lms/docker_lms_gunicorn.py --name lms --bind=0.0.0.0:8000 --max-requests=1000 --access-logfile - lms.wsgi:application

FROM lms as lms-devstack
# TODO: This compiles static assets.
# However, it's a bit of a hack, it's slow, and it's inefficient because makes the final Docker cache layer very large.
# We ought to be able to this higher up in the Dockerfile, and do it the same for Prod and Devstack.
RUN mkdir -p test_root/log
ENV DJANGO_SETTINGS_MODULE ""
RUN NO_PREREQ_INSTALL=1 paver update_assets lms --settings devstack_decentralized
ENV DJANGO_SETTINGS_MODULE lms.envs.devstack_decentralized

FROM base as studio
ENV SERVICE_VARIANT cms
ENV DJANGO_SETTINGS_MODULE cms.envs.production
EXPOSE 8010
CMD gunicorn -c /edx/app/edxapp/edx-platform/cms/docker_cms_gunicorn.py --name cms --bind=0.0.0.0:8010 --max-requests=1000 --access-logfile - cms.wsgi:application

FROM studio as studio-newrelic
RUN pip install newrelic
CMD newrelic-admin run-program gunicorn -c /edx/app/edxapp/edx-platform/cms/docker_cms_gunicorn.py --name cms --bind=0.0.0.0:8010 --max-requests=1000 --access-logfile - cms.wsgi:application

FROM studio as studio-devstack
# TODO: This compiles static assets.
# However, it's a bit of a hack, it's slow, and it's inefficient because makes the final Docker cache layer very large.
# We ought to be able to this higher up in the Dockerfile, and do it the same for Prod and Devstack.
RUN mkdir -p test_root/log
ENV DJANGO_SETTINGS_MODULE ""
RUN NO_PREREQ_INSTALL=1 paver update_assets cms --settings devstack_decentralized
ENV DJANGO_SETTINGS_MODULE cms.envs.devstack_decentralized

FROM ubuntu:xenial as base

# Install system requirements
RUN apt update && \
    # Global requirements
    DEBIAN_FRONTEND=noninteractive apt install -y \
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
    software-properties-common \
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
    python3-pip \
    python3.5 \
    -qy && rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN ln -s /usr/bin/pip3 /usr/bin/pip
RUN ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /edx/app/edx-platform/edx-platform

COPY . /edx/app/edx-platform/edx-platform

ENV PATH /edx/app/edx-platform/nodeenv/bin:${PATH}
ENV PATH ./node_modules/.bin:${PATH}
ENV CONFIG_ROOT /edx/etc/
ENV PATH /edx/app/edx-platform/edx-platform/bin:${PATH}
ENV SETTINGS production

# TODO: Install requirements before copying in code.
RUN pip install setuptools==39.0.1 pip==9.0.3
RUN pip install -r requirements/edx/base.txt

RUN nodeenv /edx/app/edx-platform/nodeenv --node=8.9.3 --prebuilt

RUN npm set progress=false \
    && npm install

RUN mkdir -p /edx/etc/

EXPOSE 18000

FROM base as lms
ENV SERVICE_VARIANT lms
ENV LMS_CFG /edx/etc/lms.yaml
CMD gunicorn -c /edx/app/edx-platform/edx-platform/lms/docker_lms_gunicorn.py --name lms --bind=0.0.0.0:18000 --max-requests=1000 --access-logfile - lms.wsgi:application

FROM lms as lms-newrelic
RUN pip install newrelic
CMD newrelic-admin run-program gunicorn -c /edx/app/edx-platform/edx-platform/lms/docker_lms_gunicorn.py --name lms --bind=0.0.0.0:8000 --max-requests=1000 --access-logfile - lms.wsgi:application

FROM base as cms
ENV SERVICE_VARIANT cms
ENV STUDIO_CFG /edx/etc/studio.yaml
CMD gunicorn -c /edx/app/edx-platform/edx-platform/cms/docker_cms_gunicorn.py --name cms --bind=0.0.0.0:8000 --max-requests=1000 --access-logfile - cms.wsgi:application

FROM cms as cms-newrelic
RUN pip install newrelic
CMD newrelic-admin run-program gunicorn -c /edx/app/edx-platform/edx-platform/cms/docker_cms_gunicorn.py --name cms --bind=0.0.0.0:8000 --max-requests=1000 --access-logfile - cms.wsgi:application

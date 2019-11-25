FROM ubuntu:16.04

RUN rm /bin/sh && ln -s /bin/bash /bin/sh

RUN apt-get update \
  && apt-get upgrade -y \
  && apt-get install -y \
    apt-transport-https \
    build-essential \
    gcc \
    g++ \
    gettext \
    git \
    git-core \
    gfortran \
    golang \
    graphviz \
    graphviz-dev \
    language-pack-en \
    libblas-dev \
    liblapack-dev \
    libatlas-base-dev \
    libfreetype6-dev \
    libssl-dev \
    libffi-dev \
    libgeos-dev \
    libjpeg8-dev \
    libsqlite3-dev \
    libmysqlclient-dev \
    libpng12-dev \
    libpq-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libxslt1-dev \
    memcached \
    mongodb \
    openssl \
    pkg-config \
    python-apt \
    python-dev \
    python-mysqldb \
    python-cryptography \
    python-pip \
    python-setuptools \
    python-virtualenv \
    software-properties-common \
    swig \
  && pip install setuptools -U \
  && pip install virtualenv \
  && pip install more-itertools==5.0.0 \
  && pip install tox

# COPY nodesource.gpg.key /tmp/nodesource.gpg.key
# RUN apt-key add /tmp/nodesource.gpg.key \
#   && echo 'deb https://deb.nodesource.com/node_8.x xenial main' > /etc/apt/sources.list.d/nodesource.list \
#   && echo 'deb-src https://deb.nodesource.com/node_8.x xenial main' >> /etc/apt/sources.list.d/nodesource.list \
#   && apt-get update \
#   && apt-get install -y nodejs

WORKDIR /app
COPY . /app

ENTRYPOINT ["/app/scripts/docker_tox.sh"]

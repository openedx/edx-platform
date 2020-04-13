Installation
============

These installation instructions are for installing Open edX from scratch on an empty host. This is a challenging endeavour and non-technical users are **strongly discouraged** to attempt to install Open edX from scratch. Instead, they should use one of the `official self-managed installation methods <https://open.edx.org/get-started/get-started-self-managed/>`__.

Hardware requirements
---------------------

At least 4Gb or RAM and 4 CPU are required to run a bare-bone Open edX platform with the minimal set of features enabled. To sustain traffic for more a couple thousand registered users, it is strongly recommended to upgrade to 8 Gb of RAM.

Dependencies
------------

Open edX depends on several services that need to be running in order to operate properly.

* Elasticsearch 1.5.2
* Memcached
* MySQL v5.6
* MongoDb v3.6.17
* Redis v2.8

The instructions for installing and managing these services are outside the scope of this manual.

System requirements
-------------------

Open edX is only compatible with Ubuntu 16.04.  The following system requirements should be installed::
    
    sudo apt install gettext \
        build-essential \
        curl \
        libxmlsec1-dev \
        libfreetype6-dev \
        swig \
        gcc \
        g++ \
        gfortran \
        graphviz \
        graphviz-dev \
        libffi-dev \
        libfreetype6-dev \
        libgeos-dev \
        libjpeg8-dev \
        liblapack-dev \
        libmysqlclient-dev \
        libpng12-dev \
        libsqlite3-dev \
        libxml2-dev \
        libxmlsec1-dev \
        libxslt1-dev \
        lynx \
        nodejs \
        npm \
        ntp \
        python3.5 \
        python3-dev \
        python3-pip \
        pkg-config \
        software-properties-common

Python requirements
-------------------

::

    pip install setuptools==39.0.1 pip==19.3.1
    pip install -r requirements/base.txt

Production settings
-------------------

.. DOCUMENTME

Web server configuration
------------------------

.. DOCUMENTME

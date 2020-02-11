FROM ubuntu:xenial as base

# Install system requirements
RUN apt update && \
    # Global requirements
    DEBIAN_FRONTEND=noninteractive apt install -y language-pack-en git build-essential software-properties-common curl git-core libxml2-dev libxslt1-dev libmysqlclient-dev libxmlsec1-dev libfreetype6-dev libssl-dev swig gcc g++ \
    # openedx requirements
    gettext gfortran graphviz libgraphviz-dev libffi-dev libfreetype6-dev libgeos-dev libjpeg8-dev liblapack-dev libpng-dev libsqlite3-dev libxml2-dev libxmlsec1-dev libxslt1-dev ntp pkg-config python3.5 python3-pip python3-dev \
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

RUN pip install setuptools==39.0.1 pip==9.0.3
RUN pip install -r requirements/edx/base.txt
RUN pip install newrelic

RUN nodeenv /edx/app/edx-platform/nodeenv --node=8.9.3 --prebuilt

RUN npm set progress=false \
    && npm install

RUN mkdir -p /edx/etc/

EXPOSE 8000


FROM base as lms
ENV SERVICE_VARIANT lms
ENV LMS_CFG /edx/etc/lms.yaml
CMD gunicorn -c /edx/app/edx-platform/edx-platform/lms/docker_lms_gunicorn_conf.py --name lms --bind=0.0.0.0:8000 --max-requests=1000 --access-logfile - lms.wsgi:application


FROM base as studio
ENV SERVICE_VARIANT cms
ENV CMS_CFG /edx/etc/studio.yaml
CMD gunicorn -c /edx/app/edx-platform/edx-platform/cms/docker_cms_gunicorn_conf.py --name cms --bind=0.0.0.0:8000 --max-requests=1000 --access-logfile - cms.wsgi:application

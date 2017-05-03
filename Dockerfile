FROM clintonb/edx-base:python-2.7-slim
ENV DJANGO_SETTINGS_MODULE devstack_docker

WORKDIR /code

# Install OS libs
RUN apt-get update && \
    apt-get install -y \
        apparmor-utils \
        # Iceweasel is the Debian name for Firefox
        iceweasel \
        ipython \
        libfreetype6-dev \
        pkg-config \
        ntp \
        s3cmd \
        xvfb


COPY Makefile /code/
COPY requirements.txt /code/
COPY package.json /code/
COPY pavelib/ /code/pavelib/
COPY requirements/ /code/requirements/

RUN make requirements
RUN make production-requirements

ADD . /code/

RUN make static

# TODO
# TODO Write YAML config

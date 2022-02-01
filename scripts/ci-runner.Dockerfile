FROM summerwind/actions-runner:v2.278.0-ubuntu-20.04 as base

USER root

# Install system requirements
RUN apt-get update && \
    # Global requirements
    DEBIAN_FRONTEND=noninteractive apt-get install --yes \
    build-essential git language-pack-en libmysqlclient-dev libssl-dev libxml2-dev \
    libxmlsec1-dev libxslt1-dev \
    # lynx: Required by https://github.com/edx/edx-platform/blob/b489a4ecb122/openedx/core/lib/html_to_text.py#L16
    lynx xvfb pkg-config \
    python3-dev python3-venv \
    mongodb\
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


FROM base as build

# Install Python requirements
COPY setup.py setup.py
COPY common/lib/ common/lib/
COPY openedx/core/lib openedx/core/lib
COPY lms lms
COPY cms cms
COPY requirements/pip.txt requirements/pip.txt
COPY requirements/edx/testing.txt requirements/edx/testing.txt
COPY requirements/edx/django.txt requirements/edx/django.txt
RUN pip install -r requirements/pip.txt && \
pip install -r requirements/edx/testing.txt -r requirements/edx/django.txt

FROM base as runner

COPY --from=build /edx/app/edxapp/venvs/edxapp /edx/app/edxapp/venvs/edxapp

USER runner

CMD ["/entrypoint.sh"]

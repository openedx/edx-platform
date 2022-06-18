# Copyright 2010 New Relic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import re
import socket
import string
import threading

from newrelic.common.agent_http import InsecureHttpClient
from newrelic.common.encoding_utils import json_decode
from newrelic.core.internal_metrics import internal_count_metric

_logger = logging.getLogger(__name__)
VALID_CHARS_RE = re.compile(r'[0-9a-zA-Z_ ./-]')

class UtilizationHttpClient(InsecureHttpClient):
    SOCKET_TIMEOUT = 0.05

    def send_request(self, *args, **kwargs):
        sock = socket.socket()
        sock.settimeout(self.SOCKET_TIMEOUT)

        # If we cannot connect to the metadata host in SOCKET_TIMEOUT time,
        # this will raise an exception, terminating the fetch before attempting
        # to use an http client.
        # This is an optimization which will speed up connect.
        try:
            sock.connect((self._host, self._port))
        finally:
            sock.close()

        return super(UtilizationHttpClient, self).send_request(*args, **kwargs)


class CommonUtilization(object):
    METADATA_HOST = ''
    METADATA_PATH = ''
    METADATA_QUERY = None
    HEADERS = None
    EXPECTED_KEYS = ()
    VENDOR_NAME = ''
    FETCH_TIMEOUT = 0.4
    CLIENT_CLS = UtilizationHttpClient

    @classmethod
    def record_error(cls, resource, data):
        # As per spec
        internal_count_metric(
                'Supportability/utilization/%s/error' % cls.VENDOR_NAME, 1)
        _logger.warning('Invalid %r data (%r): %r',
                cls.VENDOR_NAME, resource, data)

    @classmethod
    def fetch(cls):
        try:
            with cls.CLIENT_CLS(cls.METADATA_HOST,
                                timeout=cls.FETCH_TIMEOUT) as client:
                resp = client.send_request(method='GET',
                                           path=cls.METADATA_PATH,
                                           params=cls.METADATA_QUERY,
                                           headers=cls.HEADERS)
            if not 200 <= resp[0] < 300:
                raise ValueError(resp[0])
            return resp[1]
        except Exception as e:
            _logger.debug('Unable to fetch %s data from %s%s: %r',
                    cls.VENDOR_NAME, cls.METADATA_HOST, cls.METADATA_PATH, e)
            return None

    @classmethod
    def get_values(cls, response):
        if response is None:
            return

        try:
            return json_decode(response.decode('utf-8'))
        except ValueError:
            _logger.debug('Invalid %s data (%s%s): %r',
                    cls.VENDOR_NAME, cls.METADATA_HOST,
                    cls.METADATA_PATH, response)

    @classmethod
    def valid_chars(cls, data):
        if data is None:
            return False

        for c in data:
            if not VALID_CHARS_RE.match(c) and ord(c) < 0x80:
                return False

        return True

    @classmethod
    def valid_length(cls, data):
        if data is None:
            return False

        b = data.encode('utf-8')
        valid = len(b) <= 255
        if valid:
            return True

        return False

    @classmethod
    def normalize(cls, key, data):
        if data is None:
            return

        try:
            stripped = data.strip()

            if (stripped and cls.valid_length(stripped) and
                    cls.valid_chars(stripped)):
                return stripped
        except:
            pass

    @classmethod
    def sanitize(cls, values):
        if values is None:
            return

        out = {}
        for key in cls.EXPECTED_KEYS:
            metadata = values.get(key, None)
            if not metadata:
                cls.record_error(key, metadata)
                return

            normalized = cls.normalize(key, metadata)
            if not normalized:
                cls.record_error(key, metadata)
                return

            out[key] = normalized

        return out

    @classmethod
    def detect(cls):
        response = cls.fetch()
        values = cls.get_values(response)
        return cls.sanitize(values)


class AWSUtilization(CommonUtilization):
    EXPECTED_KEYS = ('availabilityZone', 'instanceId', 'instanceType')
    METADATA_HOST = '169.254.169.254'
    METADATA_PATH = '/latest/dynamic/instance-identity/document'
    METADATA_TOKEN_PATH = '/latest/api/token'
    HEADERS = {'X-aws-ec2-metadata-token-ttl-seconds': '21600'}
    VENDOR_NAME = 'aws'

    @classmethod
    def fetchAuthToken(cls):
        try:
            with cls.CLIENT_CLS(cls.METADATA_HOST,
                                timeout=cls.FETCH_TIMEOUT) as client:
                resp = client.send_request(method='PUT',
                                           path=cls.METADATA_TOKEN_PATH,
                                           params=cls.METADATA_QUERY,
                                           headers=cls.HEADERS)
            if not 200 <= resp[0] < 300:
                raise ValueError(resp[0])
            return resp[1]
        except Exception as e:
            _logger.debug('Unable to fetch %s data from %s%s: %r',
                    cls.VENDOR_NAME, cls.METADATA_HOST, cls.METADATA_PATH, e)
            return None

    @classmethod
    def fetch(cls):
        try:
            authToken = cls.fetchAuthToken()
            if authToken == None:
                return
            cls.HEADERS = {"X-aws-ec2-metadata-token": authToken}
            with cls.CLIENT_CLS(cls.METADATA_HOST,
                                timeout=cls.FETCH_TIMEOUT) as client:
                resp = client.send_request(method='GET',
                                           path=cls.METADATA_PATH,
                                           params=cls.METADATA_QUERY,
                                           headers=cls.HEADERS)
            if not 200 <= resp[0] < 300:
                raise ValueError(resp[0])
            return resp[1]
        except Exception as e:
            _logger.debug('Unable to fetch %s data from %s%s: %r',
                    cls.VENDOR_NAME, cls.METADATA_HOST, cls.METADATA_PATH, e)
            return None


class AzureUtilization(CommonUtilization):
    METADATA_HOST = '169.254.169.254'
    METADATA_PATH = '/metadata/instance/compute'
    METADATA_QUERY = {'api-version': '2017-03-01'}
    EXPECTED_KEYS = ('location', 'name', 'vmId', 'vmSize')
    HEADERS = {'Metadata': 'true'}
    VENDOR_NAME = 'azure'


class GCPUtilization(CommonUtilization):
    EXPECTED_KEYS = ('id', 'machineType', 'name', 'zone')
    HEADERS = {'Metadata-Flavor': 'Google'}
    METADATA_HOST = 'metadata.google.internal'
    METADATA_PATH = '/computeMetadata/v1/instance/'
    METADATA_QUERY = {'recursive': 'true'}
    VENDOR_NAME = 'gcp'

    @classmethod
    def normalize(cls, key, data):
        if data is None:
            return

        if key in ('machineType', 'zone'):
            formatted = data.strip().split('/')[-1]
        elif key == 'id':
            formatted = str(data)
        else:
            formatted = data

        return super(GCPUtilization, cls).normalize(key, formatted)


class PCFUtilization(CommonUtilization):
    EXPECTED_KEYS = ('cf_instance_guid', 'cf_instance_ip', 'memory_limit')
    VENDOR_NAME = 'pcf'

    @staticmethod
    def fetch():
        cf_instance_guid = os.environ.get('CF_INSTANCE_GUID')
        cf_instance_ip = os.environ.get('CF_INSTANCE_IP')
        memory_limit = os.environ.get('MEMORY_LIMIT')
        pcf_vars = (cf_instance_guid, cf_instance_ip, memory_limit)
        if all(pcf_vars):
            return pcf_vars

    @classmethod
    def get_values(cls, response):
        if response is None or len(response) != 3:
            return

        values = {}
        for k, v in zip(cls.EXPECTED_KEYS, response):
            if hasattr(v, 'decode'):
                v = v.decode('utf-8')
            values[k] = v
        return values


class DockerUtilization(CommonUtilization):
    VENDOR_NAME = 'docker'
    EXPECTED_KEYS = ('id',)
    METADATA_FILE = '/proc/self/cgroup'
    DOCKER_RE = re.compile(r'([0-9a-f]{64,})')

    @classmethod
    def fetch(cls):
        try:
            with open(cls.METADATA_FILE, 'rb') as f:
                for line in f:
                    stripped = line.decode('utf-8').strip()
                    cgroup = stripped.split(':')
                    if len(cgroup) != 3:
                        continue
                    subsystems = cgroup[1].split(',')
                    if 'cpu' in subsystems:
                        return cgroup[2]
        except:
            # There are all sorts of exceptions that can occur here
            # (i.e. permissions, non-existent file, etc)
            pass

    @classmethod
    def get_values(cls, contents):
        if contents is None:
            return

        value = contents.split('/')[-1]
        match = cls.DOCKER_RE.search(value)
        if match:
            value = match.group(0)
            return {'id': value}

    @classmethod
    def valid_chars(cls, data):
        if data is None:
            return False

        hex_digits = set(string.hexdigits)

        valid = all((c in hex_digits for c in data))
        if valid:
            return True

        return False

    @classmethod
    def valid_length(cls, data):
        if data is None:
            return False

        # Must be exactly 64 characters
        valid = len(data) == 64
        if valid:
            return True

        return False


class KubernetesUtilization(CommonUtilization):
    EXPECTED_KEYS = ('kubernetes_service_host', )
    VENDOR_NAME = 'kubernetes'

    @staticmethod
    def fetch():
        kubernetes_service_host = os.environ.get('KUBERNETES_SERVICE_HOST')
        if kubernetes_service_host:
            return kubernetes_service_host

    @classmethod
    def get_values(cls, v):
        if v is None:
            return

        if hasattr(v, 'decode'):
            v = v.decode('utf-8')

        return {'kubernetes_service_host': v}

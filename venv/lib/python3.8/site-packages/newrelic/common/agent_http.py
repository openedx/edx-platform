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

from __future__ import print_function

import os
import sys
import time
import zlib
from pprint import pprint

import newrelic.packages.urllib3 as urllib3
from newrelic import version
from newrelic.common import certs
from newrelic.common.encoding_utils import json_decode, json_encode
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import patch_function_wrapper
from newrelic.core.internal_metrics import internal_count_metric, internal_metric
from newrelic.network.exceptions import NetworkInterfaceException

try:
    from ssl import get_default_verify_paths
except ImportError:

    class _DEFAULT_CERT_PATH(object):
        cafile = None
        capath = None

    def get_default_verify_paths():
        return _DEFAULT_CERT_PATH


# User agent string that must be used in all requests. The data collector
# does not rely on this, but is used to target specific agents if there
# is a problem with data collector handling requests.

USER_AGENT = "NewRelic-PythonAgent/%s (Python %s %s)" % (
    version,
    sys.version.split()[0],
    sys.platform,
)


# This is a monkey patch for urllib3 + python3.6 + gevent/eventlet.
# Gevent/Eventlet patches the ssl library resulting in a re-binding that causes
# infinite recursion in a super call. In order to prevent this error, the
# SSLContext object should be accessed through the ssl library attribute.
#
#   https://github.com/python/cpython/commit/328067c468f82e4ec1b5c510a4e84509e010f296#diff-c49248c7181161e24048bec5e35ba953R457
#   https://github.com/gevent/gevent/blob/f3acb176d0f0f1ac797b50e44a5e03726f687c53/src/gevent/_ssl3.py#L67
#   https://github.com/shazow/urllib3/pull/1177
#   https://bugs.python.org/issue29149
#
@patch_function_wrapper("newrelic.packages.urllib3.util.ssl_", "SSLContext")
def _urllib3_ssl_recursion_workaround(wrapped, instance, args, kwargs):
    try:
        import ssl

        return ssl.SSLContext(*args, **kwargs)
    except:
        return wrapped(*args, **kwargs)


class BaseClient(object):
    AUDIT_LOG_ID = 0

    def __init__(
        self,
        host,
        port,
        proxy_scheme=None,
        proxy_host=None,
        proxy_port=None,
        proxy_user=None,
        proxy_pass=None,
        timeout=None,
        ca_bundle_path=None,
        disable_certificate_validation=False,
        compression_threshold=64 * 1024,
        compression_level=None,
        compression_method="gzip",
        max_payload_size_in_bytes=1000000,
        audit_log_fp=None,
    ):
        self._audit_log_fp = audit_log_fp

    def __enter__(self):
        return self

    def __exit__(self, exc, value, tb):
        pass

    def close_connection(self):
        pass

    def finalize(self):
        pass

    @staticmethod
    def _supportability_request(params, payload, body, compression_time):
        pass

    @classmethod
    def log_request(
        cls, fp, method, url, params, payload, headers, body=None, compression_time=None
    ):
        cls._supportability_request(params, payload, body, compression_time)

        if not fp:
            return

        # Maintain a global AUDIT_LOG_ID attached to all class instances
        # NOTE: this is not thread safe so this class cannot be used
        # across threads when audit logging is on
        cls.AUDIT_LOG_ID += 1

        print(
            "TIME: %r" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), file=fp,
        )
        print(file=fp)
        print("ID: %r" % cls.AUDIT_LOG_ID, file=fp)
        print(file=fp)
        print("PID: %r" % os.getpid(), file=fp)
        print(file=fp)
        print("URL: %r" % url, file=fp)
        print(file=fp)
        print("PARAMS: %r" % params, file=fp)
        print(file=fp)
        print("HEADERS: %r" % headers, file=fp)
        print(file=fp)
        print("DATA:", end=" ", file=fp)

        try:
            data = json_decode(payload.decode("utf-8"))
        except Exception:
            data = payload

        pprint(data, stream=fp)

        print(file=fp)
        print(78 * "=", file=fp)
        print(file=fp)

        fp.flush()

        return cls.AUDIT_LOG_ID

    @staticmethod
    def _supportability_response(status, exc, connection="direct"):
        pass

    @classmethod
    def log_response(cls, fp, log_id, status, headers, data, connection="direct"):
        if not status:
            # Exclude traceback in order to prevent a reference cycle
            exc_info = sys.exc_info()[:2]
        else:
            exc_info = None

        cls._supportability_response(status, exc_info and exc_info[0], connection)

        if not fp:
            return

        try:
            result = json_decode(data)
        except Exception:
            result = data

        print(
            "TIME: %r" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), file=fp
        )
        print(file=fp)
        print("ID: %r" % log_id, file=fp)
        print(file=fp)
        print("PID: %r" % os.getpid(), file=fp)
        print(file=fp)

        if exc_info:
            print("Exception: %r" % exc_info[1], file=fp)
            print(file=fp)
        else:
            print("STATUS: %r" % status, file=fp)
            print(file=fp)
            print("HEADERS:", end=" ", file=fp)
            pprint(dict(headers), stream=fp)
            print(file=fp)
            print("RESULT:", end=" ", file=fp)
            pprint(result, stream=fp)
            print(file=fp)

        print(78 * "=", file=fp)
        print(file=fp)

        fp.flush()

    def send_request(
        self,
        method="POST",
        path="/agent_listener/invoke_raw_method",
        params=None,
        headers=None,
        payload=None,
    ):
        return 202, b""


class HttpClient(BaseClient):
    CONNECTION_CLS = urllib3.HTTPSConnectionPool
    PREFIX_SCHEME = "https://"
    BASE_HEADERS = urllib3.make_headers(
        keep_alive=True, accept_encoding=True, user_agent=USER_AGENT
    )

    def __init__(
        self,
        host,
        port=443,
        proxy_scheme=None,
        proxy_host=None,
        proxy_port=None,
        proxy_user=None,
        proxy_pass=None,
        timeout=None,
        ca_bundle_path=None,
        disable_certificate_validation=False,
        compression_threshold=64 * 1024,
        compression_level=None,
        compression_method="gzip",
        max_payload_size_in_bytes=1000000,
        audit_log_fp=None,
    ):
        self._host = host
        port = self._port = port
        self._compression_threshold = compression_threshold
        self._compression_level = compression_level
        self._compression_method = compression_method
        self._max_payload_size_in_bytes = max_payload_size_in_bytes
        self._audit_log_fp = audit_log_fp

        self._prefix = ""

        self._headers = dict(self.BASE_HEADERS)
        self._connection_kwargs = connection_kwargs = {
            "timeout": timeout,
        }
        self._urlopen_kwargs = urlopen_kwargs = {}

        if self.CONNECTION_CLS.scheme == "https":
            if not ca_bundle_path:
                verify_path = get_default_verify_paths()

                # If there is no resolved cafile, assume the bundled certs are
                # required and report this condition as a supportability metric.
                if not verify_path.cafile:
                    ca_bundle_path = certs.where()
                    internal_metric(
                        "Supportability/Python/Certificate/BundleRequired", 1
                    )

            if ca_bundle_path:
                if os.path.isdir(ca_bundle_path):
                    connection_kwargs["ca_cert_dir"] = ca_bundle_path
                else:
                    connection_kwargs["ca_certs"] = ca_bundle_path

            if disable_certificate_validation:
                connection_kwargs["cert_reqs"] = "NONE"

        proxy = self._parse_proxy(
            proxy_scheme, proxy_host, proxy_port, proxy_user, proxy_pass,
        )
        proxy_headers = (
            proxy and proxy.auth and urllib3.make_headers(proxy_basic_auth=proxy.auth)
        )

        if proxy:
            if self.CONNECTION_CLS.scheme == "https" and proxy.scheme != "https":
                connection_kwargs["_proxy"] = proxy
                connection_kwargs["_proxy_headers"] = proxy_headers
            else:
                self._host = proxy.host
                self._port = proxy.port or 443
                self._prefix = self.PREFIX_SCHEME + host + ":" + str(port)
                urlopen_kwargs["assert_same_host"] = False
                if proxy_headers:
                    self._headers.update(proxy_headers)

        # Logging
        self._proxy = proxy

        self._connection_attr = None

    @staticmethod
    def _parse_proxy(scheme, host, port, username, password):
        # Users may specify a full URL for the host
        # In this case, the URL is used as a starting point to build up the URL
        components = urllib3.util.parse_url(host)

        scheme = components.scheme or scheme or None
        host = components.host or host or None
        port = components.port or port or None

        if components.auth:
            auth = components.auth
        else:
            auth = username
            if auth and password is not None:
                auth = auth + ":" + password

        # Host must be defined
        if not host:
            return

        # At least one of (scheme, port) must be defined
        if not scheme and not port:
            return

        return urllib3.util.Url(scheme=scheme, auth=auth, host=host, port=port)

    def __enter__(self):
        self._connection.__enter__()
        return self

    def __exit__(self, exc, value, tb):
        if self._connection_attr:
            self._connection_attr.__exit__(exc, value, tb)
            self._connection_attr = None

    @property
    def _connection(self):
        if self._connection_attr:
            return self._connection_attr

        retries = urllib3.Retry(
            total=False, connect=None, read=None, redirect=0, status=None
        )
        self._connection_attr = self.CONNECTION_CLS(
            self._host,
            self._port,
            strict=True,
            retries=retries,
            **self._connection_kwargs
        )
        return self._connection_attr

    def close_connection(self):
        if self._connection_attr:
            self._connection_attr.close()
            self._connection_attr = None

    def log_request(
        self,
        fp,
        method,
        url,
        params,
        payload,
        headers,
        body=None,
        compression_time=None,
    ):
        if not self._prefix:
            url = self.CONNECTION_CLS.scheme + "://" + self._host + url

        return super(HttpClient, self).log_request(
            fp, method, url, params, payload, headers, body, compression_time
        )

    @staticmethod
    def _compress(data, method="gzip", level=None):
        compression_start = time.time()
        level = level or zlib.Z_DEFAULT_COMPRESSION
        wbits = 31 if method == "gzip" else 15

        compressor = zlib.compressobj(level, zlib.DEFLATED, wbits)
        data = compressor.compress(data)
        data += compressor.flush()

        compression_time = max(time.time(), compression_start) - compression_start

        return data, compression_time

    def send_request(
        self,
        method="POST",
        path="/agent_listener/invoke_raw_method",
        params=None,
        headers=None,
        payload=None,
    ):
        if self._proxy:
            proxy_scheme = self._proxy.scheme or "http"
            connection = proxy_scheme + "-proxy"
        else:
            connection = "direct"

        merged_headers = dict(self._headers)
        if headers:
            merged_headers.update(headers)
        path = self._prefix + path
        body = payload
        compression_time = None
        if payload is not None:
            if len(payload) > self._compression_threshold:
                body, compression_time = self._compress(
                    payload,
                    method=self._compression_method,
                    level=self._compression_level,
                )
                content_encoding = self._compression_method
            else:
                content_encoding = "Identity"

            merged_headers["Content-Encoding"] = content_encoding

        request_id = self.log_request(
            self._audit_log_fp,
            "POST",
            path,
            params,
            payload,
            merged_headers,
            body,
            compression_time,
        )

        if body and len(body) > self._max_payload_size_in_bytes:
            return 413, b""

        try:
            response = self._connection.request_encode_url(
                method,
                path,
                fields=params,
                body=body,
                headers=merged_headers,
                **self._urlopen_kwargs
            )
        except urllib3.exceptions.HTTPError as e:
            self.log_response(
                self._audit_log_fp, request_id, 0, None, None, connection,
            )
            # All urllib3 HTTP errors should be treated as a network
            # interface exception.
            raise NetworkInterfaceException(e)

        self.log_response(
            self._audit_log_fp,
            request_id,
            response.status,
            response.headers,
            response.data,
            connection,
        )

        return response.status, response.data


class InsecureHttpClient(HttpClient):
    CONNECTION_CLS = urllib3.HTTPConnectionPool
    PREFIX_SCHEME = "http://"

    def __init__(
        self,
        host,
        port=80,
        proxy_scheme=None,
        proxy_host=None,
        proxy_port=None,
        proxy_user=None,
        proxy_pass=None,
        timeout=None,
        ca_bundle_path=None,
        disable_certificate_validation=False,
        compression_threshold=64 * 1024,
        compression_level=None,
        compression_method="gzip",
        max_payload_size_in_bytes=1000000,
        audit_log_fp=None,
    ):
        proxy = self._parse_proxy(proxy_scheme, proxy_host, None, None, None)
        if proxy and proxy.scheme == "https":
            # HTTPS must be used to connect to the proxy
            self.CONNECTION_CLS = urllib3.HTTPSConnectionPool
        else:
            # Disable any HTTPS specific options
            ca_bundle_path = None
            disable_certificate_validation = None

        super(InsecureHttpClient, self).__init__(
            host,
            port,
            proxy_scheme,
            proxy_host,
            proxy_port,
            proxy_user,
            proxy_pass,
            timeout,
            ca_bundle_path,
            disable_certificate_validation,
            compression_threshold,
            compression_level,
            compression_method,
            max_payload_size_in_bytes,
            audit_log_fp,
        )


class SupportabilityMixin(object):
    @staticmethod
    def _supportability_request(params, payload, body, compression_time):
        # *********
        # Used only for supportability metrics. Do not use to drive business
        # logic!
        agent_method = params and params.get("method")
        # *********

        if agent_method and body:
            # Compression was applied
            if compression_time is not None:
                internal_metric(
                    "Supportability/Python/Collector/ZLIB/Bytes/%s" % agent_method,
                    len(payload),
                )
                internal_metric(
                    "Supportability/Python/Collector/ZLIB/Compress/%s" % agent_method,
                    compression_time,
                )

            internal_metric(
                "Supportability/Python/Collector/Output/Bytes/%s" % agent_method,
                len(body),
            )

    @staticmethod
    def _supportability_response(status, exc, connection="direct"):
        if exc or not 200 <= status < 300:
            internal_count_metric("Supportability/Python/Collector/Failures", 1)
            internal_count_metric(
                "Supportability/Python/Collector/Failures/%s" % connection, 1
            )

            if exc:
                internal_count_metric(
                    "Supportability/Python/Collector/Exception/"
                    "%s" % callable_name(exc),
                    1,
                )
            else:
                internal_count_metric(
                    "Supportability/Python/Collector/HTTPError/%d" % status, 1
                )


class ApplicationModeClient(SupportabilityMixin, HttpClient):
    pass


class DeveloperModeClient(SupportabilityMixin, BaseClient):
    RESPONSES = {
        "preconnect": {u"redirect_host": u"fake-collector.newrelic.com"},
        "agent_settings": [],
        "connect": {
            u"js_agent_loader": u"<!-- NREUM -->",
            u"js_agent_file": u"fake-js-agent.newrelic.com/nr-0.min.js",
            u"browser_key": u"1234567890",
            u"browser_monitoring.loader_version": u"0",
            u"beacon": u"fake-beacon.newrelic.com",
            u"error_beacon": u"fake-jserror.newrelic.com",
            u"apdex_t": 0.5,
            u"encoding_key": u"1111111111111111111111111111111111111111",
            u"entity_guid": u"DEVELOPERMODEENTITYGUID",
            u"agent_run_id": u"1234567",
            u"product_level": 50,
            u"trusted_account_ids": [12345],
            u"trusted_account_key": u"12345",
            u"url_rules": [],
            u"collect_errors": True,
            u"account_id": u"12345",
            u"cross_process_id": u"12345#67890",
            u"messages": [
                {u"message": u"Reporting to fake collector", u"level": u"INFO"}
            ],
            u"sampling_rate": 0,
            u"collect_traces": True,
            u"collect_span_events": True,
            u"data_report_period": 60,
        },
        "metric_data": None,
        "get_agent_commands": [],
        "profile_data": [],
        "agent_command_results": [],
        "error_data": None,
        "transaction_sample_data": None,
        "sql_trace_data": None,
        "analytic_event_data": None,
        "error_event_data": None,
        "span_event_data": None,
        "custom_event_data": None,
        "shutdown": [],
    }

    def send_request(
        self,
        method="POST",
        path="/agent_listener/invoke_raw_method",
        params=None,
        headers=None,
        payload=None,
    ):
        request_id = self.log_request(
            self._audit_log_fp,
            "POST",
            "https://fake-collector.newrelic.com" + path,
            params,
            payload,
            headers,
        )
        if not params or "method" not in params:
            return 400, b"Missing method parameter"

        method = params["method"]
        if method not in self.RESPONSES:
            return 400, b"Invalid method received"

        result = self.RESPONSES[method]
        payload = {"return_value": result}
        response_data = json_encode(payload).encode("utf-8")
        self.log_response(
            self._audit_log_fp, request_id, 200, {}, response_data,
        )
        return 200, response_data


class ServerlessModeClient(DeveloperModeClient):
    def __init__(self, *args, **kwargs):
        super(ServerlessModeClient, self).__init__(*args, **kwargs)
        self.payload = {}

    def send_request(
        self,
        method="POST",
        path="/agent_listener/invoke_raw_method",
        params=None,
        headers=None,
        payload=None,
    ):
        result = super(ServerlessModeClient, self).send_request(
            method=method, path=path, params=params, headers=headers, payload=payload
        )

        if result[0] == 200:
            agent_method = params["method"]
            self.payload[agent_method] = json_decode(payload.decode("utf-8"))

        return result

    def finalize(self):
        output = dict(self.payload)
        self.payload.clear()
        return output

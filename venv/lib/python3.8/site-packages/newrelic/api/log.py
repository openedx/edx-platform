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

import json
import logging
import re
from logging import Formatter, LogRecord

from newrelic.api.time_trace import get_linking_metadata
from newrelic.api.transaction import current_transaction
from newrelic.common import agent_http
from newrelic.common.object_names import parse_exc_info
from newrelic.core.attribute import truncate
from newrelic.core.config import global_settings, is_expected_error


def format_exc_info(exc_info):
    _, _, fullnames, message = parse_exc_info(exc_info)
    fullname = fullnames[0]

    formatted = {
        "error.class": fullname,
        "error.message": message,
    }

    expected = is_expected_error(exc_info)
    if expected is not None:
        formatted["error.expected"] = expected

    return formatted


class NewRelicContextFormatter(Formatter):
    DEFAULT_LOG_RECORD_KEYS = frozenset(vars(LogRecord("", 0, "", 0, "", (), None)))

    def __init__(self, *args, **kwargs):
        super(NewRelicContextFormatter, self).__init__()

    @classmethod
    def log_record_to_dict(cls, record):
        output = {
            "timestamp": int(record.created * 1000),
            "message": record.getMessage(),
            "log.level": record.levelname,
            "logger.name": record.name,
            "thread.id": record.thread,
            "thread.name": record.threadName,
            "process.id": record.process,
            "process.name": record.processName,
            "file.name": record.pathname,
            "line.number": record.lineno,
        }
        output.update(get_linking_metadata())

        DEFAULT_LOG_RECORD_KEYS = cls.DEFAULT_LOG_RECORD_KEYS
        if len(record.__dict__) > len(DEFAULT_LOG_RECORD_KEYS):
            for key in record.__dict__:
                if key not in DEFAULT_LOG_RECORD_KEYS:
                    output["extra." + key] = getattr(record, key)

        if record.exc_info:
            output.update(format_exc_info(record.exc_info))

        return output

    def format(self, record):
        def safe_str(object, *args, **kwargs):
            """Convert object to str, catching any errors raised."""
            try:
                return str(object, *args, **kwargs)
            except:
                return "<unprintable %s object>" % type(object).__name__

        return json.dumps(self.log_record_to_dict(record), default=safe_str, separators=(",", ":"))


class NewRelicLogHandler(logging.Handler):
    """This is an experimental log handler provided by the community. Use with caution."""

    PATH = "/log/v1"

    def __init__(
        self,
        level=logging.INFO,
        license_key=None,
        host=None,
        port=443,
        proxy_scheme=None,
        proxy_host=None,
        proxy_user=None,
        proxy_pass=None,
        timeout=None,
        ca_bundle_path=None,
        disable_certificate_validation=False,
    ):
        super(NewRelicLogHandler, self).__init__(level=level)
        self.license_key = license_key or self.settings.license_key
        self.host = host or self.settings.host or self.default_host(self.license_key)

        self.client = agent_http.HttpClient(
            host=host,
            port=port,
            proxy_scheme=proxy_scheme,
            proxy_host=proxy_host,
            proxy_user=proxy_user,
            proxy_pass=proxy_pass,
            timeout=timeout,
            ca_bundle_path=ca_bundle_path,
            disable_certificate_validation=disable_certificate_validation,
        )

        self.setFormatter(NewRelicContextFormatter())

    @property
    def settings(self):
        transaction = current_transaction()
        if transaction:
            return transaction.settings
        return global_settings()

    def emit(self, record):
        try:
            headers = {"Api-Key": self.license_key or "", "Content-Type": "application/json"}
            payload = self.format(record).encode("utf-8")
            with self.client:
                status_code, response = self.client.send_request(path=self.PATH, headers=headers, payload=payload)
                if status_code < 200 or status_code >= 300:
                    raise RuntimeError(
                        "An unexpected HTTP response of %r was received for request made to https://%s:%d%s."
                        "The response payload for the request was %r. If this issue persists then please "
                        "report this problem to New Relic support for further investigation."
                        % (
                            status_code,
                            self.client._host,
                            self.client._port,
                            self.PATH,
                            truncate(response.decode("utf-8"), 1024),
                        )
                    )

        except Exception:
            self.handleError(record)

    def default_host(self, license_key):
        if not license_key:
            return "log-api.newrelic.com"

        region_aware_match = re.match("^(.+?)x", license_key)
        if not region_aware_match:
            return "log-api.newrelic.com"

        region = region_aware_match.group(1)
        host = "log-api." + region + ".newrelic.com"
        return host

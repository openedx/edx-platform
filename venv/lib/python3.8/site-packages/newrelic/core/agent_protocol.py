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

from newrelic import version
from newrelic.common import system_info
from newrelic.common.agent_http import ApplicationModeClient, ServerlessModeClient
from newrelic.common.encoding_utils import (
    json_decode,
    json_encode,
    serverless_payload_encode,
)
from newrelic.common.utilization import (
    AWSUtilization,
    AzureUtilization,
    DockerUtilization,
    GCPUtilization,
    KubernetesUtilization,
    PCFUtilization,
)
from newrelic.core.attribute import truncate
from newrelic.core.config import (
    fetch_config_setting,
    finalize_application_settings,
    global_settings_dump,
)
from newrelic.core.internal_metrics import internal_count_metric
from newrelic.network.exceptions import (
    DiscardDataForRequest,
    ForceAgentDisconnect,
    ForceAgentRestart,
    NetworkInterfaceException,
    RetryDataForRequest,
)

_logger = logging.getLogger(__name__)


class AgentProtocol(object):
    VERSION = 17

    STATUS_CODE_RESPONSE = {
        400: DiscardDataForRequest,
        401: ForceAgentRestart,
        403: DiscardDataForRequest,
        404: DiscardDataForRequest,
        405: DiscardDataForRequest,
        407: DiscardDataForRequest,
        408: RetryDataForRequest,
        409: ForceAgentRestart,
        410: ForceAgentDisconnect,
        411: DiscardDataForRequest,
        413: DiscardDataForRequest,
        414: DiscardDataForRequest,
        415: DiscardDataForRequest,
        417: DiscardDataForRequest,
        429: RetryDataForRequest,
        431: DiscardDataForRequest,
        500: RetryDataForRequest,
        503: RetryDataForRequest,
    }
    LOG_MESSAGES = {
        401: (
            logging.ERROR,
            (
                "Data collector is indicating that an incorrect license key "
                "has been supplied by the agent. Please correct any problem "
                "with the license key or report this problem to New Relic "
                "support."
            ),
        ),
        407: (
            logging.WARNING,
            (
                "Received a proxy authentication required response from the "
                "data collector. This occurs when the agent has a "
                "misconfigured proxy. Please check your proxy configuration. "
                "Proxy user: %(proxy_user)s, proxy host: %(proxy_host)s "
                "proxy port: %(proxy_port)s."
            ),
        ),
        408: (
            logging.INFO,
            (
                "Data collector is indicating that a timeout has occurred. "
                "Check your network settings. If this keeps occurring on a "
                "regular basis, please report this problem to New Relic "
                "support."
            ),
        ),
        409: (
            logging.INFO,
            (
                "An automatic internal agent restart has been "
                "requested by the data collector for the application "
                "where the agent run was %(agent_run_id)s."
            ),
        ),
        410: (
            logging.CRITICAL,
            (
                "Disconnection of the agent has been requested by the data "
                "collector for the application where the agent run was "
                "%(agent_run_id)s. Please contact New Relic support for "
                "further information. content=%(content)s"
            ),
        ),
        429: (
            logging.WARNING,
            (
                "The agent received a 429 response from the data collector, "
                "indicating that it is currently experiencing issues for "
                "endpoint %(method)s. The agent will retry again on the next "
                "scheduled harvest."
            ),
        ),
        "default": (
            logging.WARNING,
            (
                "Received a non 200 or 202 HTTP response from the data "
                "collector where params=%(params)s, headers=%(headers)s, "
                "status_code=%(status_code)s and content=%(content)s."
            ),
        ),
    }
    PARAMS_ALLOWLIST = frozenset(("method", "protocol_version", "marshal_format", "run_id"))

    SECURITY_SETTINGS = (
        "capture_params",
        "transaction_tracer.record_sql",
        "strip_exception_messages.enabled",
        "custom_insights_events.enabled",
    )

    LOGGER_FUNC_MAPPING = {
        "ERROR": _logger.error,
        "WARN": _logger.warning,
        "INFO": _logger.info,
        "VERBOSE": _logger.debug,
    }

    def __init__(self, settings, host=None, client_cls=ApplicationModeClient):
        if settings.audit_log_file:
            audit_log_fp = open(settings.audit_log_file, "a")
        else:
            audit_log_fp = None

        self.client = client_cls(
            host=host or settings.host,
            port=settings.port or 443,
            proxy_scheme=settings.proxy_scheme,
            proxy_host=settings.proxy_host,
            proxy_port=settings.proxy_port,
            proxy_user=settings.proxy_user,
            proxy_pass=settings.proxy_pass,
            timeout=settings.agent_limits.data_collector_timeout,
            ca_bundle_path=settings.ca_bundle_path,
            disable_certificate_validation=settings.debug.disable_certificate_validation,
            compression_threshold=settings.agent_limits.data_compression_threshold,
            compression_level=settings.agent_limits.data_compression_level,
            compression_method=settings.compressed_content_encoding,
            max_payload_size_in_bytes=settings.max_payload_size_in_bytes,
            audit_log_fp=audit_log_fp,
        )

        self._params = {
            "protocol_version": self.VERSION,
            "license_key": settings.license_key,
            "marshal_format": "json",
        }
        self._headers = {}

        # In Python 2, the JSON is loaded with unicode keys and values;
        # however, the header name must be a non-unicode value when given to
        # the HTTP library. This code converts the header name from unicode to
        # non-unicode.
        if settings.request_headers_map:
            for k, v in settings.request_headers_map.items():
                if not isinstance(k, str):
                    k = k.encode("utf-8")
                self._headers[k] = v

        self._headers["Content-Type"] = "application/json"
        self._run_token = settings.agent_run_id

        # Logging
        self._proxy_host = settings.proxy_host
        self._proxy_port = settings.proxy_port
        self._proxy_user = settings.proxy_user

        # Do not access configuration anywhere inside the class
        self.configuration = settings

    def __enter__(self):
        self.client.__enter__()
        return self

    def __exit__(self, exc, value, tb):
        self.client.__exit__(exc, value, tb)

    def close_connection(self):
        self.client.close_connection()

    def send(self, method, payload=()):
        params, headers, payload = self._to_http(method, payload)

        try:
            response = self.client.send_request(params=params, headers=headers, payload=payload)
        except NetworkInterfaceException:
            # All HTTP errors are currently retried
            raise RetryDataForRequest

        status, data = response

        if not 200 <= status < 300:
            if status == 413:
                internal_count_metric(
                    "Supportability/Python/Collector/MaxPayloadSizeLimit/%s" % method,
                    1,
                )
            level, message = self.LOG_MESSAGES.get(status, self.LOG_MESSAGES["default"])
            _logger.log(
                level,
                message,
                {
                    "proxy_host": self._proxy_host,
                    "proxy_port": self._proxy_port,
                    "proxy_user": self._proxy_user,
                    "method": method,
                    "status_code": status,
                    "headers": headers,
                    "params": {k: v for k, v in params.items() if k in self.PARAMS_ALLOWLIST},
                    "content": truncate(data, 1024),
                    "agent_run_id": self._run_token,
                },
            )
            exception = self.STATUS_CODE_RESPONSE.get(status, DiscardDataForRequest)
            raise exception
        if status == 200:
            return json_decode(data.decode("utf-8"))["return_value"]

    def _to_http(self, method, payload=()):
        params = dict(self._params)
        params["method"] = method
        if self._run_token:
            params["run_id"] = self._run_token
        return params, self._headers, json_encode(payload).encode("utf-8")

    @staticmethod
    def _connect_payload(app_name, linked_applications, environment, settings):
        settings = global_settings_dump(settings)
        app_names = [app_name] + linked_applications

        hostname = system_info.gethostname(
            settings["heroku.use_dyno_names"],
            settings["heroku.dyno_name_prefixes_to_shorten"],
        )

        ip_address = system_info.getips()

        connect_settings = {}
        connect_settings["browser_monitoring.loader"] = settings["browser_monitoring.loader"]
        connect_settings["browser_monitoring.debug"] = settings["browser_monitoring.debug"]

        security_settings = {}
        security_settings["capture_params"] = settings["capture_params"]
        security_settings["transaction_tracer"] = {}
        security_settings["transaction_tracer"]["record_sql"] = settings["transaction_tracer.record_sql"]

        utilization_settings = {}
        # metadata_version corresponds to the utilization spec being used.
        utilization_settings["metadata_version"] = 5
        utilization_settings["logical_processors"] = system_info.logical_processor_count()
        utilization_settings["total_ram_mib"] = system_info.total_physical_memory()
        utilization_settings["hostname"] = hostname
        if ip_address:
            utilization_settings["ip_address"] = ip_address

        boot_id = system_info.BootIdUtilization.detect()
        if boot_id:
            utilization_settings["boot_id"] = boot_id

        utilization_conf = {}
        logical_processor_conf = settings["utilization.logical_processors"]
        total_ram_conf = settings["utilization.total_ram_mib"]
        hostname_conf = settings["utilization.billing_hostname"]
        if logical_processor_conf:
            utilization_conf["logical_processors"] = logical_processor_conf
        if total_ram_conf:
            utilization_conf["total_ram_mib"] = total_ram_conf
        if hostname_conf:
            utilization_conf["hostname"] = hostname_conf
        if utilization_conf:
            utilization_settings["config"] = utilization_conf

        vendors = []
        if settings["utilization.detect_aws"]:
            vendors.append(AWSUtilization)
        if settings["utilization.detect_pcf"]:
            vendors.append(PCFUtilization)
        if settings["utilization.detect_gcp"]:
            vendors.append(GCPUtilization)
        if settings["utilization.detect_azure"]:
            vendors.append(AzureUtilization)

        utilization_vendor_settings = {}
        for vendor in vendors:
            metadata = vendor.detect()
            if metadata:
                utilization_vendor_settings[vendor.VENDOR_NAME] = metadata
                break

        if settings["utilization.detect_docker"]:
            docker = DockerUtilization.detect()
            if docker:
                utilization_vendor_settings["docker"] = docker

        if settings["utilization.detect_kubernetes"]:
            kubernetes = KubernetesUtilization.detect()
            if kubernetes:
                utilization_vendor_settings["kubernetes"] = kubernetes

        if utilization_vendor_settings:
            utilization_settings["vendors"] = utilization_vendor_settings

        display_host = settings["process_host.display_name"]
        if display_host is None:
            display_host = hostname

        metadata = {}
        for env_var in os.environ:
            if env_var.startswith("NEW_RELIC_METADATA_"):
                metadata[env_var] = os.environ[env_var]

        return (
            {
                "host": hostname,
                "pid": os.getpid(),
                "language": "python",
                "app_name": app_names,
                "identifier": ",".join(app_names),
                "agent_version": version,
                "environment": environment,
                "metadata": metadata,
                "settings": connect_settings,
                "security_settings": security_settings,
                "utilization": utilization_settings,
                "high_security": settings["high_security"],
                "event_harvest_config": settings["event_harvest_config"],
                "labels": settings["labels"],
                "display_host": display_host,
            },
        )

    @classmethod
    def _apply_high_security_mode_fixups(cls, server_settings, local_settings):
        # When High Security Mode is True in local_settings, then all
        # security related settings should be removed from server_settings.
        # That way, when the local and server side configuration settings
        # are merged, the local security settings will not get overwritten
        # by the server side configuration settings.
        #
        # Note that security settings we may want to remove can appear at
        # both the top level of the server settings, but also nested within
        # the 'agent_config' sub dictionary. Those settings at the top level
        # represent how the settings were previously overridden for high
        # security mode. Those in 'agent_config' correspond to server side
        # configuration as set by the user.

        if not local_settings.high_security:
            return server_settings

        # Remove top-level 'high_security' setting. This will only exist
        # if it had been enabled server side.

        if "high_security" in server_settings:
            del server_settings["high_security"]

        # Remove individual security settings from top level of configuration
        # settings.

        for setting in cls.SECURITY_SETTINGS:
            if setting in server_settings:
                del server_settings[setting]

        # When server side configuration is disabled, there will be no
        # agent_config value in server_settings, so no more fix-ups
        # are required.

        if "agent_config" not in server_settings:
            return server_settings

        # Remove individual security settings from agent server side
        # configuration settings.

        agent_config = server_settings["agent_config"]

        for setting in cls.SECURITY_SETTINGS:
            if setting in agent_config:
                del server_settings["agent_config"][setting]

                _logger.info(
                    "Ignoring server side configuration setting for "
                    "%r, because High Security Mode has been activated. "
                    "Using local setting %s=%r.",
                    setting,
                    setting,
                    fetch_config_setting(local_settings, setting),
                )

        return server_settings

    @classmethod
    def connect(
        cls,
        app_name,
        linked_applications,
        environment,
        settings,
        client_cls=ApplicationModeClient,
    ):
        with cls(settings, client_cls=client_cls) as preconnect:
            redirect_host = preconnect.send("preconnect")["redirect_host"]

        with cls(settings, host=redirect_host, client_cls=client_cls) as protocol:
            configuration = protocol.send(
                "connect",
                cls._connect_payload(app_name, linked_applications, environment, settings),
            )

        # Apply High Security Mode to server_config, so the local
        # security settings won't get overwritten when we overlay
        # the server settings on top of them.

        configuration = cls._apply_high_security_mode_fixups(configuration, settings)

        # The agent configuration for the application in constructed
        # by taking a snapshot of the locally constructed
        # configuration and overlaying it with that from the server,
        # as well as creating the attribute filter.
        settings = finalize_application_settings(configuration, settings)

        with cls(settings, host=redirect_host, client_cls=client_cls) as protocol:
            protocol.send("agent_settings", (global_settings_dump(settings, serializable=True),))

        if "messages" in configuration:
            for item in configuration["messages"]:
                message = item["message"]
                level = item["level"]
                logger_func = cls.LOGGER_FUNC_MAPPING.get(level, None)
                if logger_func:
                    logger_func("%s", message)

        return protocol

    def finalize(self):
        return self.client.finalize()


class ServerlessModeProtocol(AgentProtocol):
    def __init__(self, settings, host=None, client_cls=ServerlessModeClient):
        super(ServerlessModeProtocol, self).__init__(settings, host=host, client_cls=client_cls)
        self._metadata = {
            "protocol_version": self.VERSION,
            "execution_environment": os.environ.get("AWS_EXECUTION_ENV", None),
            "agent_version": version,
        }

    def finalize(self):
        for key in self.configuration.aws_lambda_metadata:
            if key not in self._metadata:
                self._metadata[key] = self.configuration.aws_lambda_metadata[key]

        data = self.client.finalize()

        payload = {
            "metadata": self._metadata,
            "data": data,
        }

        encoded = serverless_payload_encode(payload)
        payload = json_encode((1, "NR_LAMBDA_MONITORING", encoded))

        print(payload)

        return payload

    @classmethod
    def connect(
        cls,
        app_name,
        linked_applications,
        environment,
        settings,
        client_cls=ServerlessModeClient,
    ):
        aws_lambda_metadata = settings.aws_lambda_metadata
        settings = finalize_application_settings({"cross_application_tracer.enabled": False}, settings)
        # Metadata must come from the original settings object since it
        # can be modified later
        settings.aws_lambda_metadata = aws_lambda_metadata
        return cls(settings, client_cls=client_cls)

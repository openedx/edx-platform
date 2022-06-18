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

""" This module provides a structure to hang the configuration settings. We
use an empty class structure and manually populate it. The global defaults
will be overlaid with any settings from the local agent configuration file.
For a specific application we will then deep copy the global default
settings and then overlay that with application settings obtained from the
server side core application. Finally, to allow for local testing and
debugging, for selected override configuration settings, we will apply back
the global defaults or those from local agent configuration.

"""

import copy
import logging
import os
import re
import threading

import newrelic.packages.six as six
from newrelic.common.object_names import parse_exc_info
from newrelic.core.attribute_filter import AttributeFilter

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

try:
    import grpc

    from newrelic.core.infinite_tracing_pb2 import (  # pylint: disable=W0611,C0412  # noqa: F401
        Span,
    )
except ImportError:
    grpc = None


# By default, Transaction Events and Custom Events have the same size
# reservoir. Error Events have a different default size.

DEFAULT_RESERVOIR_SIZE = 1200
ERROR_EVENT_RESERVOIR_SIZE = 100
SPAN_EVENT_RESERVOIR_SIZE = 2000

# settings that should be completely ignored if set server side
IGNORED_SERVER_SIDE_SETTINGS = [
    "utilization.logical_processors",
    "utilization.total_ram_mib",
    "utilization.billing_hostname",
]


class _NullHandler(logging.Handler):
    def emit(self, record):
        pass


_logger = logging.getLogger(__name__)
_logger.addHandler(_NullHandler())


# The Settings objects and the global default settings. We create a
# distinct type for each sub category of settings that the agent knows
# about so that an error when accessing a non-existent setting is more
# descriptive and identifies the category of settings. When applying
# server side configuration we create normal Settings object for new
# sub categories we don't know about.


class Settings(object):
    nested = False

    def __repr__(self):
        return repr(self.__dict__)

    def __iter__(self):
        return iter(flatten_settings(self).items())

    def __contains__(self, item):
        return hasattr(self, item)


def create_settings(nested):
    return type("Settings", (Settings,), {"nested": nested})()


class TopLevelSettings(Settings):
    _host = None

    @property
    def host(self):
        if self._host:
            return self._host
        return default_host(self.license_key)

    @host.setter
    def host(self, value):
        self._host = value


class AttributesSettings(Settings):
    pass


class GCRuntimeMetricsSettings(Settings):
    enabled = False


class ThreadProfilerSettings(Settings):
    pass


class TransactionTracerSettings(Settings):
    pass


class TransactionTracerAttributesSettings(Settings):
    pass


class ErrorCollectorSettings(Settings):
    pass


class ErrorCollectorAttributesSettings(Settings):
    pass


class BrowserMonitorSettings(Settings):
    pass


class BrowserMonitorAttributesSettings(Settings):
    pass


class TransactionNameSettings(Settings):
    pass


class TransactionMetricsSettings(Settings):
    pass


class RumSettings(Settings):
    pass


class SlowSqlSettings(Settings):
    pass


class AgentLimitsSettings(Settings):
    pass


class ConsoleSettings(Settings):
    pass


class DebugSettings(Settings):
    pass


class CrossApplicationTracerSettings(Settings):
    pass


class TransactionEventsSettings(Settings):
    pass


class TransactionEventsAttributesSettings(Settings):
    pass


class CustomInsightsEventsSettings(Settings):
    pass


class ProcessHostSettings(Settings):
    pass


class SyntheticsSettings(Settings):
    pass


class MessageTracerSettings(Settings):
    pass


class UtilizationSettings(Settings):
    pass


class StripExceptionMessageSettings(Settings):
    pass


class DatastoreTracerSettings(Settings):
    pass


class DatastoreTracerInstanceReportingSettings(Settings):
    pass


class DatastoreTracerDatabaseNameReportingSettings(Settings):
    pass


class HerokuSettings(Settings):
    pass


class SpanEventSettings(Settings):
    pass


class SpanEventAttributesSettings(Settings):
    pass


class DistributedTracingSettings(Settings):
    pass


class ServerlessModeSettings(Settings):
    pass


class TransactionSegmentSettings(Settings):
    pass


class TransactionSegmentAttributesSettings(Settings):
    pass


class EventLoopVisibilitySettings(Settings):
    pass


class InfiniteTracingSettings(Settings):
    _trace_observer_host = None

    @property
    def enabled(self):
        return bool(self._trace_observer_host)

    @property
    def trace_observer_host(self):
        return self._trace_observer_host

    @trace_observer_host.setter
    def trace_observer_host(self, value):
        if value and self._can_enable_infinite_tracing():
            self._trace_observer_host = self._normalize_host(value)
        else:
            self._trace_observer_host = None

    @staticmethod
    def _normalize_host(value):
        u = urlparse.urlparse(value)
        if u.hostname:
            _logger.warning(
                "An invalid host (%s) was configured for infinite tracing. "
                "A host of %s has been extracted by interpreting the "
                "configuration value as a URL. An update to the configuration "
                "value is recommended.",
                value,
                u.hostname,
            )
            return u.hostname
        elif "/" in value or ":" in value:
            _logger.error(
                "An invalid host (%s) was configured for infinite tracing. "
                "Please verify that only the host name was supplied via the "
                "infinite tracing configuration. "
                "Falling back to infinite tracing disabled.",
                value,
            )
            return None

        return value

    @staticmethod
    def _can_enable_infinite_tracing():
        if grpc is None:
            _logger.error(
                "Unable to import libraries required for infinite tracing. "
                "Please run pip install newrelic[infinite-tracing] "
                "to install required dependencies. "
                "Falling back to infinite tracing disabled."
            )
            return False

        return True


class EventHarvestConfigSettings(Settings):
    nested = True
    _lock = threading.Lock()

    @property
    def report_period_ms(self):
        with self._lock:
            return vars(_settings.event_harvest_config).get("report_period_ms", 60 * 1000)

    @report_period_ms.setter
    def report_period_ms(self, value):
        with self._lock:
            vars(_settings.event_harvest_config)["report_period_ms"] = value
            vars(self)["report_period_ms"] = value


class EventHarvestConfigHarvestLimitSettings(Settings):
    nested = True


_settings = TopLevelSettings()
_settings.attributes = AttributesSettings()
_settings.gc_runtime_metrics = GCRuntimeMetricsSettings()
_settings.thread_profiler = ThreadProfilerSettings()
_settings.transaction_tracer = TransactionTracerSettings()
_settings.transaction_tracer.attributes = TransactionTracerAttributesSettings()
_settings.error_collector = ErrorCollectorSettings()
_settings.error_collector.attributes = ErrorCollectorAttributesSettings()
_settings.browser_monitoring = BrowserMonitorSettings()
_settings.browser_monitoring.attributes = BrowserMonitorAttributesSettings()
_settings.transaction_name = TransactionNameSettings()
_settings.transaction_metrics = TransactionMetricsSettings()
_settings.event_loop_visibility = EventLoopVisibilitySettings()
_settings.rum = RumSettings()
_settings.slow_sql = SlowSqlSettings()
_settings.agent_limits = AgentLimitsSettings()
_settings.console = ConsoleSettings()
_settings.debug = DebugSettings()
_settings.cross_application_tracer = CrossApplicationTracerSettings()
_settings.transaction_events = TransactionEventsSettings()
_settings.transaction_events.attributes = TransactionEventsAttributesSettings()
_settings.custom_insights_events = CustomInsightsEventsSettings()
_settings.process_host = ProcessHostSettings()
_settings.synthetics = SyntheticsSettings()
_settings.message_tracer = MessageTracerSettings()
_settings.utilization = UtilizationSettings()
_settings.strip_exception_messages = StripExceptionMessageSettings()
_settings.datastore_tracer = DatastoreTracerSettings()
_settings.datastore_tracer.instance_reporting = DatastoreTracerInstanceReportingSettings()
_settings.datastore_tracer.database_name_reporting = DatastoreTracerDatabaseNameReportingSettings()
_settings.heroku = HerokuSettings()
_settings.span_events = SpanEventSettings()
_settings.span_events.attributes = SpanEventAttributesSettings()
_settings.transaction_segments = TransactionSegmentSettings()
_settings.transaction_segments.attributes = TransactionSegmentAttributesSettings()
_settings.distributed_tracing = DistributedTracingSettings()
_settings.serverless_mode = ServerlessModeSettings()
_settings.infinite_tracing = InfiniteTracingSettings()
_settings.event_harvest_config = EventHarvestConfigSettings()
_settings.event_harvest_config.harvest_limits = EventHarvestConfigHarvestLimitSettings()


_settings.log_file = os.environ.get("NEW_RELIC_LOG", None)
_settings.audit_log_file = os.environ.get("NEW_RELIC_AUDIT_LOG", None)


def _environ_as_int(name, default=0):
    val = os.environ.get(name, default)
    try:
        return int(val)
    except ValueError:
        return default


def _environ_as_float(name, default=0.0):
    val = os.environ.get(name, default)

    try:
        return float(val)
    except ValueError:
        return default


def _environ_as_bool(name, default=False):
    flag = os.environ.get(name, default)
    if default is None or default:
        try:
            flag = not flag.lower() in ["off", "false", "0"]
        except AttributeError:
            pass
    else:
        try:
            flag = flag.lower() in ["on", "true", "1"]
        except AttributeError:
            pass
    return flag


def _environ_as_set(name, default=""):
    value = os.environ.get(name, default)
    return set(value.split())


def _environ_as_mapping(name, default=""):
    result = []
    items = os.environ.get(name, default)

    # Strip all whitespace and semicolons from the end of the string.
    # That way, when we split a valid labels string by ';', the resulting
    # list will contain no empty elements. When we loop through the
    # elements, if we see one that is empty, or can't be split by ':',
    # then we know the string has an invalid format.

    items = items.strip("; \t\n\r\f\v")

    if not items:
        return result

    for item in items.split(";"):

        try:
            key, value = item.split(":")
        except ValueError:
            _logger.warning(
                "Invalid configuration. Cannot parse: %r. Expected format 'key1:value1;key2:value2 ... '.", items
            )
            result = []
            break

        key = key.strip()
        value = value.strip()

        if key and value:
            result.append((key, value))
        else:
            _logger.warning(
                "Invalid configuration. Cannot parse: %r. Expected format 'key1:value1;key2:value2 ... '.", items
            )
            result = []
            break

    return result


def _parse_status_codes(value, target):
    items = value.split()
    for item in items:
        try:
            negate = item.startswith("!")
            if negate:
                item = item[1:]

            start, end = item.split("-")

            values = set(range(int(start), int(end) + 1))

            if negate:
                target.difference_update(values)
            else:
                target.update(values)

        except ValueError:
            if negate:
                target.discard(int(item))
            else:
                target.add(int(item))
    return target


def _parse_attributes(s):
    valid = []
    for item in s.split():
        if "*" not in item[:-1] and len(item.encode("utf-8")) < 256:
            valid.append(item)
        else:
            _logger.warning("Improperly formatted attribute: %r", item)
    return valid


def default_host(license_key):
    if not license_key:
        return "collector.newrelic.com"

    region_aware_match = re.match("^(.+?)x", license_key)
    if not region_aware_match:
        return "collector.newrelic.com"

    region = region_aware_match.group(1)
    host = "collector." + region + ".nr-data.net"
    return host


_LOG_LEVEL = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}

_settings.enabled = _environ_as_bool("NEW_RELIC_ENABLED", False)

_settings.feature_flag = _environ_as_set("NEW_RELIC_FEATURE_FLAG", "")

_settings.log_level = os.environ.get("NEW_RELIC_LOG_LEVEL", "INFO").upper()

if _settings.log_level in _LOG_LEVEL:
    _settings.log_level = _LOG_LEVEL[_settings.log_level]
else:
    _settings.log_level = logging.INFO

_settings.license_key = os.environ.get("NEW_RELIC_LICENSE_KEY", None)
_settings.api_key = os.environ.get("NEW_RELIC_API_KEY", None)

_settings.ssl = _environ_as_bool("NEW_RELIC_SSL", True)

_settings.host = os.environ.get("NEW_RELIC_HOST")
_settings.port = int(os.environ.get("NEW_RELIC_PORT", "0"))

_settings.agent_run_id = None
_settings.entity_guid = None
_settings.request_headers_map = {}

_settings.proxy_scheme = os.environ.get("NEW_RELIC_PROXY_SCHEME", None)
_settings.proxy_host = os.environ.get("NEW_RELIC_PROXY_HOST", None)
_settings.proxy_port = int(os.environ.get("NEW_RELIC_PROXY_PORT", "0"))
_settings.proxy_user = os.environ.get("NEW_RELIC_PROXY_USER", None)
_settings.proxy_pass = os.environ.get("NEW_RELIC_PROXY_PASS", None)

_settings.ca_bundle_path = os.environ.get("NEW_RELIC_CA_BUNDLE_PATH", None)

_settings.app_name = os.environ.get("NEW_RELIC_APP_NAME", "Python Application")
_settings.linked_applications = []

_settings.process_host.display_name = os.environ.get("NEW_RELIC_PROCESS_HOST_DISPLAY_NAME", None)

_settings.labels = _environ_as_mapping("NEW_RELIC_LABELS", "")

_settings.monitor_mode = _environ_as_bool("NEW_RELIC_MONITOR_MODE", True)

_settings.developer_mode = _environ_as_bool("NEW_RELIC_DEVELOPER_MODE", False)

_settings.high_security = _environ_as_bool("NEW_RELIC_HIGH_SECURITY", False)

_settings.attribute_filter = None

_settings.collect_errors = True
_settings.collect_error_events = True
_settings.collect_traces = True
_settings.collect_span_events = True
_settings.collect_analytics_events = True
_settings.collect_custom_events = True

_settings.apdex_t = _environ_as_float("NEW_RELIC_APDEX_T", 0.5)
_settings.web_transactions_apdex = {}

_settings.capture_params = None
_settings.ignored_params = []

_settings.capture_environ = True
_settings.include_environ = [
    "REQUEST_METHOD",
    "HTTP_USER_AGENT",
    "HTTP_REFERER",
    "CONTENT_TYPE",
    "CONTENT_LENGTH",
    "HTTP_HOST",
    "HTTP_ACCEPT",
]

_settings.max_stack_trace_lines = 50

_settings.sampling_rate = 0

_settings.startup_timeout = float(os.environ.get("NEW_RELIC_STARTUP_TIMEOUT", "0.0"))
_settings.shutdown_timeout = float(os.environ.get("NEW_RELIC_SHUTDOWN_TIMEOUT", "2.5"))

_settings.beacon = None
_settings.error_beacon = None
_settings.application_id = None
_settings.browser_key = None
_settings.episodes_url = None
_settings.js_agent_loader = None
_settings.js_agent_file = None

_settings.url_rules = []
_settings.metric_name_rules = []
_settings.transaction_name_rules = []
_settings.transaction_segment_terms = []

_settings.account_id = os.environ.get("NEW_RELIC_ACCOUNT_ID")
_settings.cross_process_id = None
_settings.primary_application_id = os.environ.get("NEW_RELIC_PRIMARY_APPLICATION_ID", "Unknown")
_settings.trusted_account_ids = []
_settings.trusted_account_key = os.environ.get("NEW_RELIC_TRUSTED_ACCOUNT_KEY")
_settings.encoding_key = None
_settings.sampling_target = 10
_settings.sampling_target_period_in_seconds = 60

_settings.compressed_content_encoding = "gzip"
_settings.max_payload_size_in_bytes = 1000000

_settings.attributes.enabled = True
_settings.attributes.exclude = []
_settings.attributes.include = []

_settings.thread_profiler.enabled = True
_settings.cross_application_tracer.enabled = False

_settings.gc_runtime_metrics.enabled = False
_settings.gc_runtime_metrics.top_object_count_limit = 5

_settings.transaction_events.enabled = True
_settings.transaction_events.attributes.enabled = True
_settings.transaction_events.attributes.exclude = []
_settings.transaction_events.attributes.include = []

_settings.custom_insights_events.enabled = True

_settings.distributed_tracing.enabled = _environ_as_bool("NEW_RELIC_DISTRIBUTED_TRACING_ENABLED", default=True)
_settings.distributed_tracing.exclude_newrelic_header = False
_settings.span_events.enabled = _environ_as_bool("NEW_RELIC_SPAN_EVENTS_ENABLED", default=True)
_settings.span_events.attributes.enabled = True
_settings.span_events.attributes.exclude = []
_settings.span_events.attributes.include = []

_settings.transaction_segments.attributes.enabled = True
_settings.transaction_segments.attributes.exclude = []
_settings.transaction_segments.attributes.include = []

_settings.transaction_tracer.enabled = True
_settings.transaction_tracer.transaction_threshold = None
_settings.transaction_tracer.record_sql = "obfuscated"
_settings.transaction_tracer.stack_trace_threshold = 0.5
_settings.transaction_tracer.explain_enabled = True
_settings.transaction_tracer.explain_threshold = 0.5
_settings.transaction_tracer.function_trace = []
_settings.transaction_tracer.generator_trace = []
_settings.transaction_tracer.top_n = 20
_settings.transaction_tracer.attributes.enabled = True
_settings.transaction_tracer.attributes.exclude = []
_settings.transaction_tracer.attributes.include = []

_settings.error_collector.enabled = True
_settings.error_collector.capture_events = True
_settings.error_collector.capture_source = False
_settings.error_collector.ignore_classes = []
_settings.error_collector.ignore_status_codes = _parse_status_codes("100-102 200-208 226 300-308 404", set())
_settings.error_collector.expected_classes = []
_settings.error_collector.expected_status_codes = set()
_settings.error_collector.attributes.enabled = True
_settings.error_collector.attributes.exclude = []
_settings.error_collector.attributes.include = []

_settings.browser_monitoring.enabled = True
_settings.browser_monitoring.auto_instrument = True
_settings.browser_monitoring.loader = "rum"  # Valid values: 'full', 'none'
_settings.browser_monitoring.loader_version = None
_settings.browser_monitoring.debug = False
_settings.browser_monitoring.ssl_for_http = None
_settings.browser_monitoring.content_type = ["text/html"]
_settings.browser_monitoring.attributes.enabled = False
_settings.browser_monitoring.attributes.exclude = []
_settings.browser_monitoring.attributes.include = []

_settings.transaction_name.limit = None
_settings.transaction_name.naming_scheme = os.environ.get("NEW_RELIC_TRANSACTION_NAMING_SCHEME")

_settings.slow_sql.enabled = True

_settings.synthetics.enabled = True

_settings.agent_limits.data_collector_timeout = 30.0
_settings.agent_limits.transaction_traces_nodes = 2000
_settings.agent_limits.sql_query_length_maximum = 16384
_settings.agent_limits.slow_sql_stack_trace = 30
_settings.agent_limits.max_sql_connections = 4
_settings.agent_limits.sql_explain_plans = 30
_settings.agent_limits.sql_explain_plans_per_harvest = 60
_settings.agent_limits.slow_sql_data = 10
_settings.agent_limits.merge_stats_maximum = None
_settings.agent_limits.errors_per_transaction = 5
_settings.agent_limits.errors_per_harvest = 20
_settings.agent_limits.slow_transaction_dry_harvests = 5
_settings.agent_limits.thread_profiler_nodes = 20000
_settings.agent_limits.synthetics_events = 200
_settings.agent_limits.synthetics_transactions = 20
_settings.agent_limits.data_compression_threshold = 64 * 1024
_settings.agent_limits.data_compression_level = None

_settings.infinite_tracing.trace_observer_host = os.environ.get("NEW_RELIC_INFINITE_TRACING_TRACE_OBSERVER_HOST", None)
_settings.infinite_tracing.trace_observer_port = _environ_as_int("NEW_RELIC_INFINITE_TRACING_TRACE_OBSERVER_PORT", 443)
_settings.infinite_tracing.ssl = True
_settings.infinite_tracing.span_queue_size = _environ_as_int("NEW_RELIC_INFINITE_TRACING_SPAN_QUEUE_SIZE", 10000)

_settings.event_harvest_config.harvest_limits.analytic_event_data = _environ_as_int(
    "NEW_RELIC_ANALYTICS_EVENTS_MAX_SAMPLES_STORED", DEFAULT_RESERVOIR_SIZE
)

_settings.event_harvest_config.harvest_limits.custom_event_data = _environ_as_int(
    "NEW_RELIC_CUSTOM_INSIGHTS_EVENTS_MAX_SAMPLES_STORED", DEFAULT_RESERVOIR_SIZE
)

_settings.event_harvest_config.harvest_limits.span_event_data = _environ_as_int(
    "NEW_RELIC_SPAN_EVENTS_MAX_SAMPLES_STORED", SPAN_EVENT_RESERVOIR_SIZE
)

_settings.event_harvest_config.harvest_limits.error_event_data = _environ_as_int(
    "NEW_RELIC_ERROR_COLLECTOR_MAX_EVENT_SAMPLES_STORED", ERROR_EVENT_RESERVOIR_SIZE
)

_settings.console.listener_socket = None
_settings.console.allow_interpreter_cmd = False

_settings.debug.ignore_all_server_settings = False
_settings.debug.local_settings_overrides = []

_settings.debug.disable_api_supportability_metrics = False
_settings.debug.log_agent_initialization = False
_settings.debug.log_data_collector_calls = False
_settings.debug.log_data_collector_payloads = False
_settings.debug.log_malformed_json_data = False
_settings.debug.log_transaction_trace_payload = False
_settings.debug.log_thread_profile_payload = False
_settings.debug.log_normalization_rules = False
_settings.debug.log_raw_metric_data = False
_settings.debug.log_normalized_metric_data = False
_settings.debug.log_explain_plan_queries = False
_settings.debug.log_autorum_middleware = False
_settings.debug.record_transaction_failure = False
_settings.debug.enable_coroutine_profiling = False
_settings.debug.explain_plan_obfuscation = "simple"
_settings.debug.disable_certificate_validation = False
_settings.debug.log_untrusted_distributed_trace_keys = False
_settings.debug.disable_harvest_until_shutdown = False
_settings.debug.connect_span_stream_in_developer_mode = False

_settings.message_tracer.segment_parameters_enabled = True

_settings.utilization.detect_aws = True
_settings.utilization.detect_azure = True
_settings.utilization.detect_docker = True
_settings.utilization.detect_kubernetes = True
_settings.utilization.detect_gcp = True
_settings.utilization.detect_pcf = True

_settings.utilization.logical_processors = _environ_as_int("NEW_RELIC_UTILIZATION_LOGICAL_PROCESSORS")
_settings.utilization.total_ram_mib = _environ_as_int("NEW_RELIC_UTILIZATION_TOTAL_RAM_MIB")
_settings.utilization.billing_hostname = os.environ.get("NEW_RELIC_UTILIZATION_BILLING_HOSTNAME")

_settings.strip_exception_messages.enabled = False
_settings.strip_exception_messages.whitelist = []

_settings.datastore_tracer.instance_reporting.enabled = True
_settings.datastore_tracer.database_name_reporting.enabled = True

_settings.heroku.use_dyno_names = _environ_as_bool("NEW_RELIC_HEROKU_USE_DYNO_NAMES", default=True)
_settings.heroku.dyno_name_prefixes_to_shorten = list(
    _environ_as_set("NEW_RELIC_HEROKU_DYNO_NAME_PREFIXES_TO_SHORTEN", "scheduler run")
)

_settings.serverless_mode.enabled = _environ_as_bool("NEW_RELIC_SERVERLESS_MODE_ENABLED", default=False)
_settings.aws_lambda_metadata = {}

_settings.event_loop_visibility.enabled = True
_settings.event_loop_visibility.blocking_threshold = 0.1


def global_settings():
    """This returns the default global settings. Generally only used
    directly in test scripts and test harnesses or when applying global
    settings from agent configuration file. Making changes to the settings
    object returned by this function will not have any effect on any
    applications that have already been initialised. This is because when
    the settings are obtained from the core application a snapshot of these
    settings will be taken.

    >>> global_settings = global_settings()
    >>> global_settings.browser_monitoring.auto_instrument = True
    >>> global_settings.browser_monitoring.auto_instrument
    True

    """

    return _settings


def flatten_settings(settings):
    """This returns dictionary of settings flattened into a single
    key namespace or a nested hierarchy according to the settings object.

    """

    def _flatten(settings, o, name=None):
        for key, value in vars(o).items():
            # Remove any leading underscores on keys accessed through
            # properties for reporting.
            if key.startswith("_"):
                key = key[1:]

            if name:
                key = "%s.%s" % (name, key)

            if isinstance(value, Settings):
                if value.nested:
                    _settings = settings[key] = {}
                    _flatten(_settings, value)
                else:
                    _flatten(settings, value, key)
            else:
                settings[key] = value

    flattened = {}
    _flatten(flattened, settings)
    return flattened


def create_obfuscated_netloc(username, password, hostname, mask):
    """Create a netloc string from hostname, username and password. If the
    username and/or password is present, replace them with the obfuscation
    mask. Otherwise, leave them out of netloc.

    """

    if username:
        username = mask

    if password:
        password = mask

    if username and password:
        netloc = "%s:%s@%s" % (username, password, hostname)
    elif username:
        netloc = "%s@%s" % (username, hostname)
    else:
        netloc = hostname

    return netloc


def global_settings_dump(settings_object=None, serializable=False):
    """This returns dictionary of global settings flattened into a single
    key namespace rather than nested hierarchy. This is used to send the
    global settings configuration back to core application.

    """

    if settings_object is None:
        settings_object = _settings

    settings = flatten_settings(settings_object)

    # Strip out any sensitive settings.
    # The license key is being sent already, but no point sending
    # it again.

    del settings["license_key"]
    del settings["api_key"]
    del settings["encoding_key"]
    del settings["js_agent_loader"]
    del settings["js_agent_file"]

    # If proxy credentials are included in the settings, we obfuscate
    # them before sending, rather than deleting.

    obfuscated = "****"

    if settings["proxy_user"] is not None:
        settings["proxy_user"] = obfuscated

    if settings["proxy_pass"] is not None:
        settings["proxy_pass"] = obfuscated

    # For the case of proxy_host we have to do a bit more work as it
    # could be a URI which includes the username and password within
    # it. What we do here is parse the value and if identified as a
    # URI, we recompose it with the obfuscated username and password.

    proxy_host = settings["proxy_host"]

    if proxy_host:
        components = urlparse.urlparse(proxy_host)

        if components.scheme:

            netloc = create_obfuscated_netloc(components.username, components.password, components.hostname, obfuscated)

            if components.port:
                uri = "%s://%s:%s%s" % (components.scheme, netloc, components.port, components.path)
            else:
                uri = "%s://%s%s" % (components.scheme, netloc, components.path)

            settings["proxy_host"] = uri

    if serializable:
        for key, value in list(six.iteritems(settings)):
            if not isinstance(key, six.string_types):
                del settings[key]

            if (
                not isinstance(value, six.string_types)
                and not isinstance(value, float)
                and not isinstance(value, six.integer_types)
            ):
                settings[key] = repr(value)

    return settings


# Creation of an application settings object from global default settings
# and any server side configuration settings.


def apply_config_setting(settings_object, name, value, nested=False):
    """Apply a setting to the settings object where name is a dotted path.
    If there is no pre existing settings object for a sub category then
    one will be created and added automatically.

    >>> name = 'browser_monitoring.auto_instrument'
    >>> value = True
    >>>
    >>> global_settings = global_settings()
    >>> apply_config_setting(global_settings, name, value)

    """

    target = settings_object
    fields = name.split(".", 1)

    while len(fields) > 1:
        if not hasattr(target, fields[0]):
            setattr(target, fields[0], create_settings(nested))
        nested = False
        target = getattr(target, fields[0])
        fields = fields[1].split(".", 1)

    default_value = getattr(target, fields[0], None)
    if isinstance(value, dict) and value and not isinstance(default_value, dict):
        for k, v in value.items():
            k_name = "{}.{}".format(fields[0], k)
            apply_config_setting(target, k_name, v, nested=True)
    else:
        setattr(target, fields[0], value)


def fetch_config_setting(settings_object, name):
    """Fetch a setting from the settings object where name is a dotted path.

    >>> name = 'browser_monitoring.auto_instrument'
    >>>
    >>> global_settings = global_settings()
    >>> global_settings.browser_monitoring.auto_instrument = True
    >>> fetch_config_setting(global_settings, name)
    True

    """

    target = settings_object
    fields = name.split(".", 1)

    target = getattr(target, fields[0])

    while len(fields) > 1:
        fields = fields[1].split(".", 1)
        target = getattr(target, fields[0])

    return target


def apply_server_side_settings(server_side_config=None, settings=_settings):
    """Create a snapshot of the global default settings and overlay it
    with any server side configuration settings. Any local settings
    overrides to take precedence over server side configuration settings
    will then be reapplied to the copy. Note that the intention is that
    the resulting settings object will be cached for subsequent use
    within the application object the settings pertain to.

    >>> server_config = {'browser_monitoring.auto_instrument': True}
    >>>
    >>> settings_snapshot = apply_server_side_settings(server_config)

    """
    server_side_config = server_side_config if server_side_config is not None else {}

    settings_snapshot = copy.deepcopy(settings)

    # Break out the server side agent config settings which
    # are stored under 'agent_config' key.

    agent_config = server_side_config.pop("agent_config", {})

    # Remap as necessary any server side agent config settings.

    if "transaction_tracer.transaction_threshold" in agent_config:
        value = agent_config["transaction_tracer.transaction_threshold"]
        if value == "apdex_f":
            agent_config["transaction_tracer.transaction_threshold"] = None

    # If ignore_errors exists, and either ignore_classes is not set or it is empty
    if "error_collector.ignore_errors" in agent_config and (
        "error_collector.ignore_classes" not in agent_config or not agent_config["error_collector.ignore_classes"]
    ):
        # Remap to newer config key
        agent_config["error_collector.ignore_classes"] = agent_config.pop("error_collector.ignore_errors")

    # Overlay with agent server side configuration settings.

    for (name, value) in agent_config.items():
        apply_config_setting(settings_snapshot, name, value)

    # Overlay with global server side configuration settings.
    # global server side configuration always takes precedence over the global
    # server side configuration settings.

    for (name, value) in server_side_config.items():
        apply_config_setting(settings_snapshot, name, value)

    event_harvest_config = server_side_config.get("event_harvest_config", {})
    harvest_limits = event_harvest_config.get("harvest_limits", ())
    apply_config_setting(settings_snapshot, "event_harvest_config.whitelist", frozenset(harvest_limits))

    # Override span event harvest config
    span_event_harvest_config = server_side_config.get("span_event_harvest_config", {})
    span_event_harvest_limit = span_event_harvest_config.get("harvest_limit", None)
    if span_event_harvest_limit is not None:
        apply_config_setting(
            settings_snapshot, "event_harvest_config.harvest_limits.span_event_data", span_event_harvest_limit
        )

    # This will be removed at some future point
    # Special case for account_id which will be sent instead of
    # cross_process_id in the future

    if settings_snapshot.cross_process_id is not None:
        vals = [settings_snapshot.account_id, settings_snapshot.application_id]
        derived_vals = settings_snapshot.cross_process_id.split("#")

        if len(derived_vals) == 2:
            for idx, val in enumerate(derived_vals):
                # only override the value if the server side does not provide
                # the value specifically
                if vals[idx] is None:
                    vals[idx] = derived_vals[idx]

            settings_snapshot.account_id = vals[0]
            settings_snapshot.application_id = vals[1]

    # Reapply on top any local setting overrides.

    for name in _settings.debug.local_settings_overrides:
        value = fetch_config_setting(_settings, name)
        apply_config_setting(settings_snapshot, name, value)

    return settings_snapshot


def finalize_application_settings(server_side_config=None, settings=_settings):
    """Overlay server-side settings and add attribute filter."""
    server_side_config = server_side_config if server_side_config is not None else {}

    # Remove values from server_config that should not overwrite the
    # ones set locally
    server_side_config = _remove_ignored_configs(server_side_config)

    application_settings = apply_server_side_settings(server_side_config, settings)

    application_settings.attribute_filter = AttributeFilter(flatten_settings(application_settings))

    return application_settings


def _remove_ignored_configs(server_settings):
    if not server_settings.get("agent_config"):
        return server_settings

    # These settings should be ignored completely
    for ignored_setting in IGNORED_SERVER_SIDE_SETTINGS:
        server_settings["agent_config"].pop(ignored_setting, None)

    return server_settings


def ignore_status_code(status):
    """Legacy function kept here for compatibility."""
    return status in _settings.error_collector.ignore_status_codes


def is_expected_error(
    exc_info,
    status_code=None,
    settings=None,
):
    """Check if an error is expected based on rules matching. Default is False when settings lookup fails."""
    return error_matches_rules(
        "expected",
        exc_info,
        status_code=status_code,
        settings=settings,
    )


def should_ignore_error(
    exc_info,
    status_code=None,
    settings=None,
):
    """Check if an error should be ignored based on rules matching. Default is True when settings lookup fails."""
    return error_matches_rules(
        "ignore",
        exc_info,
        status_code=status_code,
        settings=settings,
    )


def error_matches_rules(
    rules_prefix,
    exc_info,
    status_code=None,
    settings=None,
):
    """
    Attempt to match exception to rules based on prefix.

    rules_prefix is one of [ignore, expected]
    exc_info is an exception tuple of (exc, val, tb)
    status_code is an optional value or callable taking in exc_info that returns an int-like object
    origin is either the current application or trace.
    """
    # Delay imports to prevent lockups
    from newrelic.core.trace_cache import trace_cache

    if not settings:
        # Pull from current transaction if no settings provided
        tc = trace_cache()
        transaction = tc.current_transaction()
        settings = transaction and transaction.settings

        if not settings:
            # Pull from active trace if no settings on transaction
            trace = tc.current_trace()
            settings = trace and trace.settings

            if not settings:
                # Unable to find rules to match with
                _logger.debug(
                    "Failed to retrieve exception rules: No settings supplied, or found on transaction or trace."
                )
                return None

    # Retrieve settings based on prefix
    classes_rules = getattr(settings.error_collector, "%s_classes" % rules_prefix, set())
    status_codes_rules = getattr(settings.error_collector, "%s_status_codes" % rules_prefix, set())

    _, _, fullnames, _ = parse_exc_info(exc_info)
    fullname = fullnames[0]

    # Check class names
    for fullname in fullnames:
        if fullname in classes_rules:
            return True

    # Check status_code
    # For callables, call on exc_info to retrieve status_code.
    # It's possible to return None, in which case no code is evaluated.
    if callable(status_code):
        status_code = status_code(*exc_info)

    # Match status_code if it exists
    if status_code is not None:
        try:
            # Coerce into integer
            status_code = int(status_code)
        except:
            _logger.error("Failed to coerce status code into integer. status_code: %s" % str(status_code))
        else:
            if status_code in status_codes_rules:
                return True

    return False

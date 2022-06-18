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

import fnmatch
import logging
import os
import sys
import traceback

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

import newrelic.api.application
import newrelic.api.background_task
import newrelic.api.database_trace
import newrelic.api.error_trace
import newrelic.api.exceptions
import newrelic.api.external_trace
import newrelic.api.function_profile
import newrelic.api.function_trace
import newrelic.api.generator_trace
import newrelic.api.import_hook
import newrelic.api.memcache_trace
import newrelic.api.object_wrapper
import newrelic.api.profile_trace
import newrelic.api.settings
import newrelic.api.transaction_name
import newrelic.api.wsgi_application
import newrelic.console
import newrelic.core.agent
import newrelic.core.config
import newrelic.core.trace_cache as trace_cache
from newrelic.common.log_file import initialize_logging
from newrelic.common.object_names import expand_builtin_exception_name
from newrelic.core.config import (
    Settings,
    apply_config_setting,
    default_host,
    fetch_config_setting,
)
from newrelic.packages import six

__all__ = ["initialize", "filter_app_factory"]

_logger = logging.getLogger(__name__)

# Register our importer which implements post import hooks for
# triggering of callbacks to monkey patch modules before import
# returns them to caller.

sys.meta_path.insert(0, newrelic.api.import_hook.ImportHookFinder())

# The set of valid feature flags that the agent currently uses.
# This will be used to validate what is provided and issue warnings
# if feature flags not in set are provided.

_FEATURE_FLAGS = set(
    [
        "django.instrumentation.inclusion-tags.r1",
    ]
)

# Names of configuration file and deployment environment. This
# will be overridden by the load_configuration() function when
# configuration is loaded.

_config_file = None
_environment = None
_ignore_errors = True

# This is the actual internal settings object. Options which
# are read from the configuration file will be applied to this.

_settings = newrelic.api.settings.settings()

# Use the raw config parser as we want to avoid interpolation
# within values. This avoids problems when writing lambdas
# within the actual configuration file for options which value
# can be dynamically calculated at time wrapper is executed.
# This configuration object can be used by the instrumentation
# modules to look up customised settings defined in the loaded
# configuration file.

_config_object = ConfigParser.RawConfigParser()

# Cache of the parsed global settings found in the configuration
# file. We cache these so can dump them out to the log file once
# all the settings have been read.

_cache_object = []

# Mechanism for extracting settings from the configuration for use in
# instrumentation modules and extensions.


def extra_settings(section, types={}, defaults={}):
    settings = {}

    if _config_object.has_section(section):
        settings.update(_config_object.items(section))

    settings_object = Settings()

    for name, value in defaults.items():
        apply_config_setting(settings_object, name, value)

    for name, value in settings.items():
        if name in types:
            value = types[name](value)

        apply_config_setting(settings_object, name, value)

    return settings_object


# Define some mapping functions to convert raw values read from
# configuration file into the internal types expected by the
# internal configuration settings object.

_LOG_LEVEL = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}

_RECORD_SQL = {
    "off": newrelic.api.settings.RECORDSQL_OFF,
    "raw": newrelic.api.settings.RECORDSQL_RAW,
    "obfuscated": newrelic.api.settings.RECORDSQL_OBFUSCATED,
}

_COMPRESSED_CONTENT_ENCODING = {
    "deflate": newrelic.api.settings.COMPRESSED_CONTENT_ENCODING_DEFLATE,
    "gzip": newrelic.api.settings.COMPRESSED_CONTENT_ENCODING_GZIP,
}


def _map_log_level(s):
    return _LOG_LEVEL[s.upper()]


def _map_feature_flag(s):
    return set(s.split())


def _map_labels(s):
    return newrelic.core.config._environ_as_mapping(name="", default=s)


def _map_transaction_threshold(s):
    if s == "apdex_f":
        return None
    return float(s)


def _map_record_sql(s):
    return _RECORD_SQL[s]


def _map_compressed_content_encoding(s):
    return _COMPRESSED_CONTENT_ENCODING[s]


def _map_split_strings(s):
    return s.split()


def _map_console_listener_socket(s):
    return s % {"pid": os.getpid()}


def _merge_ignore_status_codes(s):
    return newrelic.core.config._parse_status_codes(s, _settings.error_collector.ignore_status_codes)


def _merge_expected_status_codes(s):
    return newrelic.core.config._parse_status_codes(s, _settings.error_collector.expected_status_codes)


def _map_browser_monitoring_content_type(s):
    return s.split()


def _map_strip_exception_messages_whitelist(s):
    return [expand_builtin_exception_name(item) for item in s.split()]


def _map_inc_excl_attributes(s):
    return newrelic.core.config._parse_attributes(s)


def _map_default_host_value(license_key):
    # If the license key is region aware, we should override the default host
    # to be the region aware host
    _default_host = default_host(license_key)
    _settings.host = os.environ.get("NEW_RELIC_HOST", _default_host)

    return license_key


# Processing of a single setting from configuration file.


def _raise_configuration_error(section, option=None):
    _logger.error("CONFIGURATION ERROR")
    if section:
        _logger.error("Section = %s" % section)

    if option is None:
        options = _config_object.options(section)

        _logger.error("Options = %s" % options)
        _logger.exception("Exception Details")

        if not _ignore_errors:
            if section:
                raise newrelic.api.exceptions.ConfigurationError(
                    'Invalid configuration for section "%s". '
                    "Check New Relic agent log file for further "
                    "details." % section
                )
            else:
                raise newrelic.api.exceptions.ConfigurationError(
                    "Invalid configuration. Check New Relic agent log file for further details."
                )

    else:
        _logger.error("Option = %s" % option)
        _logger.exception("Exception Details")

        if not _ignore_errors:
            if section:
                raise newrelic.api.exceptions.ConfigurationError(
                    'Invalid configuration for option "%s" in '
                    'section "%s". Check New Relic agent log '
                    "file for further details." % (option, section)
                )
            else:
                raise newrelic.api.exceptions.ConfigurationError(
                    'Invalid configuration for option "%s". '
                    "Check New Relic agent log file for further "
                    "details." % option
                )


def _process_setting(section, option, getter, mapper):
    try:
        # The type of a value is dictated by the getter
        # function supplied.

        value = getattr(_config_object, getter)(section, option)

        # The getter parsed the value okay but want to
        # pass this through a mapping function to change
        # it to internal value suitable for internal
        # settings object. This is usually one where the
        # value was a string.

        if mapper:
            value = mapper(value)

        # Now need to apply the option from the
        # configuration file to the internal settings
        # object. Walk the object path and assign it.

        target = _settings
        fields = option.split(".", 1)

        while True:
            if len(fields) == 1:
                setattr(target, fields[0], value)
                break
            else:
                target = getattr(target, fields[0])
                fields = fields[1].split(".", 1)

        # Cache the configuration so can be dumped out to
        # log file when whole main configuration has been
        # processed. This ensures that the log file and log
        # level entries have been set.

        _cache_object.append((option, value))

    except ConfigParser.NoSectionError:
        pass

    except ConfigParser.NoOptionError:
        pass

    except Exception:
        _raise_configuration_error(section, option)


# Processing of all the settings for specified section except
# for log file and log level which are applied separately to
# ensure they are set as soon as possible.


def _process_configuration(section):
    _process_setting(section, "feature_flag", "get", _map_feature_flag)
    _process_setting(section, "app_name", "get", None)
    _process_setting(section, "labels", "get", _map_labels)
    _process_setting(section, "license_key", "get", _map_default_host_value)
    _process_setting(section, "api_key", "get", None)
    _process_setting(section, "host", "get", None)
    _process_setting(section, "port", "getint", None)
    _process_setting(section, "ssl", "getboolean", None)
    _process_setting(section, "proxy_scheme", "get", None)
    _process_setting(section, "proxy_host", "get", None)
    _process_setting(section, "proxy_port", "getint", None)
    _process_setting(section, "proxy_user", "get", None)
    _process_setting(section, "proxy_pass", "get", None)
    _process_setting(section, "ca_bundle_path", "get", None)
    _process_setting(section, "audit_log_file", "get", None)
    _process_setting(section, "monitor_mode", "getboolean", None)
    _process_setting(section, "developer_mode", "getboolean", None)
    _process_setting(section, "high_security", "getboolean", None)
    _process_setting(section, "capture_params", "getboolean", None)
    _process_setting(section, "ignored_params", "get", _map_split_strings)
    _process_setting(section, "capture_environ", "getboolean", None)
    _process_setting(section, "include_environ", "get", _map_split_strings)
    _process_setting(section, "max_stack_trace_lines", "getint", None)
    _process_setting(section, "startup_timeout", "getfloat", None)
    _process_setting(section, "shutdown_timeout", "getfloat", None)
    _process_setting(section, "compressed_content_encoding", "get", _map_compressed_content_encoding)
    _process_setting(section, "attributes.enabled", "getboolean", None)
    _process_setting(section, "attributes.exclude", "get", _map_inc_excl_attributes)
    _process_setting(section, "attributes.include", "get", _map_inc_excl_attributes)
    _process_setting(section, "transaction_name.naming_scheme", "get", None)
    _process_setting(section, "gc_runtime_metrics.enabled", "getboolean", None)
    _process_setting(section, "gc_runtime_metrics.top_object_count_limit", "getint", None)
    _process_setting(section, "thread_profiler.enabled", "getboolean", None)
    _process_setting(section, "transaction_tracer.enabled", "getboolean", None)
    _process_setting(
        section,
        "transaction_tracer.transaction_threshold",
        "get",
        _map_transaction_threshold,
    )
    _process_setting(section, "transaction_tracer.record_sql", "get", _map_record_sql)
    _process_setting(section, "transaction_tracer.stack_trace_threshold", "getfloat", None)
    _process_setting(section, "transaction_tracer.explain_enabled", "getboolean", None)
    _process_setting(section, "transaction_tracer.explain_threshold", "getfloat", None)
    _process_setting(section, "transaction_tracer.function_trace", "get", _map_split_strings)
    _process_setting(section, "transaction_tracer.generator_trace", "get", _map_split_strings)
    _process_setting(section, "transaction_tracer.top_n", "getint", None)
    _process_setting(section, "transaction_tracer.attributes.enabled", "getboolean", None)
    _process_setting(
        section,
        "transaction_tracer.attributes.exclude",
        "get",
        _map_inc_excl_attributes,
    )
    _process_setting(
        section,
        "transaction_tracer.attributes.include",
        "get",
        _map_inc_excl_attributes,
    )
    _process_setting(section, "error_collector.enabled", "getboolean", None)
    _process_setting(section, "error_collector.capture_events", "getboolean", None)
    _process_setting(section, "error_collector.max_event_samples_stored", "getint", None)
    _process_setting(section, "error_collector.capture_source", "getboolean", None)
    _process_setting(section, "error_collector.ignore_errors", "get", _map_split_strings)
    _process_setting(section, "error_collector.ignore_classes", "get", _map_split_strings)
    _process_setting(
        section,
        "error_collector.ignore_status_codes",
        "get",
        _merge_ignore_status_codes,
    )
    _process_setting(section, "error_collector.expected_classes", "get", _map_split_strings)
    _process_setting(
        section,
        "error_collector.expected_status_codes",
        "get",
        _merge_expected_status_codes,
    )
    _process_setting(section, "error_collector.attributes.enabled", "getboolean", None)
    _process_setting(section, "error_collector.attributes.exclude", "get", _map_inc_excl_attributes)
    _process_setting(section, "error_collector.attributes.include", "get", _map_inc_excl_attributes)
    _process_setting(section, "browser_monitoring.enabled", "getboolean", None)
    _process_setting(section, "browser_monitoring.auto_instrument", "getboolean", None)
    _process_setting(section, "browser_monitoring.loader", "get", None)
    _process_setting(section, "browser_monitoring.debug", "getboolean", None)
    _process_setting(section, "browser_monitoring.ssl_for_http", "getboolean", None)
    _process_setting(section, "browser_monitoring.content_type", "get", _map_split_strings)
    _process_setting(section, "browser_monitoring.attributes.enabled", "getboolean", None)
    _process_setting(
        section,
        "browser_monitoring.attributes.exclude",
        "get",
        _map_inc_excl_attributes,
    )
    _process_setting(
        section,
        "browser_monitoring.attributes.include",
        "get",
        _map_inc_excl_attributes,
    )
    _process_setting(section, "slow_sql.enabled", "getboolean", None)
    _process_setting(section, "synthetics.enabled", "getboolean", None)
    _process_setting(section, "transaction_events.enabled", "getboolean", None)
    _process_setting(section, "transaction_events.max_samples_stored", "getint", None)
    _process_setting(section, "transaction_events.attributes.enabled", "getboolean", None)
    _process_setting(
        section,
        "transaction_events.attributes.exclude",
        "get",
        _map_inc_excl_attributes,
    )
    _process_setting(
        section,
        "transaction_events.attributes.include",
        "get",
        _map_inc_excl_attributes,
    )
    _process_setting(section, "custom_insights_events.enabled", "getboolean", None)
    _process_setting(section, "custom_insights_events.max_samples_stored", "getint", None)
    _process_setting(section, "distributed_tracing.enabled", "getboolean", None)
    _process_setting(section, "distributed_tracing.exclude_newrelic_header", "getboolean", None)
    _process_setting(section, "span_events.enabled", "getboolean", None)
    _process_setting(section, "span_events.max_samples_stored", "getint", None)
    _process_setting(section, "span_events.attributes.enabled", "getboolean", None)
    _process_setting(section, "span_events.attributes.exclude", "get", _map_inc_excl_attributes)
    _process_setting(section, "span_events.attributes.include", "get", _map_inc_excl_attributes)
    _process_setting(section, "transaction_segments.attributes.enabled", "getboolean", None)
    _process_setting(
        section,
        "transaction_segments.attributes.exclude",
        "get",
        _map_inc_excl_attributes,
    )
    _process_setting(
        section,
        "transaction_segments.attributes.include",
        "get",
        _map_inc_excl_attributes,
    )
    _process_setting(section, "local_daemon.socket_path", "get", None)
    _process_setting(section, "local_daemon.synchronous_startup", "getboolean", None)
    _process_setting(section, "agent_limits.transaction_traces_nodes", "getint", None)
    _process_setting(section, "agent_limits.sql_query_length_maximum", "getint", None)
    _process_setting(section, "agent_limits.slow_sql_stack_trace", "getint", None)
    _process_setting(section, "agent_limits.max_sql_connections", "getint", None)
    _process_setting(section, "agent_limits.sql_explain_plans", "getint", None)
    _process_setting(section, "agent_limits.sql_explain_plans_per_harvest", "getint", None)
    _process_setting(section, "agent_limits.slow_sql_data", "getint", None)
    _process_setting(section, "agent_limits.merge_stats_maximum", "getint", None)
    _process_setting(section, "agent_limits.errors_per_transaction", "getint", None)
    _process_setting(section, "agent_limits.errors_per_harvest", "getint", None)
    _process_setting(section, "agent_limits.slow_transaction_dry_harvests", "getint", None)
    _process_setting(section, "agent_limits.thread_profiler_nodes", "getint", None)
    _process_setting(section, "agent_limits.synthetics_events", "getint", None)
    _process_setting(section, "agent_limits.synthetics_transactions", "getint", None)
    _process_setting(section, "agent_limits.data_compression_threshold", "getint", None)
    _process_setting(section, "agent_limits.data_compression_level", "getint", None)
    _process_setting(section, "console.listener_socket", "get", _map_console_listener_socket)
    _process_setting(section, "console.allow_interpreter_cmd", "getboolean", None)
    _process_setting(section, "debug.disable_api_supportability_metrics", "getboolean", None)
    _process_setting(section, "debug.log_data_collector_calls", "getboolean", None)
    _process_setting(section, "debug.log_data_collector_payloads", "getboolean", None)
    _process_setting(section, "debug.log_malformed_json_data", "getboolean", None)
    _process_setting(section, "debug.log_transaction_trace_payload", "getboolean", None)
    _process_setting(section, "debug.log_thread_profile_payload", "getboolean", None)
    _process_setting(section, "debug.log_raw_metric_data", "getboolean", None)
    _process_setting(section, "debug.log_normalized_metric_data", "getboolean", None)
    _process_setting(section, "debug.log_normalization_rules", "getboolean", None)
    _process_setting(section, "debug.log_agent_initialization", "getboolean", None)
    _process_setting(section, "debug.log_explain_plan_queries", "getboolean", None)
    _process_setting(section, "debug.log_autorum_middleware", "getboolean", None)
    _process_setting(section, "debug.log_untrusted_distributed_trace_keys", "getboolean", None)
    _process_setting(section, "debug.enable_coroutine_profiling", "getboolean", None)
    _process_setting(section, "debug.record_transaction_failure", "getboolean", None)
    _process_setting(section, "debug.explain_plan_obfuscation", "get", None)
    _process_setting(section, "debug.disable_certificate_validation", "getboolean", None)
    _process_setting(section, "debug.disable_harvest_until_shutdown", "getboolean", None)
    _process_setting(section, "debug.connect_span_stream_in_developer_mode", "getboolean", None)
    _process_setting(section, "cross_application_tracer.enabled", "getboolean", None)
    _process_setting(section, "message_tracer.segment_parameters_enabled", "getboolean", None)
    _process_setting(section, "process_host.display_name", "get", None)
    _process_setting(section, "utilization.detect_aws", "getboolean", None)
    _process_setting(section, "utilization.detect_azure", "getboolean", None)
    _process_setting(section, "utilization.detect_docker", "getboolean", None)
    _process_setting(section, "utilization.detect_kubernetes", "getboolean", None)
    _process_setting(section, "utilization.detect_gcp", "getboolean", None)
    _process_setting(section, "utilization.detect_pcf", "getboolean", None)
    _process_setting(section, "utilization.logical_processors", "getint", None)
    _process_setting(section, "utilization.total_ram_mib", "getint", None)
    _process_setting(section, "utilization.billing_hostname", "get", None)
    _process_setting(section, "strip_exception_messages.enabled", "getboolean", None)
    _process_setting(
        section,
        "strip_exception_messages.whitelist",
        "get",
        _map_strip_exception_messages_whitelist,
    )
    _process_setting(section, "datastore_tracer.instance_reporting.enabled", "getboolean", None)
    _process_setting(section, "datastore_tracer.database_name_reporting.enabled", "getboolean", None)
    _process_setting(section, "heroku.use_dyno_names", "getboolean", None)
    _process_setting(section, "heroku.dyno_name_prefixes_to_shorten", "get", _map_split_strings)
    _process_setting(section, "serverless_mode.enabled", "getboolean", None)
    _process_setting(section, "apdex_t", "getfloat", None)
    _process_setting(section, "event_loop_visibility.enabled", "getboolean", None)
    _process_setting(section, "event_loop_visibility.blocking_threshold", "getfloat", None)
    _process_setting(
        section,
        "event_harvest_config.harvest_limits.analytic_event_data",
        "getint",
        None,
    )
    _process_setting(section, "event_harvest_config.harvest_limits.custom_event_data", "getint", None)
    _process_setting(section, "event_harvest_config.harvest_limits.span_event_data", "getint", None)
    _process_setting(section, "event_harvest_config.harvest_limits.error_event_data", "getint", None)
    _process_setting(section, "infinite_tracing.trace_observer_host", "get", None)
    _process_setting(section, "infinite_tracing.trace_observer_port", "getint", None)
    _process_setting(section, "infinite_tracing.span_queue_size", "getint", None)


# Loading of configuration from specified file and for specified
# deployment environment. Can also indicate whether configuration
# and instrumentation errors should raise an exception or not.

_configuration_done = False


def _process_app_name_setting():
    # Do special processing to handle the case where the application
    # name was actually a semicolon separated list of names. In this
    # case the first application name is the primary and the others are
    # linked applications the application also reports to. What we need
    # to do is explicitly retrieve the application object for the
    # primary application name and link it with the other applications.
    # When activating the application the linked names will be sent
    # along to the core application where the association will be
    # created if the do not exist.

    name = _settings.app_name.split(";")[0].strip() or "Python Application"

    linked = []
    for altname in _settings.app_name.split(";")[1:]:
        altname = altname.strip()
        if altname:
            linked.append(altname)

    def _link_applications(application):
        for altname in linked:
            _logger.debug("link to %s" % ((name, altname),))
            application.link_to_application(altname)

    if linked:
        newrelic.api.application.Application.run_on_initialization(name, _link_applications)
        _settings.linked_applications = linked

    _settings.app_name = name


def _process_labels_setting(labels=None):
    # Do special processing to handle labels. Initially the labels
    # setting will be a list of key/value tuples. This needs to be
    # converted into a list of dictionaries. It is also necessary
    # to eliminate duplicates by taking the last value, plus apply
    # length limits and limits on the number collected.

    if labels is None:
        labels = _settings.labels

    length_limit = 255
    count_limit = 64

    deduped = {}

    for key, value in labels:

        if len(key) > length_limit:
            _logger.warning(
                "Improper configuration. Label key %s is too long. Truncating key to: %s" % (key, key[:length_limit])
            )

        if len(value) > length_limit:
            _logger.warning(
                "Improper configuration. Label value %s is too "
                "long. Truncating value to: %s" % (value, value[:length_limit])
            )

        if len(deduped) >= count_limit:
            _logger.warning(
                "Improper configuration. Maximum number of labels reached. Using first %d labels." % count_limit
            )
            break

        key = key[:length_limit]
        value = value[:length_limit]

        deduped[key] = value

    result = []

    for key, value in deduped.items():
        result.append({"label_type": key, "label_value": value})

    _settings.labels = result


def delete_setting(settings_object, name):
    """Delete setting from settings_object.

    If passed a 'root' setting, like 'error_collector', it will
    delete 'error_collector' and all settings underneath it, such
    as 'error_collector.attributes.enabled'

    """

    target = settings_object
    fields = name.split(".", 1)

    while len(fields) > 1:
        if not hasattr(target, fields[0]):
            break
        target = getattr(target, fields[0])
        fields = fields[1].split(".", 1)

    try:
        delattr(target, fields[0])
    except AttributeError:
        _logger.debug("Failed to delete setting: %r", name)


def translate_deprecated_settings(settings, cached_settings):
    # If deprecated setting has been set by user, but the new
    # setting has not, then translate the deprecated setting to the
    # new one.
    #
    # If both deprecated and new setting have been applied, ignore
    # deprecated setting.
    #
    # In either case, delete the deprecated one from the settings object.

    # Parameters:
    #
    #    settings:
    #         Settings object
    #
    #   cached_settings:
    #         A list of (key, value) pairs of the parsed global settings
    #         found in the config file.

    # NOTE:
    #
    # cached_settings is a list of option key/values and can have duplicate
    # keys, if the customer used environment sections in the config file.
    # Since options are applied to the settings object in order, so that the
    # options at the end of the list will override earlier options with the
    # same key, then converting to a dict will result in each option having
    # the most recently applied value.

    cached = dict(cached_settings)

    deprecated_settings_map = [
        (
            "transaction_tracer.capture_attributes",
            "transaction_tracer.attributes.enabled",
        ),
        ("error_collector.capture_attributes", "error_collector.attributes.enabled"),
        (
            "browser_monitoring.capture_attributes",
            "browser_monitoring.attributes.enabled",
        ),
        (
            "analytics_events.capture_attributes",
            "transaction_events.attributes.enabled",
        ),
        ("analytics_events.enabled", "transaction_events.enabled"),
        (
            "analytics_events.max_samples_stored",
            "event_harvest_config.harvest_limits.analytic_event_data",
        ),
        (
            "transaction_events.max_samples_stored",
            "event_harvest_config.harvest_limits.analytic_event_data",
        ),
        (
            "span_events.max_samples_stored",
            "event_harvest_config.harvest_limits.span_event_data",
        ),
        (
            "error_collector.max_event_samples_stored",
            "event_harvest_config.harvest_limits.error_event_data",
        ),
        (
            "custom_insights_events.max_samples_stored",
            "event_harvest_config.harvest_limits.custom_event_data",
        ),
        (
            "error_collector.ignore_errors",
            "error_collector.ignore_classes",
        ),
    ]

    for (old_key, new_key) in deprecated_settings_map:

        if old_key in cached:
            _logger.info(
                "Deprecated setting found: %r. Please use new setting: %r.",
                old_key,
                new_key,
            )

            if new_key in cached:
                _logger.info(
                    "Ignoring deprecated setting: %r. Using new setting: %r.",
                    old_key,
                    new_key,
                )
            else:
                apply_config_setting(settings, new_key, cached[old_key])
                _logger.info("Applying value of deprecated setting %r to %r.", old_key, new_key)

            delete_setting(settings, old_key)

    # The 'ignored_params' setting is more complicated than the above
    # deprecated settings, so it gets handled separately.

    if "ignored_params" in cached:

        _logger.info(
            "Deprecated setting found: ignored_params. Please use "
            "new setting: attributes.exclude. For the new setting, an "
            "ignored parameter should be prefaced with "
            '"request.parameters.". For example, ignoring a parameter '
            'named "foo" should be added added to attributes.exclude as '
            '"request.parameters.foo."'
        )

        # Don't merge 'ignored_params' settings. If user set
        # 'attributes.exclude' setting, only use those values,
        # and ignore 'ignored_params' settings.

        if "attributes.exclude" in cached:
            _logger.info("Ignoring deprecated setting: ignored_params. Using new setting: attributes.exclude.")

        else:
            ignored_params = fetch_config_setting(settings, "ignored_params")

            for p in ignored_params:
                attr_value = "request.parameters." + p
                excluded_attrs = fetch_config_setting(settings, "attributes.exclude")

                if attr_value not in excluded_attrs:
                    settings.attributes.exclude.append(attr_value)
                    _logger.info(
                        "Applying value of deprecated setting ignored_params to attributes.exclude: %r.",
                        attr_value,
                    )

        delete_setting(settings, "ignored_params")

    # The 'capture_params' setting is deprecated, but since it affects
    # attribute filter default destinations, it is not translated here. We
    # log a message, but keep the capture_params setting.
    #
    # See newrelic.core.transaction:Transaction.agent_attributes to see how
    # it is used.

    if "capture_params" in cached:
        _logger.info(
            "Deprecated setting found: capture_params. Please use "
            "new setting: attributes.exclude. To disable capturing all "
            'request parameters, add "request.parameters.*" to '
            "attributes.exclude."
        )

    if "cross_application_tracer.enabled" in cached:
        # CAT Deprecation Warning
        _logger.info(
            "Deprecated setting found: cross_application_tracer.enabled. Please replace Cross Application Tracing "
            "(CAT) with the newer Distributed Tracing by setting 'distributed_tracing.enabled' to True in your agent "
            "configuration. For further details on distributed tracing, please refer to our documentation: "
            "https://docs.newrelic.com/docs/distributed-tracing/concepts/distributed-tracing-planning-guide/#changes."
        )

    if not settings.ssl:
        settings.ssl = True
        _logger.info("Ignoring deprecated setting: ssl. Enabling ssl is now mandatory. Setting ssl=true.")

    if settings.agent_limits.merge_stats_maximum is not None:
        _logger.info(
            "Ignoring deprecated setting: "
            "agent_limits.merge_stats_maximum. The agent will now respect "
            "server-side commands."
        )

    return settings


def apply_local_high_security_mode_setting(settings):
    # When High Security Mode is activated, certain settings must be
    # set to be secure, even if that requires overriding a setting that
    # has been individually configured as insecure.

    if not settings.high_security:
        return settings

    log_template = (
        "Overriding setting for %r because High "
        "Security Mode has been activated. The original "
        "setting was %r. The new setting is %r."
    )

    # capture_params is a deprecated setting for users, and has three
    # possible values:
    #
    #   True:  For backward compatibility.
    #   False: For backward compatibility.
    #   None:  The current default setting.
    #
    # In High Security, capture_params must be False, but we only need
    # to log if the customer has actually used the deprecated setting
    # and set it to True.

    if settings.capture_params:
        settings.capture_params = False
        _logger.info(log_template, "capture_params", True, False)
    elif settings.capture_params is None:
        settings.capture_params = False

    if settings.transaction_tracer.record_sql == "raw":
        settings.transaction_tracer.record_sql = "obfuscated"
        _logger.info(log_template, "transaction_tracer.record_sql", "raw", "obfuscated")

    if not settings.strip_exception_messages.enabled:
        settings.strip_exception_messages.enabled = True
        _logger.info(log_template, "strip_exception_messages.enabled", False, True)

    if settings.custom_insights_events.enabled:
        settings.custom_insights_events.enabled = False
        _logger.info(log_template, "custom_insights_events.enabled", True, False)

    if settings.message_tracer.segment_parameters_enabled:
        settings.message_tracer.segment_parameters_enabled = False
        _logger.info(log_template, "message_tracer.segment_parameters_enabled", True, False)

    return settings


def _load_configuration(
    config_file=None,
    environment=None,
    ignore_errors=True,
    log_file=None,
    log_level=None,
):

    global _configuration_done

    global _config_file
    global _environment
    global _ignore_errors

    # Check whether initialisation has been done previously. If
    # it has then raise a configuration error if it was against
    # a different configuration. Otherwise just return. We don't
    # check at this time if an incompatible configuration has
    # been read from a different sub interpreter. If this occurs
    # then results will be undefined. Use from different sub
    # interpreters of the same process is not recommended.

    if _configuration_done:
        if _config_file != config_file or _environment != environment:
            raise newrelic.api.exceptions.ConfigurationError(
                "Configuration has already been done against "
                "differing configuration file or environment. "
                'Prior configuration file used was "%s" and '
                'environment "%s".' % (_config_file, _environment)
            )
        else:
            return

    _configuration_done = True

    # Update global variables tracking what configuration file and
    # environment was used, plus whether errors are to be ignored.

    _config_file = config_file
    _environment = environment
    _ignore_errors = ignore_errors

    # If no configuration file then nothing more to be done.

    if not config_file:

        _logger.debug("no agent configuration file")

        # Force initialisation of the logging system now in case
        # setup provided by environment variables.

        if log_file is None:
            log_file = _settings.log_file

        if log_level is None:
            log_level = _settings.log_level

        initialize_logging(log_file, log_level)

        # Validate provided feature flags and log a warning if get one
        # which isn't valid.

        for flag in _settings.feature_flag:
            if flag not in _FEATURE_FLAGS:
                _logger.warning(
                    "Unknown agent feature flag %r provided. "
                    "Check agent documentation or release notes, or "
                    "contact New Relic support for clarification of "
                    "validity of the specific feature flag.",
                    flag,
                )

        # Look for an app_name setting which is actually a semi colon
        # list of application names and adjust app_name setting and
        # registered linked applications for later handling.

        _process_app_name_setting()

        # Look for any labels and translate them into required form
        # for sending up to data collector on registration.

        _process_labels_setting()

        return

    _logger.debug("agent configuration file was %s" % config_file)

    # Now read in the configuration file. Cache the config file
    # name in internal settings object as indication of succeeding.

    if not _config_object.read([config_file]):
        raise newrelic.api.exceptions.ConfigurationError("Unable to open configuration file %s." % config_file)

    _settings.config_file = config_file

    # Must process log file entries first so that errors with
    # the remainder will get logged if log file is defined.

    _process_setting("newrelic", "log_file", "get", None)

    if environment:
        _process_setting("newrelic:%s" % environment, "log_file", "get", None)

    if log_file is None:
        log_file = _settings.log_file

    _process_setting("newrelic", "log_level", "get", _map_log_level)

    if environment:
        _process_setting("newrelic:%s" % environment, "log_level", "get", _map_log_level)

    if log_level is None:
        log_level = _settings.log_level

    # Force initialisation of the logging system now that we
    # have the log file and log level.

    initialize_logging(log_file, log_level)

    # Now process the remainder of the global configuration
    # settings.

    _process_configuration("newrelic")

    # And any overrides specified with a section corresponding
    # to a specific deployment environment.

    if environment:
        _settings.environment = environment
        _process_configuration("newrelic:%s" % environment)

    # Log details of the configuration options which were
    # read and the values they have as would be applied
    # against the internal settings object.

    for option, value in _cache_object:
        _logger.debug("agent config %s = %s" % (option, repr(value)))

    # Validate provided feature flags and log a warning if get one
    # which isn't valid.

    for flag in _settings.feature_flag:
        if flag not in _FEATURE_FLAGS:
            _logger.warning(
                "Unknown agent feature flag %r provided. "
                "Check agent documentation or release notes, or "
                "contact New Relic support for clarification of "
                "validity of the specific feature flag.",
                flag,
            )

    # Translate old settings

    translate_deprecated_settings(_settings, _cache_object)

    # Apply High Security Mode policy if enabled in local agent
    # configuration file.

    apply_local_high_security_mode_setting(_settings)

    # Look for an app_name setting which is actually a semi colon
    # list of application names and adjust app_name setting and
    # registered linked applications for later handling.

    _process_app_name_setting()

    # Look for any labels and translate them into required form
    # for sending up to data collector on registration.

    _process_labels_setting()

    # Instrument with function trace any callables supplied by the
    # user in the configuration.

    for function in _settings.transaction_tracer.function_trace:
        try:
            (module, object_path) = function.split(":", 1)

            name = None
            group = "Function"
            label = None
            params = None
            terminal = False
            rollup = None

            _logger.debug("register function-trace %s" % ((module, object_path, name, group),))

            hook = _function_trace_import_hook(object_path, name, group, label, params, terminal, rollup)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section=None, option="transaction_tracer.function_trace")

    # Instrument with generator trace any callables supplied by the
    # user in the configuration.

    for function in _settings.transaction_tracer.generator_trace:
        try:
            (module, object_path) = function.split(":", 1)

            name = None
            group = "Function"

            _logger.debug("register generator-trace %s" % ((module, object_path, name, group),))

            hook = _generator_trace_import_hook(object_path, name, group)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section=None, option="transaction_tracer.generator_trace")


# Generic error reporting functions.


def _raise_instrumentation_error(type, locals):
    _logger.error("INSTRUMENTATION ERROR")
    _logger.error("Type = %s" % type)
    _logger.error("Locals = %s" % locals)
    _logger.exception("Exception Details")

    if not _ignore_errors:
        raise newrelic.api.exceptions.InstrumentationError(
            "Failure when instrumenting code. Check New Relic agent log file for further details."
        )


# Registration of module import hooks defined in configuration file.

_module_import_hook_results = {}
_module_import_hook_registry = {}


def module_import_hook_results():
    return _module_import_hook_results


def _module_import_hook(target, module, function):
    def _instrument(target):
        _logger.debug("instrument module %s" % ((target, module, function),))

        try:
            instrumented = target._nr_instrumented
        except AttributeError:
            instrumented = target._nr_instrumented = set()

        if (module, function) in instrumented:
            _logger.debug("instrumentation already run %s" % ((target, module, function),))
            return

        instrumented.add((module, function))

        try:
            getattr(newrelic.api.import_hook.import_module(module), function)(target)

            _module_import_hook_results[(target.__name__, module, function)] = ""

        except Exception:
            _module_import_hook_results[(target.__name__, module, function)] = traceback.format_exception(
                *sys.exc_info()
            )

            _raise_instrumentation_error("import-hook", locals())

    return _instrument


def _process_module_configuration():
    for section in _config_object.sections():
        if not section.startswith("import-hook:"):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, "enabled")
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            execute = _config_object.get(section, "execute")
            fields = execute.split(":", 1)
            module = fields[0]
            function = "instrument"
            if len(fields) != 1:
                function = fields[1]

            target = section.split(":", 1)[1]

            if target not in _module_import_hook_registry:
                _module_import_hook_registry[target] = (module, function)

                _logger.debug("register module %s" % ((target, module, function),))

                hook = _module_import_hook(target, module, function)
                newrelic.api.import_hook.register_import_hook(target, hook)

                _module_import_hook_results.setdefault((target, module, function), None)

        except Exception:
            _raise_configuration_error(section)


def _module_function_glob(module, object_path):
    """Match functions and class methods in a module to file globbing syntax."""
    if not any([c in object_path for c in {"*", "?", "["}]):  # Identify globbing patterns
        return (object_path,)  # Returned value must be iterable
    else:
        # Gather module functions
        try:
            available_functions = {k: v for k, v in module.__dict__.items() if callable(v) and not isinstance(v, type)}
        except Exception:
            # Default to empty dict if no functions available
            available_functions = dict()

        # Gather module classes and methods
        try:
            available_classes = {k: v for k, v in module.__dict__.items() if isinstance(v, type)}
            for cls in available_classes:
                try:
                    # Skip adding individual class's methods on failure
                    available_functions.update(
                        {
                            "%s.%s" % (cls, k): v
                            for k, v in available_classes.get(cls).__dict__.items()
                            if callable(v) and not isinstance(v, type)
                        }
                    )
                except Exception:
                    pass
        except Exception:
            # Skip adding all class methods on failure
            pass

        # Under the hood uses fnmatch, which uses os.path.normcase
        # On windows this would cause issues with case insensitivity,
        # but on all other operating systems there should be no issues.
        return fnmatch.filter(available_functions, object_path)


# Setup wsgi application wrapper defined in configuration file.


def _wsgi_application_import_hook(object_path, application):
    def _instrument(target):
        try:
            for func in _module_function_glob(target, object_path):
                _logger.debug("wrap wsgi-application %s", (target, func, application))
                newrelic.api.wsgi_application.wrap_wsgi_application(target, func, application)
        except Exception:
            _raise_instrumentation_error("wsgi-application", locals())

    return _instrument


def _process_wsgi_application_configuration():
    for section in _config_object.sections():
        if not section.startswith("wsgi-application:"):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, "enabled")
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, "function")
            (module, object_path) = function.split(":", 1)

            application = None

            if _config_object.has_option(section, "application"):
                application = _config_object.get(section, "application")

            _logger.debug("register wsgi-application %s" % ((module, object_path, application),))

            hook = _wsgi_application_import_hook(object_path, application)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


# Setup background task wrapper defined in configuration file.


def _background_task_import_hook(object_path, application, name, group):
    def _instrument(target):
        try:
            for func in _module_function_glob(target, object_path):
                _logger.debug("wrap background-task %s", (target, func, application, name, group))
                newrelic.api.background_task.wrap_background_task(target, func, application, name, group)
        except Exception:
            _raise_instrumentation_error("background-task", locals())

    return _instrument


def _process_background_task_configuration():
    for section in _config_object.sections():
        if not section.startswith("background-task:"):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, "enabled")
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, "function")
            (module, object_path) = function.split(":", 1)

            application = None
            name = None
            group = "Function"

            if _config_object.has_option(section, "application"):
                application = _config_object.get(section, "application")
            if _config_object.has_option(section, "name"):
                name = _config_object.get(section, "name")
            if _config_object.has_option(section, "group"):
                group = _config_object.get(section, "group")

            if name and name.startswith("lambda "):
                vars = {"callable_name": newrelic.api.object_wrapper.callable_name}
                name = eval(name, vars)  # nosec

            _logger.debug("register background-task %s" % ((module, object_path, application, name, group),))

            hook = _background_task_import_hook(object_path, application, name, group)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


# Setup database traces defined in configuration file.


def _database_trace_import_hook(object_path, sql):
    def _instrument(target):
        try:
            for func in _module_function_glob(target, object_path):
                _logger.debug("wrap database-trace %s", (target, func, sql))
                newrelic.api.database_trace.wrap_database_trace(target, func, sql)
        except Exception:
            _raise_instrumentation_error("database-trace", locals())

    return _instrument


def _process_database_trace_configuration():
    for section in _config_object.sections():
        if not section.startswith("database-trace:"):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, "enabled")
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, "function")
            (module, object_path) = function.split(":", 1)

            sql = _config_object.get(section, "sql")

            if sql.startswith("lambda "):
                vars = {"callable_name": newrelic.api.object_wrapper.callable_name}
                sql = eval(sql, vars)  # nosec

            _logger.debug("register database-trace %s" % ((module, object_path, sql),))

            hook = _database_trace_import_hook(object_path, sql)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


# Setup external traces defined in configuration file.


def _external_trace_import_hook(object_path, library, url, method):
    def _instrument(target):
        try:
            for func in _module_function_glob(target, object_path):
                _logger.debug("wrap external-trace %s", (target, func, library, url, method))
                newrelic.api.external_trace.wrap_external_trace(target, func, library, url, method)
        except Exception:
            _raise_instrumentation_error("external-trace", locals())

    return _instrument


def _process_external_trace_configuration():
    for section in _config_object.sections():
        if not section.startswith("external-trace:"):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, "enabled")
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, "function")
            (module, object_path) = function.split(":", 1)

            method = None

            library = _config_object.get(section, "library")
            url = _config_object.get(section, "url")
            if _config_object.has_option(section, "method"):
                method = _config_object.get(section, "method")

            if url.startswith("lambda "):
                vars = {"callable_name": newrelic.api.object_wrapper.callable_name}
                url = eval(url, vars)  # nosec

            if method and method.startswith("lambda "):
                vars = {"callable_name": newrelic.api.object_wrapper.callable_name}
                method = eval(method, vars)  # nosec

            _logger.debug("register external-trace %s" % ((module, object_path, library, url, method),))

            hook = _external_trace_import_hook(object_path, library, url, method)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


# Setup function traces defined in configuration file.


def _function_trace_import_hook(object_path, name, group, label, params, terminal, rollup):
    def _instrument(target):
        try:
            for func in _module_function_glob(target, object_path):
                _logger.debug("wrap function-trace %s", (target, func, name, group, label, params, terminal, rollup))
                newrelic.api.function_trace.wrap_function_trace(
                    target, func, name, group, label, params, terminal, rollup
                )
        except Exception:
            _raise_instrumentation_error("function-trace", locals())

    return _instrument


def _process_function_trace_configuration():
    for section in _config_object.sections():
        if not section.startswith("function-trace:"):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, "enabled")
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, "function")
            (module, object_path) = function.split(":", 1)

            name = None
            group = "Function"
            label = None
            params = None
            terminal = False
            rollup = None

            if _config_object.has_option(section, "name"):
                name = _config_object.get(section, "name")
            if _config_object.has_option(section, "group"):
                group = _config_object.get(section, "group")
            if _config_object.has_option(section, "label"):
                label = _config_object.get(section, "label")
            if _config_object.has_option(section, "terminal"):
                terminal = _config_object.getboolean(section, "terminal")
            if _config_object.has_option(section, "rollup"):
                rollup = _config_object.get(section, "rollup")

            if name and name.startswith("lambda "):
                vars = {"callable_name": newrelic.api.object_wrapper.callable_name}
                name = eval(name, vars)  # nosec

            _logger.debug(
                "register function-trace %s" % ((module, object_path, name, group, label, params, terminal, rollup),)
            )

            hook = _function_trace_import_hook(object_path, name, group, label, params, terminal, rollup)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


# Setup generator traces defined in configuration file.


def _generator_trace_import_hook(object_path, name, group):
    def _instrument(target):
        try:
            for func in _module_function_glob(target, object_path):
                _logger.debug("wrap generator-trace %s", (target, func, name, group))
                newrelic.api.generator_trace.wrap_generator_trace(target, func, name, group)
        except Exception:
            _raise_instrumentation_error("generator-trace", locals())

    return _instrument


def _process_generator_trace_configuration():
    for section in _config_object.sections():
        if not section.startswith("generator-trace:"):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, "enabled")
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, "function")
            (module, object_path) = function.split(":", 1)

            name = None
            group = "Function"

            if _config_object.has_option(section, "name"):
                name = _config_object.get(section, "name")
            if _config_object.has_option(section, "group"):
                group = _config_object.get(section, "group")

            if name and name.startswith("lambda "):
                vars = {"callable_name": newrelic.api.object_wrapper.callable_name}
                name = eval(name, vars)  # nosec

            _logger.debug("register generator-trace %s" % ((module, object_path, name, group),))

            hook = _generator_trace_import_hook(object_path, name, group)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


# Setup profile traces defined in configuration file.


def _profile_trace_import_hook(object_path, name, group, depth):
    def _instrument(target):
        try:
            for func in _module_function_glob(target, object_path):
                _logger.debug("wrap profile-trace %s", (target, func, name, group, depth))
                newrelic.api.profile_trace.wrap_profile_trace(target, func, name, group, depth=depth)
        except Exception:
            _raise_instrumentation_error("profile-trace", locals())

    return _instrument


def _process_profile_trace_configuration():
    for section in _config_object.sections():
        if not section.startswith("profile-trace:"):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, "enabled")
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, "function")
            (module, object_path) = function.split(":", 1)

            name = None
            group = "Function"
            depth = 3

            if _config_object.has_option(section, "name"):
                name = _config_object.get(section, "name")
            if _config_object.has_option(section, "group"):
                group = _config_object.get(section, "group")
            if _config_object.has_option(section, "depth"):
                depth = _config_object.get(section, "depth")

            if name and name.startswith("lambda "):
                vars = {"callable_name": newrelic.api.object_wrapper.callable_name}
                name = eval(name, vars)  # nosec

            _logger.debug("register profile-trace %s" % ((module, object_path, name, group, depth),))

            hook = _profile_trace_import_hook(object_path, name, group, depth=depth)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


# Setup memcache traces defined in configuration file.


def _memcache_trace_import_hook(object_path, command):
    def _instrument(target):
        try:
            for func in _module_function_glob(target, object_path):
                _logger.debug("wrap memcache-trace %s", (target, func, command))
                newrelic.api.memcache_trace.wrap_memcache_trace(target, func, command)
        except Exception:
            _raise_instrumentation_error("memcache-trace", locals())

    return _instrument


def _process_memcache_trace_configuration():
    for section in _config_object.sections():
        if not section.startswith("memcache-trace:"):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, "enabled")
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, "function")
            (module, object_path) = function.split(":", 1)

            command = _config_object.get(section, "command")

            if command.startswith("lambda "):
                vars = {"callable_name": newrelic.api.object_wrapper.callable_name}
                command = eval(command, vars)  # nosec

            _logger.debug("register memcache-trace %s", (module, object_path, command))

            hook = _memcache_trace_import_hook(object_path, command)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


# Setup name transaction wrapper defined in configuration file.


def _transaction_name_import_hook(object_path, name, group, priority):
    def _instrument(target):
        try:
            for func in _module_function_glob(target, object_path):
                _logger.debug("wrap transaction-name %s" % ((target, func, name, group, priority),))
                newrelic.api.transaction_name.wrap_transaction_name(target, func, name, group, priority)
        except Exception:
            _raise_instrumentation_error("transaction-name", locals())

    return _instrument


def _process_transaction_name_configuration():
    for section in _config_object.sections():
        # Support 'name-transaction' for backward compatibility.
        if not section.startswith("transaction-name:") and not section.startswith("name-transaction:"):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, "enabled")
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, "function")
            (module, object_path) = function.split(":", 1)

            name = None
            group = "Function"
            priority = None

            if _config_object.has_option(section, "name"):
                name = _config_object.get(section, "name")
            if _config_object.has_option(section, "group"):
                group = _config_object.get(section, "group")
            if _config_object.has_option(section, "priority"):
                priority = _config_object.getint(section, "priority")

            if name and name.startswith("lambda "):
                vars = {"callable_name": newrelic.api.object_wrapper.callable_name}
                name = eval(name, vars)  # nosec

            _logger.debug("register transaction-name %s" % ((module, object_path, name, group, priority),))

            hook = _transaction_name_import_hook(object_path, name, group, priority)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


# Setup error trace wrapper defined in configuration file.


def _error_trace_import_hook(object_path, ignore, expected):
    def _instrument(target):
        try:
            for func in _module_function_glob(target, object_path):
                _logger.debug("wrap error-trace %s", (target, func, ignore, expected))
                newrelic.api.error_trace.wrap_error_trace(target, func, ignore, expected, None)
        except Exception:
            _raise_instrumentation_error("error-trace", locals())

    return _instrument


def _process_error_trace_configuration():
    for section in _config_object.sections():
        if not section.startswith("error-trace:"):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, "enabled")
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, "function")
            (module, object_path) = function.split(":", 1)

            ignore_classes = []
            expected_classes = []

            if _config_object.has_option(section, "ignore_classes"):
                ignore_classes = _config_object.get(section, "ignore_classes").split()

            if _config_object.has_option(section, "ignore_errors"):
                if _config_object.has_option(section, "ignore_classes"):
                    _logger.info("Ignoring deprecated setting: ignore_errors. Please use new setting: ignore_classes.")
                else:
                    _logger.info("Deprecated setting found: ignore_errors. Please use new setting: ignore_classes.")
                    ignore_classes = _config_object.get(section, "ignore_errors").split()

            if _config_object.has_option(section, "expected_classes"):
                expected_classes = _config_object.get(section, "expected_classes").split()

            _logger.debug("register error-trace %s", (module, object_path, ignore_classes, expected_classes))

            hook = _error_trace_import_hook(object_path, ignore_classes, expected_classes)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


# Automatic data source loading defined in configuration file.

_data_sources = []


def _process_data_source_configuration():
    for section in _config_object.sections():
        if not section.startswith("data-source:"):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, "enabled")
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, "function")
            (module, object_path) = function.split(":", 1)

            application = None
            name = None
            settings = {}
            properties = {}

            if _config_object.has_option(section, "application"):
                application = _config_object.get(section, "application")
            if _config_object.has_option(section, "name"):
                name = _config_object.get(section, "name")

            if _config_object.has_option(section, "settings"):
                config_section = _config_object.get(section, "settings")
                settings.update(_config_object.items(config_section))

            properties.update(_config_object.items(section))

            properties.pop("enabled", None)
            properties.pop("function", None)
            properties.pop("application", None)
            properties.pop("name", None)
            properties.pop("settings", None)

            _logger.debug("register data-source %s", (module, object_path, name))

            _data_sources.append((section, module, object_path, application, name, settings, properties))
        except Exception:
            _raise_configuration_error(section)


def _startup_data_source():
    _logger.debug("Registering data sources defined in configuration.")

    agent_instance = newrelic.core.agent.agent_instance()

    for (
        section,
        module,
        object_path,
        application,
        name,
        settings,
        properties,
    ) in _data_sources:
        try:
            source = getattr(newrelic.api.import_hook.import_module(module), object_path)

            agent_instance.register_data_source(source, application, name, settings, **properties)

        except Exception:
            _logger.exception(
                "Attempt to register data source %s:%s with "
                "name %r from section %r of agent configuration file "
                "has failed. Data source will be skipped.",
                module,
                object_path,
                name,
                section,
            )


_data_sources_done = False


def _setup_data_source():

    global _data_sources_done

    if _data_sources_done:
        return

    _data_sources_done = True

    if _data_sources:
        newrelic.core.agent.Agent.run_on_startup(_startup_data_source)


# Setup function profiler defined in configuration file.


def _function_profile_import_hook(object_path, filename, delay, checkpoint):
    def _instrument(target):
        try:
            for func in _module_function_glob(target, object_path):
                _logger.debug("wrap function-profile %s", (target, func, filename, delay, checkpoint))
                newrelic.api.function_profile.wrap_function_profile(target, func, filename, delay, checkpoint)
        except Exception:
            _raise_instrumentation_error("function-profile", locals())

    return _instrument


def _process_function_profile_configuration():
    for section in _config_object.sections():
        if not section.startswith("function-profile:"):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, "enabled")
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, "function")
            (module, object_path) = function.split(":", 1)

            filename = None
            delay = 1.0
            checkpoint = 30

            filename = _config_object.get(section, "filename")

            if _config_object.has_option(section, "delay"):
                delay = _config_object.getfloat(section, "delay")
            if _config_object.has_option(section, "checkpoint"):
                checkpoint = _config_object.getfloat(section, "checkpoint")

            _logger.debug("register function-profile %s" % ((module, object_path, filename, delay, checkpoint),))

            hook = _function_profile_import_hook(object_path, filename, delay, checkpoint)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


def _process_module_definition(target, module, function="instrument"):
    enabled = True
    execute = None

    # XXX This check makes the following checks to see if import hook
    # was defined in agent configuration file redundant. Leave it as is
    # for now until can clean up whole configuration system.

    if target in _module_import_hook_registry:
        return

    try:
        section = "import-hook:%s" % target
        if _config_object.has_section(section):
            enabled = _config_object.getboolean(section, "enabled")
    except ConfigParser.NoOptionError:
        pass
    except Exception:
        _raise_configuration_error(section)

    try:
        if _config_object.has_option(section, "execute"):
            execute = _config_object.get(section, "execute")

    except Exception:
        _raise_configuration_error(section)

    try:
        if enabled and not execute:
            _module_import_hook_registry[target] = (module, function)

            _logger.debug("register module %s", (target, module, function))

            newrelic.api.import_hook.register_import_hook(target, _module_import_hook(target, module, function))

            _module_import_hook_results.setdefault((target, module, function), None)

    except Exception:
        _raise_instrumentation_error("import-hook", locals())


ASYNCIO_HOOK = ("asyncio", "newrelic.core.trace_cache", "asyncio_loaded")
GREENLET_HOOK = ("greenlet", "newrelic.core.trace_cache", "greenlet_loaded")


def _process_trace_cache_import_hooks():
    _process_module_definition(*GREENLET_HOOK)

    if GREENLET_HOOK not in _module_import_hook_results:
        pass
    elif _module_import_hook_results[GREENLET_HOOK] is None:
        trace_cache.trace_cache().greenlet = False

    _process_module_definition(*ASYNCIO_HOOK)

    if ASYNCIO_HOOK not in _module_import_hook_results:
        pass
    elif _module_import_hook_results[ASYNCIO_HOOK] is None:
        trace_cache.trace_cache().asyncio = False


def _process_module_builtin_defaults():
    _process_module_definition(
        "asyncio.base_events",
        "newrelic.hooks.coroutines_asyncio",
        "instrument_asyncio_base_events",
    )
    _process_module_definition(
        "asyncio.events",
        "newrelic.hooks.coroutines_asyncio",
        "instrument_asyncio_events",
    )

    _process_module_definition("asgiref.sync", "newrelic.hooks.adapter_asgiref", "instrument_asgiref_sync")

    _process_module_definition(
        "django.core.handlers.base",
        "newrelic.hooks.framework_django",
        "instrument_django_core_handlers_base",
    )
    _process_module_definition(
        "django.core.handlers.asgi",
        "newrelic.hooks.framework_django",
        "instrument_django_core_handlers_asgi",
    )
    _process_module_definition(
        "django.core.handlers.wsgi",
        "newrelic.hooks.framework_django",
        "instrument_django_core_handlers_wsgi",
    )
    _process_module_definition(
        "django.core.urlresolvers",
        "newrelic.hooks.framework_django",
        "instrument_django_core_urlresolvers",
    )
    _process_module_definition(
        "django.template",
        "newrelic.hooks.framework_django",
        "instrument_django_template",
    )
    _process_module_definition(
        "django.template.loader_tags",
        "newrelic.hooks.framework_django",
        "instrument_django_template_loader_tags",
    )
    _process_module_definition(
        "django.core.servers.basehttp",
        "newrelic.hooks.framework_django",
        "instrument_django_core_servers_basehttp",
    )
    _process_module_definition(
        "django.contrib.staticfiles.views",
        "newrelic.hooks.framework_django",
        "instrument_django_contrib_staticfiles_views",
    )
    _process_module_definition(
        "django.contrib.staticfiles.handlers",
        "newrelic.hooks.framework_django",
        "instrument_django_contrib_staticfiles_handlers",
    )
    _process_module_definition(
        "django.views.debug",
        "newrelic.hooks.framework_django",
        "instrument_django_views_debug",
    )
    _process_module_definition(
        "django.http.multipartparser",
        "newrelic.hooks.framework_django",
        "instrument_django_http_multipartparser",
    )
    _process_module_definition(
        "django.core.mail",
        "newrelic.hooks.framework_django",
        "instrument_django_core_mail",
    )
    _process_module_definition(
        "django.core.mail.message",
        "newrelic.hooks.framework_django",
        "instrument_django_core_mail_message",
    )
    _process_module_definition(
        "django.views.generic.base",
        "newrelic.hooks.framework_django",
        "instrument_django_views_generic_base",
    )
    _process_module_definition(
        "django.core.management.base",
        "newrelic.hooks.framework_django",
        "instrument_django_core_management_base",
    )
    _process_module_definition(
        "django.template.base",
        "newrelic.hooks.framework_django",
        "instrument_django_template_base",
    )
    _process_module_definition(
        "django.middleware.gzip",
        "newrelic.hooks.framework_django",
        "instrument_django_gzip_middleware",
    )

    # New modules in Django 1.10
    _process_module_definition(
        "django.urls.resolvers",
        "newrelic.hooks.framework_django",
        "instrument_django_core_urlresolvers",
    )
    _process_module_definition(
        "django.urls.base",
        "newrelic.hooks.framework_django",
        "instrument_django_urls_base",
    )
    _process_module_definition(
        "django.core.handlers.exception",
        "newrelic.hooks.framework_django",
        "instrument_django_core_handlers_exception",
    )

    _process_module_definition("falcon.api", "newrelic.hooks.framework_falcon", "instrument_falcon_api")
    _process_module_definition("falcon.app", "newrelic.hooks.framework_falcon", "instrument_falcon_app")
    _process_module_definition(
        "falcon.routing.util",
        "newrelic.hooks.framework_falcon",
        "instrument_falcon_routing_util",
    )

    _process_module_definition(
        "fastapi.routing",
        "newrelic.hooks.framework_fastapi",
        "instrument_fastapi_routing",
    )

    _process_module_definition("flask.app", "newrelic.hooks.framework_flask", "instrument_flask_app")
    _process_module_definition(
        "flask.templating",
        "newrelic.hooks.framework_flask",
        "instrument_flask_templating",
    )
    _process_module_definition(
        "flask.blueprints",
        "newrelic.hooks.framework_flask",
        "instrument_flask_blueprints",
    )
    _process_module_definition("flask.views", "newrelic.hooks.framework_flask", "instrument_flask_views")

    _process_module_definition(
        "flask_compress",
        "newrelic.hooks.middleware_flask_compress",
        "instrument_flask_compress",
    )

    _process_module_definition("flask_restful", "newrelic.hooks.component_flask_rest", "instrument_flask_rest")
    _process_module_definition(
        "flask_restplus.api",
        "newrelic.hooks.component_flask_rest",
        "instrument_flask_rest",
    )
    _process_module_definition(
        "flask_restx.api",
        "newrelic.hooks.component_flask_rest",
        "instrument_flask_rest",
    )

    _process_module_definition(
        "graphql_server",
        "newrelic.hooks.component_graphqlserver",
        "instrument_graphqlserver",
    )

    # _process_module_definition('web.application',
    #        'newrelic.hooks.framework_webpy')
    # _process_module_definition('web.template',
    #        'newrelic.hooks.framework_webpy')

    _process_module_definition(
        "gluon.compileapp",
        "newrelic.hooks.framework_web2py",
        "instrument_gluon_compileapp",
    )
    _process_module_definition(
        "gluon.restricted",
        "newrelic.hooks.framework_web2py",
        "instrument_gluon_restricted",
    )
    _process_module_definition("gluon.main", "newrelic.hooks.framework_web2py", "instrument_gluon_main")
    _process_module_definition("gluon.template", "newrelic.hooks.framework_web2py", "instrument_gluon_template")
    _process_module_definition("gluon.tools", "newrelic.hooks.framework_web2py", "instrument_gluon_tools")
    _process_module_definition("gluon.http", "newrelic.hooks.framework_web2py", "instrument_gluon_http")

    _process_module_definition("httpx._client", "newrelic.hooks.external_httpx", "instrument_httpx_client")

    _process_module_definition("gluon.contrib.feedparser", "newrelic.hooks.external_feedparser")
    _process_module_definition("gluon.contrib.memcache.memcache", "newrelic.hooks.memcache_memcache")

    _process_module_definition(
        "graphene.types.schema",
        "newrelic.hooks.framework_graphene",
        "instrument_graphene_types_schema",
    )

    _process_module_definition(
        "graphql.graphql",
        "newrelic.hooks.framework_graphql",
        "instrument_graphql",
    )
    _process_module_definition(
        "graphql.execution.execute",
        "newrelic.hooks.framework_graphql",
        "instrument_graphql_execute",
    )
    _process_module_definition(
        "graphql.execution.executor",
        "newrelic.hooks.framework_graphql",
        "instrument_graphql_execute",
    )
    _process_module_definition(
        "graphql.execution.middleware",
        "newrelic.hooks.framework_graphql",
        "instrument_graphql_execution_middleware",
    )
    _process_module_definition(
        "graphql.execution.utils",
        "newrelic.hooks.framework_graphql",
        "instrument_graphql_execution_utils",
    )
    _process_module_definition(
        "graphql.error.located_error",
        "newrelic.hooks.framework_graphql",
        "instrument_graphql_error_located_error",
    )
    _process_module_definition(
        "graphql.language.parser",
        "newrelic.hooks.framework_graphql",
        "instrument_graphql_parser",
    )
    _process_module_definition(
        "graphql.validation.validate",
        "newrelic.hooks.framework_graphql",
        "instrument_graphql_validate",
    )
    _process_module_definition(
        "graphql.validation.validation",
        "newrelic.hooks.framework_graphql",
        "instrument_graphql_validate",
    )

    _process_module_definition(
        "ariadne.asgi",
        "newrelic.hooks.framework_ariadne",
        "instrument_ariadne_asgi",
    )
    _process_module_definition(
        "ariadne.graphql",
        "newrelic.hooks.framework_ariadne",
        "instrument_ariadne_execute",
    )
    _process_module_definition(
        "ariadne.wsgi",
        "newrelic.hooks.framework_ariadne",
        "instrument_ariadne_wsgi",
    )

    _process_module_definition("grpc._channel", "newrelic.hooks.framework_grpc", "instrument_grpc__channel")
    _process_module_definition("grpc._server", "newrelic.hooks.framework_grpc", "instrument_grpc_server")

    _process_module_definition("pylons.wsgiapp", "newrelic.hooks.framework_pylons")
    _process_module_definition("pylons.controllers.core", "newrelic.hooks.framework_pylons")
    _process_module_definition("pylons.templating", "newrelic.hooks.framework_pylons")

    _process_module_definition("bottle", "newrelic.hooks.framework_bottle", "instrument_bottle")

    _process_module_definition(
        "cherrypy._cpreqbody",
        "newrelic.hooks.framework_cherrypy",
        "instrument_cherrypy__cpreqbody",
    )
    _process_module_definition(
        "cherrypy._cprequest",
        "newrelic.hooks.framework_cherrypy",
        "instrument_cherrypy__cprequest",
    )
    _process_module_definition(
        "cherrypy._cpdispatch",
        "newrelic.hooks.framework_cherrypy",
        "instrument_cherrypy__cpdispatch",
    )
    _process_module_definition(
        "cherrypy._cpwsgi",
        "newrelic.hooks.framework_cherrypy",
        "instrument_cherrypy__cpwsgi",
    )
    _process_module_definition(
        "cherrypy._cptree",
        "newrelic.hooks.framework_cherrypy",
        "instrument_cherrypy__cptree",
    )

    _process_module_definition(
        "paste.httpserver",
        "newrelic.hooks.adapter_paste",
        "instrument_paste_httpserver",
    )

    _process_module_definition(
        "gunicorn.app.base",
        "newrelic.hooks.adapter_gunicorn",
        "instrument_gunicorn_app_base",
    )

    _process_module_definition("cx_Oracle", "newrelic.hooks.database_cx_oracle", "instrument_cx_oracle")

    _process_module_definition("ibm_db_dbi", "newrelic.hooks.database_ibm_db_dbi", "instrument_ibm_db_dbi")

    _process_module_definition("mysql.connector", "newrelic.hooks.database_mysql", "instrument_mysql_connector")
    _process_module_definition("MySQLdb", "newrelic.hooks.database_mysqldb", "instrument_mysqldb")
    _process_module_definition("oursql", "newrelic.hooks.database_oursql", "instrument_oursql")
    _process_module_definition("pymysql", "newrelic.hooks.database_pymysql", "instrument_pymysql")

    _process_module_definition("pyodbc", "newrelic.hooks.database_pyodbc", "instrument_pyodbc")

    _process_module_definition("pymssql", "newrelic.hooks.database_pymssql", "instrument_pymssql")

    _process_module_definition("psycopg2", "newrelic.hooks.database_psycopg2", "instrument_psycopg2")
    _process_module_definition(
        "psycopg2._psycopg2",
        "newrelic.hooks.database_psycopg2",
        "instrument_psycopg2__psycopg2",
    )
    _process_module_definition(
        "psycopg2.extensions",
        "newrelic.hooks.database_psycopg2",
        "instrument_psycopg2_extensions",
    )
    _process_module_definition(
        "psycopg2._json",
        "newrelic.hooks.database_psycopg2",
        "instrument_psycopg2__json",
    )
    _process_module_definition(
        "psycopg2._range",
        "newrelic.hooks.database_psycopg2",
        "instrument_psycopg2__range",
    )
    _process_module_definition("psycopg2.sql", "newrelic.hooks.database_psycopg2", "instrument_psycopg2_sql")

    _process_module_definition("psycopg2ct", "newrelic.hooks.database_psycopg2ct", "instrument_psycopg2ct")
    _process_module_definition(
        "psycopg2ct.extensions",
        "newrelic.hooks.database_psycopg2ct",
        "instrument_psycopg2ct_extensions",
    )

    _process_module_definition(
        "psycopg2cffi",
        "newrelic.hooks.database_psycopg2cffi",
        "instrument_psycopg2cffi",
    )
    _process_module_definition(
        "psycopg2cffi.extensions",
        "newrelic.hooks.database_psycopg2cffi",
        "instrument_psycopg2cffi_extensions",
    )

    _process_module_definition(
        "asyncpg.connect_utils",
        "newrelic.hooks.database_asyncpg",
        "instrument_asyncpg_connect_utils",
    )
    _process_module_definition(
        "asyncpg.protocol",
        "newrelic.hooks.database_asyncpg",
        "instrument_asyncpg_protocol",
    )

    _process_module_definition(
        "postgresql.driver.dbapi20",
        "newrelic.hooks.database_postgresql",
        "instrument_postgresql_driver_dbapi20",
    )

    _process_module_definition(
        "postgresql.interface.proboscis.dbapi2",
        "newrelic.hooks.database_postgresql",
        "instrument_postgresql_interface_proboscis_dbapi2",
    )

    _process_module_definition("sqlite3", "newrelic.hooks.database_sqlite", "instrument_sqlite3")
    _process_module_definition("sqlite3.dbapi2", "newrelic.hooks.database_sqlite", "instrument_sqlite3_dbapi2")

    _process_module_definition("pysqlite2", "newrelic.hooks.database_sqlite", "instrument_sqlite3")
    _process_module_definition(
        "pysqlite2.dbapi2",
        "newrelic.hooks.database_sqlite",
        "instrument_sqlite3_dbapi2",
    )

    _process_module_definition("memcache", "newrelic.hooks.datastore_memcache", "instrument_memcache")
    _process_module_definition("umemcache", "newrelic.hooks.datastore_umemcache", "instrument_umemcache")
    _process_module_definition(
        "pylibmc.client",
        "newrelic.hooks.datastore_pylibmc",
        "instrument_pylibmc_client",
    )
    _process_module_definition(
        "bmemcached.client",
        "newrelic.hooks.datastore_bmemcached",
        "instrument_bmemcached_client",
    )
    _process_module_definition(
        "pymemcache.client",
        "newrelic.hooks.datastore_pymemcache",
        "instrument_pymemcache_client",
    )

    _process_module_definition("jinja2.environment", "newrelic.hooks.template_jinja2")

    _process_module_definition("mako.runtime", "newrelic.hooks.template_mako", "instrument_mako_runtime")
    _process_module_definition("mako.template", "newrelic.hooks.template_mako", "instrument_mako_template")

    _process_module_definition("genshi.template.base", "newrelic.hooks.template_genshi")

    if six.PY2:
        _process_module_definition("httplib", "newrelic.hooks.external_httplib")
    else:
        _process_module_definition("http.client", "newrelic.hooks.external_httplib")

    _process_module_definition("httplib2", "newrelic.hooks.external_httplib2")

    if six.PY2:
        _process_module_definition("urllib", "newrelic.hooks.external_urllib")
    else:
        _process_module_definition("urllib.request", "newrelic.hooks.external_urllib")

    if six.PY2:
        _process_module_definition("urllib2", "newrelic.hooks.external_urllib2")

    _process_module_definition(
        "urllib3.connectionpool",
        "newrelic.hooks.external_urllib3",
        "instrument_urllib3_connectionpool",
    )
    _process_module_definition(
        "urllib3.connection",
        "newrelic.hooks.external_urllib3",
        "instrument_urllib3_connection",
    )
    _process_module_definition(
        "requests.packages.urllib3.connection",
        "newrelic.hooks.external_urllib3",
        "instrument_urllib3_connection",
    )

    _process_module_definition(
        "starlette.requests",
        "newrelic.hooks.framework_starlette",
        "instrument_starlette_requests",
    )
    _process_module_definition(
        "starlette.routing",
        "newrelic.hooks.framework_starlette",
        "instrument_starlette_routing",
    )
    _process_module_definition(
        "starlette.applications",
        "newrelic.hooks.framework_starlette",
        "instrument_starlette_applications",
    )
    _process_module_definition(
        "starlette.middleware.errors",
        "newrelic.hooks.framework_starlette",
        "instrument_starlette_middleware_errors",
    )
    _process_module_definition(
        "starlette.exceptions",
        "newrelic.hooks.framework_starlette",
        "instrument_starlette_exceptions",
    )
    _process_module_definition(
        "starlette.background",
        "newrelic.hooks.framework_starlette",
        "instrument_starlette_background_task",
    )
    _process_module_definition(
        "starlette.concurrency",
        "newrelic.hooks.framework_starlette",
        "instrument_starlette_concurrency",
    )

    _process_module_definition(
        "strawberry.asgi",
        "newrelic.hooks.framework_strawberry",
        "instrument_strawberry_asgi",
    )

    _process_module_definition(
        "strawberry.schema.schema",
        "newrelic.hooks.framework_strawberry",
        "instrument_strawberry_schema",
    )

    _process_module_definition(
        "strawberry.schema.schema_converter",
        "newrelic.hooks.framework_strawberry",
        "instrument_strawberry_schema_converter",
    )

    _process_module_definition("uvicorn.config", "newrelic.hooks.adapter_uvicorn", "instrument_uvicorn_config")

    _process_module_definition("sanic.app", "newrelic.hooks.framework_sanic", "instrument_sanic_app")
    _process_module_definition("sanic.response", "newrelic.hooks.framework_sanic", "instrument_sanic_response")

    _process_module_definition("aiohttp.wsgi", "newrelic.hooks.framework_aiohttp", "instrument_aiohttp_wsgi")
    _process_module_definition("aiohttp.web", "newrelic.hooks.framework_aiohttp", "instrument_aiohttp_web")
    _process_module_definition(
        "aiohttp.web_reqrep",
        "newrelic.hooks.framework_aiohttp",
        "instrument_aiohttp_web_response",
    )
    _process_module_definition(
        "aiohttp.web_response",
        "newrelic.hooks.framework_aiohttp",
        "instrument_aiohttp_web_response",
    )
    _process_module_definition(
        "aiohttp.web_urldispatcher",
        "newrelic.hooks.framework_aiohttp",
        "instrument_aiohttp_web_urldispatcher",
    )
    _process_module_definition(
        "aiohttp.client",
        "newrelic.hooks.framework_aiohttp",
        "instrument_aiohttp_client",
    )
    _process_module_definition(
        "aiohttp.client_reqrep",
        "newrelic.hooks.framework_aiohttp",
        "instrument_aiohttp_client_reqrep",
    )
    _process_module_definition(
        "aiohttp.protocol",
        "newrelic.hooks.framework_aiohttp",
        "instrument_aiohttp_protocol",
    )

    _process_module_definition("requests.api", "newrelic.hooks.external_requests", "instrument_requests_api")
    _process_module_definition(
        "requests.sessions",
        "newrelic.hooks.external_requests",
        "instrument_requests_sessions",
    )

    _process_module_definition("feedparser", "newrelic.hooks.external_feedparser")

    _process_module_definition("xmlrpclib", "newrelic.hooks.external_xmlrpclib")

    _process_module_definition("dropbox", "newrelic.hooks.external_dropbox")

    _process_module_definition("facepy.graph_api", "newrelic.hooks.external_facepy")

    _process_module_definition("pysolr", "newrelic.hooks.datastore_pysolr", "instrument_pysolr")

    _process_module_definition("solr", "newrelic.hooks.datastore_solrpy", "instrument_solrpy")

    _process_module_definition("aredis.client", "newrelic.hooks.datastore_aredis", "instrument_aredis_client")

    _process_module_definition(
        "aredis.connection",
        "newrelic.hooks.datastore_aredis",
        "instrument_aredis_connection",
    )

    _process_module_definition(
        "elasticsearch.client",
        "newrelic.hooks.datastore_elasticsearch",
        "instrument_elasticsearch_client",
    )
    _process_module_definition(
        "elasticsearch.client.cat",
        "newrelic.hooks.datastore_elasticsearch",
        "instrument_elasticsearch_client_cat",
    )
    _process_module_definition(
        "elasticsearch.client.cluster",
        "newrelic.hooks.datastore_elasticsearch",
        "instrument_elasticsearch_client_cluster",
    )
    _process_module_definition(
        "elasticsearch.client.indices",
        "newrelic.hooks.datastore_elasticsearch",
        "instrument_elasticsearch_client_indices",
    )
    _process_module_definition(
        "elasticsearch.client.nodes",
        "newrelic.hooks.datastore_elasticsearch",
        "instrument_elasticsearch_client_nodes",
    )
    _process_module_definition(
        "elasticsearch.client.snapshot",
        "newrelic.hooks.datastore_elasticsearch",
        "instrument_elasticsearch_client_snapshot",
    )
    _process_module_definition(
        "elasticsearch.client.tasks",
        "newrelic.hooks.datastore_elasticsearch",
        "instrument_elasticsearch_client_tasks",
    )
    _process_module_definition(
        "elasticsearch.client.ingest",
        "newrelic.hooks.datastore_elasticsearch",
        "instrument_elasticsearch_client_ingest",
    )
    _process_module_definition(
        "elasticsearch.connection.base",
        "newrelic.hooks.datastore_elasticsearch",
        "instrument_elasticsearch_connection_base",
    )
    _process_module_definition(
        "elasticsearch.transport",
        "newrelic.hooks.datastore_elasticsearch",
        "instrument_elasticsearch_transport",
    )

    _process_module_definition("pika.adapters", "newrelic.hooks.messagebroker_pika", "instrument_pika_adapters")
    _process_module_definition("pika.channel", "newrelic.hooks.messagebroker_pika", "instrument_pika_channel")
    _process_module_definition("pika.spec", "newrelic.hooks.messagebroker_pika", "instrument_pika_spec")

    _process_module_definition(
        "pyelasticsearch.client",
        "newrelic.hooks.datastore_pyelasticsearch",
        "instrument_pyelasticsearch_client",
    )

    _process_module_definition(
        "pymongo.connection",
        "newrelic.hooks.datastore_pymongo",
        "instrument_pymongo_connection",
    )
    _process_module_definition(
        "pymongo.mongo_client",
        "newrelic.hooks.datastore_pymongo",
        "instrument_pymongo_mongo_client",
    )
    _process_module_definition(
        "pymongo.collection",
        "newrelic.hooks.datastore_pymongo",
        "instrument_pymongo_collection",
    )

    _process_module_definition(
        "redis.connection",
        "newrelic.hooks.datastore_redis",
        "instrument_redis_connection",
    )
    _process_module_definition("redis.client", "newrelic.hooks.datastore_redis", "instrument_redis_client")

    _process_module_definition(
        "redis.commands.core", "newrelic.hooks.datastore_redis", "instrument_redis_commands_core"
    )

    _process_module_definition("motor", "newrelic.hooks.datastore_motor", "patch_motor")

    _process_module_definition(
        "piston.resource",
        "newrelic.hooks.component_piston",
        "instrument_piston_resource",
    )
    _process_module_definition("piston.doc", "newrelic.hooks.component_piston", "instrument_piston_doc")

    _process_module_definition(
        "tastypie.resources",
        "newrelic.hooks.component_tastypie",
        "instrument_tastypie_resources",
    )
    _process_module_definition("tastypie.api", "newrelic.hooks.component_tastypie", "instrument_tastypie_api")

    _process_module_definition(
        "rest_framework.views",
        "newrelic.hooks.component_djangorestframework",
        "instrument_rest_framework_views",
    )
    _process_module_definition(
        "rest_framework.decorators",
        "newrelic.hooks.component_djangorestframework",
        "instrument_rest_framework_decorators",
    )

    _process_module_definition(
        "celery.task.base",
        "newrelic.hooks.application_celery",
        "instrument_celery_app_task",
    )
    _process_module_definition(
        "celery.app.task",
        "newrelic.hooks.application_celery",
        "instrument_celery_app_task",
    )
    _process_module_definition("celery.worker", "newrelic.hooks.application_celery", "instrument_celery_worker")
    _process_module_definition(
        "celery.concurrency.processes",
        "newrelic.hooks.application_celery",
        "instrument_celery_worker",
    )
    _process_module_definition(
        "celery.concurrency.prefork",
        "newrelic.hooks.application_celery",
        "instrument_celery_worker",
    )
    # _process_module_definition('celery.loaders.base',
    #        'newrelic.hooks.application_celery',
    #        'instrument_celery_loaders_base')
    _process_module_definition(
        "celery.execute.trace",
        "newrelic.hooks.application_celery",
        "instrument_celery_execute_trace",
    )
    _process_module_definition(
        "celery.task.trace",
        "newrelic.hooks.application_celery",
        "instrument_celery_execute_trace",
    )
    _process_module_definition(
        "celery.app.trace",
        "newrelic.hooks.application_celery",
        "instrument_celery_execute_trace",
    )
    _process_module_definition("billiard.pool", "newrelic.hooks.application_celery", "instrument_billiard_pool")

    _process_module_definition("flup.server.cgi", "newrelic.hooks.adapter_flup", "instrument_flup_server_cgi")
    _process_module_definition(
        "flup.server.ajp_base",
        "newrelic.hooks.adapter_flup",
        "instrument_flup_server_ajp_base",
    )
    _process_module_definition(
        "flup.server.fcgi_base",
        "newrelic.hooks.adapter_flup",
        "instrument_flup_server_fcgi_base",
    )
    _process_module_definition(
        "flup.server.scgi_base",
        "newrelic.hooks.adapter_flup",
        "instrument_flup_server_scgi_base",
    )

    _process_module_definition("pywapi", "newrelic.hooks.external_pywapi", "instrument_pywapi")

    _process_module_definition(
        "meinheld.server",
        "newrelic.hooks.adapter_meinheld",
        "instrument_meinheld_server",
    )

    _process_module_definition(
        "waitress.server",
        "newrelic.hooks.adapter_waitress",
        "instrument_waitress_server",
    )

    _process_module_definition("gevent.wsgi", "newrelic.hooks.adapter_gevent", "instrument_gevent_wsgi")
    _process_module_definition("gevent.pywsgi", "newrelic.hooks.adapter_gevent", "instrument_gevent_pywsgi")

    _process_module_definition(
        "wsgiref.simple_server",
        "newrelic.hooks.adapter_wsgiref",
        "instrument_wsgiref_simple_server",
    )

    _process_module_definition(
        "cherrypy.wsgiserver",
        "newrelic.hooks.adapter_cherrypy",
        "instrument_cherrypy_wsgiserver",
    )

    _process_module_definition(
        "cheroot.wsgi",
        "newrelic.hooks.adapter_cheroot",
        "instrument_cheroot_wsgiserver",
    )

    _process_module_definition(
        "pyramid.router",
        "newrelic.hooks.framework_pyramid",
        "instrument_pyramid_router",
    )
    _process_module_definition(
        "pyramid.config",
        "newrelic.hooks.framework_pyramid",
        "instrument_pyramid_config_views",
    )
    _process_module_definition(
        "pyramid.config.views",
        "newrelic.hooks.framework_pyramid",
        "instrument_pyramid_config_views",
    )
    _process_module_definition(
        "pyramid.config.tweens",
        "newrelic.hooks.framework_pyramid",
        "instrument_pyramid_config_tweens",
    )

    _process_module_definition(
        "cornice.service",
        "newrelic.hooks.component_cornice",
        "instrument_cornice_service",
    )

    # _process_module_definition('twisted.web.server',
    #        'newrelic.hooks.framework_twisted',
    #        'instrument_twisted_web_server')
    # _process_module_definition('twisted.web.http',
    #        'newrelic.hooks.framework_twisted',
    #        'instrument_twisted_web_http')
    # _process_module_definition('twisted.web.resource',
    #        'newrelic.hooks.framework_twisted',
    #        'instrument_twisted_web_resource')
    # _process_module_definition('twisted.internet.defer',
    #        'newrelic.hooks.framework_twisted',
    #        'instrument_twisted_internet_defer')

    _process_module_definition("gevent.monkey", "newrelic.hooks.coroutines_gevent", "instrument_gevent_monkey")

    _process_module_definition(
        "weberror.errormiddleware",
        "newrelic.hooks.middleware_weberror",
        "instrument_weberror_errormiddleware",
    )
    _process_module_definition(
        "weberror.reporter",
        "newrelic.hooks.middleware_weberror",
        "instrument_weberror_reporter",
    )

    _process_module_definition("thrift.transport.TSocket", "newrelic.hooks.external_thrift")

    _process_module_definition(
        "gearman.client",
        "newrelic.hooks.application_gearman",
        "instrument_gearman_client",
    )
    _process_module_definition(
        "gearman.connection_manager",
        "newrelic.hooks.application_gearman",
        "instrument_gearman_connection_manager",
    )
    _process_module_definition(
        "gearman.worker",
        "newrelic.hooks.application_gearman",
        "instrument_gearman_worker",
    )

    _process_module_definition(
        "botocore.endpoint",
        "newrelic.hooks.external_botocore",
        "instrument_botocore_endpoint",
    )
    _process_module_definition(
        "botocore.client",
        "newrelic.hooks.external_botocore",
        "instrument_botocore_client",
    )

    _process_module_definition(
        "tornado.httpserver",
        "newrelic.hooks.framework_tornado",
        "instrument_tornado_httpserver",
    )
    _process_module_definition(
        "tornado.httputil",
        "newrelic.hooks.framework_tornado",
        "instrument_tornado_httputil",
    )
    _process_module_definition(
        "tornado.httpclient",
        "newrelic.hooks.framework_tornado",
        "instrument_tornado_httpclient",
    )
    _process_module_definition(
        "tornado.routing",
        "newrelic.hooks.framework_tornado",
        "instrument_tornado_routing",
    )
    _process_module_definition("tornado.web", "newrelic.hooks.framework_tornado", "instrument_tornado_web")


def _process_module_entry_points():
    try:
        import pkg_resources
    except ImportError:
        return

    group = "newrelic.hooks"

    for entrypoint in pkg_resources.iter_entry_points(group=group):
        target = entrypoint.name

        if target in _module_import_hook_registry:
            continue

        module = entrypoint.module_name

        if entrypoint.attrs:
            function = ".".join(entrypoint.attrs)
        else:
            function = "instrument"

        _process_module_definition(target, module, function)


_instrumentation_done = False


def _setup_instrumentation():

    global _instrumentation_done

    if _instrumentation_done:
        return

    _instrumentation_done = True

    _process_module_configuration()
    _process_module_entry_points()
    _process_trace_cache_import_hooks()
    _process_module_builtin_defaults()

    _process_wsgi_application_configuration()
    _process_background_task_configuration()

    _process_database_trace_configuration()
    _process_external_trace_configuration()
    _process_function_trace_configuration()
    _process_generator_trace_configuration()
    _process_profile_trace_configuration()
    _process_memcache_trace_configuration()

    _process_transaction_name_configuration()

    _process_error_trace_configuration()

    _process_data_source_configuration()

    _process_function_profile_configuration()


def _setup_extensions():
    try:
        import pkg_resources
    except ImportError:
        return

    group = "newrelic.extension"

    for entrypoint in pkg_resources.iter_entry_points(group=group):
        __import__(entrypoint.module_name)
        module = sys.modules[entrypoint.module_name]
        module.initialize()


_console = None


def _startup_agent_console():
    global _console

    if _console:
        return

    _console = newrelic.console.ConnectionManager(_settings.console.listener_socket)


def _setup_agent_console():
    if _settings.console.listener_socket:
        newrelic.core.agent.Agent.run_on_startup(_startup_agent_console)


def initialize(
    config_file=None,
    environment=None,
    ignore_errors=None,
    log_file=None,
    log_level=None,
):
    if config_file is None:
        config_file = os.environ.get("NEW_RELIC_CONFIG_FILE", None)

    if environment is None:
        environment = os.environ.get("NEW_RELIC_ENVIRONMENT", None)

    if ignore_errors is None:
        ignore_errors = newrelic.core.config._environ_as_bool("NEW_RELIC_IGNORE_STARTUP_ERRORS", True)

    _load_configuration(config_file, environment, ignore_errors, log_file, log_level)

    if _settings.monitor_mode or _settings.developer_mode:
        _settings.enabled = True
        _setup_instrumentation()
        _setup_data_source()
        _setup_extensions()
        _setup_agent_console()
    else:
        _settings.enabled = False


def filter_app_factory(app, global_conf, config_file, environment=None):
    initialize(config_file, environment)
    return newrelic.api.wsgi_application.WSGIApplicationWrapper(app)

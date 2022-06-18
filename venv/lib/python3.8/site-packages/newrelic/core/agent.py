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

"""This module holds the Agent class which is the primary interface for
interacting with the agent core.

"""

from __future__ import print_function

import atexit
import logging
import os
import sched
import sys
import threading
import time
import traceback
import warnings

import newrelic
import newrelic.core.application
import newrelic.core.config
import newrelic.packages.six as six
from newrelic.common.log_file import initialize_logging
from newrelic.core.thread_utilization import thread_utilization_data_source
from newrelic.samplers.cpu_usage import cpu_usage_data_source
from newrelic.samplers.gc_data import garbage_collector_data_source
from newrelic.samplers.memory_usage import memory_usage_data_source

_logger = logging.getLogger(__name__)


def check_environment():
    # If running under uWSGI, then must be version 1.2.6 or newer. Must
    # also be run with '--enable-threads' option.

    if "uwsgi" in sys.modules:
        import uwsgi

        if not hasattr(uwsgi, "version_info"):
            _logger.warning(
                "The New Relic Python Agent requires version "
                "1.2.6 or newer of uWSGI. The newer "
                "version is required because older versions of uWSGI "
                "have a bug whereby it is not compliant with the WSGI "
                "(PEP 333) specification. This bug in uWSGI will result "
                "in data being reported incorrectly. For more details see "
                "https://newrelic.com/docs/python/python-agent-and-uwsgi."
            )
        elif hasattr(uwsgi, "version_info") and uwsgi.version_info[:3] < (1, 2, 6):
            _logger.warning(
                "The New Relic Python Agent requires version "
                "1.2.6 or newer of uWSGI, you are using %r. The newer "
                "version is required because older versions of uWSGI "
                "have a bug whereby it is not compliant with the WSGI "
                "(PEP 333) specification. This bug in uWSGI will result "
                "in data being reported incorrectly. For more details see "
                "https://newrelic.com/docs/python/python-agent-and-uwsgi.",
                ".".join(map(str, uwsgi.version_info[:3])),
            )

        if hasattr(uwsgi, "opt") and hasattr(uwsgi.opt, "get") and not uwsgi.opt.get("enable-threads"):
            _logger.warning(
                "The New Relic Python Agent requires that when "
                "using uWSGI that the enable-threads option be given "
                "to uwsgi when it is run. If the option is not supplied "
                "then threading will not be enabled and you will see no "
                "data being reported by the agent. For more details see "
                "https://newrelic.com/docs/python/python-agent-and-uwsgi."
            )


class Agent(object):

    """Only one instance of the agent should ever exist and that can be
    obtained using the agent_instance() function.

    The licence key information, network connection details for the
    collector, plus whether SSL should be used is obtained directly from
    the global configuration settings. If a proxy has to be used, details
    for that will similarly come from the global configuration settings.

    The global configuration settings would normally be setup from the
    agent configuration file or could also be set explicitly. Direct access
    to global configuration settings prior to the agent instance being
    created needs to be via the 'newrelic.core.config' module.

    After the network connection details have been set, and the agent
    object created and accessed using the agent_instance() function, each
    individual reporting application can be activated using the
    activate_application() method of the agent. The name of the primary
    application and an optional list of linked applications to which metric
    data should also be reported needs to be supplied.

    Once an application has been activated and communications established
    with the core application, the application specific settings, which
    consists of the global default configuration settings overlaid with the
    server side configuration settings can be obtained using the
    application_settings() method. That a valid settings object rather than
    None is returned is the indicator that the application has been
    successfully activated. The application settings object can be
    associated with a transaction so that settings are available for the
    life of the transaction, but should not be cached and used across
    transactions. Instead the application settings object should be
    requested on each transaction to ensure that it is detected whether
    application is still active or not due to a server side triggered
    restart. When such a restart occurs, the application settings could
    change and thus why application settings cannot be cached beyond the
    lifetime of a single transaction.

    """

    _instance_lock = threading.Lock()
    _instance = None
    _startup_callables = []
    _registration_callables = {}

    @staticmethod
    def run_on_startup(callable):  # pylint: disable=W0622
        Agent._startup_callables.append(callable)

    @staticmethod
    def run_on_registration(application, callable):  # pylint: disable=W0622
        callables = Agent._registration_callables.setdefault(application, [])
        callables.append(callable)

    @staticmethod
    def agent_singleton():
        """Used by the agent_instance() function to access/create the
        single agent object instance.

        """

        if Agent._instance:
            return Agent._instance

        settings = newrelic.core.config.global_settings()

        # Just in case that the main initialisation function
        # wasn't called to read in a configuration file and as
        # such the logging system was not initialised already,
        # we trigger initialisation again here.

        initialize_logging(settings.log_file, settings.log_level)

        _logger.info("New Relic Python Agent (%s)" % newrelic.version)

        check_environment()

        if "NEW_RELIC_ADMIN_COMMAND" in os.environ:
            if settings.debug.log_agent_initialization:
                _logger.info(
                    "Monitored application started using the newrelic-admin command with command line of %s.",
                    os.environ["NEW_RELIC_ADMIN_COMMAND"],
                )
            else:
                _logger.debug(
                    "Monitored application started using the newrelic-admin command with command line of %s.",
                    os.environ["NEW_RELIC_ADMIN_COMMAND"],
                )

        with Agent._instance_lock:
            if not Agent._instance:
                if settings.debug.log_agent_initialization:
                    _logger.info("Creating instance of Python agent in process %d.", os.getpid())
                    _logger.info("Agent was initialized from: %r", "".join(traceback.format_stack()[:-1]))
                else:
                    _logger.debug("Creating instance of Python agent in process %d.", os.getpid())
                    _logger.debug("Agent was initialized from: %r", "".join(traceback.format_stack()[:-1]))

                instance = Agent(settings)
                _logger.debug("Registering builtin data sources.")

                instance.register_data_source(cpu_usage_data_source)
                instance.register_data_source(memory_usage_data_source)
                instance.register_data_source(thread_utilization_data_source)
                instance.register_data_source(garbage_collector_data_source)

                Agent._instance = instance

        return Agent._instance

    def __init__(self, config):
        """Initialises the agent and attempt to establish a connection
        to the core application. Will start the harvest loop running but
        will not activate any applications.

        """

        _logger.debug("Initializing Python agent.")

        self._creation_time = time.time()
        self._process_id = os.getpid()

        self._applications = {}
        self._config = config

        self._harvest_thread = threading.Thread(target=self._harvest_loop, name="NR-Harvest-Thread")
        self._harvest_thread.daemon = True
        self._harvest_shutdown = threading.Event()

        self._default_harvest_count = 0
        self._flexible_harvest_count = 0
        self._last_default_harvest = 0.0
        self._last_flexible_harvest = 0.0
        self._default_harvest_duration = 0.0
        self._flexible_harvest_duration = 0.0
        self._scheduler = sched.scheduler(self._harvest_timer, self._harvest_shutdown.wait)

        self._process_shutdown = False

        self._lock = threading.Lock()

        if self._config.enabled:
            atexit.register(self._atexit_shutdown)

            # Register an atexit hook for uwsgi to facilitate the graceful
            # reload of workers. This is necessary for uwsgi with gevent
            # workers, since the graceful reload waits for all greenlets to
            # join, but our NR background greenlet will never join since it has
            # to stay alive indefinitely. But if we register our agent shutdown
            # to the uwsgi's atexit hook, then the reload will trigger the
            # atexit hook, thus shutting down our agent thread. We should
            # append our atexit hook to any pre-existing ones to prevent
            # overwriting them.

            if "uwsgi" in sys.modules:
                import uwsgi

                uwsgi_original_atexit_callback = getattr(uwsgi, "atexit", None)

                def uwsgi_atexit_callback():
                    self._atexit_shutdown()
                    if uwsgi_original_atexit_callback:
                        uwsgi_original_atexit_callback()

                uwsgi.atexit = uwsgi_atexit_callback

        self._data_sources = {}

    def dump(self, file):
        """Dumps details about the agent to the file object."""

        print("Time Created: %s" % (time.asctime(time.localtime(self._creation_time))), file=file)
        print("Initialization PID: %s" % (self._process_id), file=file)
        print("Default Harvest Count: %d" % (self._default_harvest_count), file=file)
        print("Flexible Harvest Count: %d" % (self._flexible_harvest_count), file=file)
        print("Last Default Harvest: %s" % (time.asctime(time.localtime(self._last_default_harvest))), file=file)
        print("Last Flexible Harvest: %s" % (time.asctime(time.localtime(self._last_flexible_harvest))), file=file)
        print("Default Harvest Duration: %.2f" % (self._default_harvest_duration), file=file)
        print("Flexible Harvest Duration: %.2f" % (self._flexible_harvest_duration), file=file)
        print("Agent Shutdown: %s" % (self._harvest_shutdown.isSet()), file=file)
        print("Applications: %r" % (sorted(self._applications.keys())), file=file)

    def global_settings(self):
        """Returns the global default settings object. If access is
        needed to this prior to initialising the agent, use the
        'newrelic.core.config' module directly.

        """

        return newrelic.core.config.global_settings()

    def application_settings(self, app_name):
        """Returns the application specific settings object. This only
        returns a valid settings object once a connection has been
        established to the core application and the application server
        side settings have been obtained. If this returns None then
        activate_application() should be used to force activation for
        the agent in case that hasn't been done previously.

        """

        application = self._applications.get(app_name)

        if application:
            return application.configuration

    def application_attribute_filter(self, app_name):
        """Returns the attribute filter for the application."""

        application = self._applications.get(app_name)
        if application:
            return application.attribute_filter

    def activate_application(self, app_name, linked_applications=None, timeout=None, uninstrumented_modules=None):
        """Initiates activation for the named application if this has
        not been done previously. If an attempt to trigger the
        activation of the application has already been performed,
        whether or not that has completed, calling this again will
        have no affect.

        The list of linked applications is the additional applications
        to which data should also be reported in addition to the primary
        application.

        The timeout is how long to wait for the initial connection. The
        timeout only applies the first time a specific named application
        is being activated. The timeout would be used by test harnesses
        and can't really be used by activation of application for first
        request because it could take a second or more for initial
        handshake to get back configuration settings for application.

        """
        linked_applications = linked_applications if linked_applications is not None else []

        if not self._config.enabled:
            return

        # If timeout not supplied then use default from the global
        # configuration. Note that the timeout only applies on the first
        # call to activate the application.

        settings = newrelic.core.config.global_settings()

        if timeout is None:
            # In serverless mode, we should always wait for startup since it
            # should take almost no time to create the session (no network
            # activity).
            if settings.serverless_mode.enabled:
                timeout = 10.0
            else:
                timeout = settings.startup_timeout

        activate_session = False

        with self._lock:
            application = self._applications.get(app_name, None)
            if not application:

                process_id = os.getpid()

                if process_id != self._process_id:
                    _logger.warning(
                        "Attempt to activate application in a process "
                        "different to where the agent harvest thread was "
                        "started. No data will be reported for this "
                        "process with pid of %d. Creation of the harvest "
                        "thread this application occurred in process with "
                        "pid %d. If no data at all is being reported for "
                        "your application, see "
                        "https://docs.newrelic.com/docs/agents/"
                        "python-agent/troubleshooting/"
                        "activate-application-warning-python "
                        "for troubleshooting steps. If the issue "
                        "persists, please send debug logs to New Relic "
                        "support for assistance.",
                        process_id,
                        self._process_id,
                    )

                if settings.debug.log_agent_initialization:
                    _logger.info("Creating application instance for %r in process %d.", app_name, os.getpid())
                    _logger.info("Application was activated from: %r", "".join(traceback.format_stack()[:-1]))
                else:
                    _logger.debug("Creating application instance for %r in process %d.", app_name, os.getpid())
                    _logger.debug("Application was activated from: %r", "".join(traceback.format_stack()[:-1]))

                linked_applications = sorted(set(linked_applications))
                application = newrelic.core.application.Application(app_name, linked_applications)
                application._uninstrumented = uninstrumented_modules
                self._applications[app_name] = application
                activate_session = True

                # Register any data sources with the application.

                for source, name, settings, properties in self._data_sources.get(None, []):
                    application.register_data_source(source, name, settings, **properties)

                for source, name, settings, properties in self._data_sources.get(app_name, []):
                    application.register_data_source(source, name, settings, **properties)

            else:
                # Do some checks to see whether try to reactivate the
                # application in a different process to what it was
                # originally activated in.

                application.validate_process()

            # Activate the session if application was just created and wait
            # for session activation if a timeout was specified. This may
            # bail out early if is detected that a deadlock may occur for
            # the period of the timeout.

            if activate_session:
                application.activate_session(self.activate_agent, timeout)

    @property
    def applications(self):
        """Returns a dictionary of the internal application objects
        corresponding to the applications for which activation has already
        been requested. This does not reflect whether activation has been
        successful or not. To determine if application is currently in an
        activated state use application_settings() method to see if a valid
        application settings objects is available or query the application
        object directly.

        """

        return self._applications

    def application(self, app_name):
        """Returns the internal application object for the named
        application or None if not created. When an application object
        is returned, it does not reflect whether activation has been
        successful or not. To determine if application is currently in an
        activated state use application_settings() method to see if a valid
        application settings objects is available or query the application
        object directly.

        """

        return self._applications.get(app_name, None)

    def register_data_source(self, source, application=None, name=None, settings=None, **properties):
        """Registers the specified data source."""

        _logger.debug("Register data source with agent %r.", (source, application, name, settings, properties))

        with self._lock:
            # Remember the data sources in case we need them later.

            self._data_sources.setdefault(application, []).append((source, name, settings, properties))

            if application is None:
                # Bind to any applications that already exist.

                for application in list(six.itervalues(self._applications)):
                    application.register_data_source(source, name, settings, **properties)

            else:
                # Bind to specific application if it exists.

                instance = self._applications.get(application)

                if instance is not None:
                    instance.register_data_source(source, name, settings, **properties)

    def remove_thread_utilization(self):

        _logger.debug("Removing thread utilization data source from all applications")

        source_name = thread_utilization_data_source.__name__
        factory_name = "Thread Utilization"

        with self._lock:
            source_names = [s[0].__name__ for s in self._data_sources[None]]
            if source_name in source_names:
                idx = source_names.index(source_name)
                self._data_sources[None].pop(idx)

            # Clear out the data samplers that add thread utilization custom
            # metrics every harvest (for each application)

            for application in self._applications.values():
                application.remove_data_source(factory_name)

        # The thread utilization data source may have been started, so we
        # must clear out the list of trackers that transactions will use to add
        # thread.concurrency attributes

        from newrelic.core.thread_utilization import _utilization_trackers

        _utilization_trackers.clear()

    def record_exception(self, app_name, exc=None, value=None, tb=None, params=None, ignore_errors=None):
        # Deprecation Warning
        warnings.warn(
            ("The record_exception function is deprecated. Please use the new api named notice_error instead."),
            DeprecationWarning,
        )

        self.notice_error(app_name, error=(exc, value, tb), attributes=params, ignore=ignore_errors)

    def notice_error(self, app_name, error=None, attributes=None, expected=None, ignore=None, status_code=None):
        application = self._applications.get(app_name, None)
        if application is None or not application.active:
            return

        application.notice_error(
            error=error,
            attributes=attributes,
            expected=expected,
            ignore=ignore,
            status_code=status_code,
        )

    def record_custom_metric(self, app_name, name, value):
        """Records a basic metric for the named application. If there has
        been no prior request to activate the application, the metric is
        discarded.

        """

        application = self._applications.get(app_name, None)
        if application is None or not application.active:
            return

        application.record_custom_metric(name, value)

    def record_custom_metrics(self, app_name, metrics):
        """Records the metrics for the named application. If there has
        been no prior request to activate the application, the metric is
        discarded. The metrics should be an iterable yielding tuples
        consisting of the name and value.

        """

        application = self._applications.get(app_name, None)
        if application is None or not application.active:
            return

        application.record_custom_metrics(metrics)

    def record_custom_event(self, app_name, event_type, params):
        application = self._applications.get(app_name, None)
        if application is None or not application.active:
            return

        application.record_custom_event(event_type, params)

    def record_transaction(self, app_name, data):
        """Processes the raw transaction data, generating and recording
        appropriate metrics against the named application. If there has
        been no prior request to activate the application, the metric is
        discarded.

        """

        application = self._applications.get(app_name, None)
        if application is None or not application.active:
            return

        application.record_transaction(data)

        if self._config.serverless_mode.enabled:
            application.harvest(flexible=True)
            application.harvest(flexible=False)

    def normalize_name(self, app_name, name, rule_type="url"):
        application = self._applications.get(app_name, None)
        if application is None:
            return name, False

        return application.normalize_name(name, rule_type)

    def compute_sampled(self, app_name):
        application = self._applications.get(app_name, None)
        return application.compute_sampled()

    def _harvest_shutdown_is_set(self):
        try:
            return self._harvest_shutdown.is_set()
        except TypeError:
            return self._harvest_shutdown.isSet()

    def _harvest_flexible(self, shutdown=False):
        if not self._harvest_shutdown_is_set():
            event_harvest_config = self.global_settings().event_harvest_config

            self._scheduler.enter(event_harvest_config.report_period_ms / 1000.0, 1, self._harvest_flexible, ())
            _logger.debug("Commencing harvest[flexible] of application data.")
        elif not shutdown:
            return
        else:
            _logger.debug("Commencing final harvest[flexible] of application data.")

        self._flexible_harvest_count += 1
        self._last_flexible_harvest = time.time()

        for application in list(six.itervalues(self._applications)):
            try:
                application.harvest(shutdown=False, flexible=True)
            except Exception:
                _logger.exception("Failed to harvest data for %s." % application.name)

        self._flexible_harvest_duration = time.time() - self._last_flexible_harvest

        _logger.debug(
            "Completed harvest[flexible] of application data in %.2f seconds.", self._flexible_harvest_duration
        )

    def _harvest_default(self, shutdown=False):
        if not self._harvest_shutdown_is_set():
            self._scheduler.enter(60.0, 2, self._harvest_default, ())
            _logger.debug("Commencing harvest[default] of application data.")
        elif not shutdown:
            return
        else:
            _logger.debug("Commencing final harvest[default] of application data.")

        self._default_harvest_count += 1
        self._last_default_harvest = time.time()

        for application in list(six.itervalues(self._applications)):
            try:
                application.harvest(shutdown, flexible=False)
            except Exception:
                _logger.exception("Failed to harvest data for %s." % application.name)

        self._default_harvest_duration = time.time() - self._last_default_harvest

        _logger.debug("Completed harvest[default] of application data in %.2f seconds.", self._default_harvest_duration)

    def _harvest_timer(self):
        if self._harvest_shutdown_is_set():
            return float("inf")
        return time.time()

    def _harvest_loop(self):
        _logger.debug("Entering harvest loop.")

        settings = newrelic.core.config.global_settings()
        event_harvest_config = settings.event_harvest_config

        self._scheduler.enter(event_harvest_config.report_period_ms / 1000.0, 1, self._harvest_flexible, ())
        self._scheduler.enter(60.0, 2, self._harvest_default, ())

        try:
            self._scheduler.run()
        except Exception:
            # An unexpected error, possibly some sort of internal agent
            # implementation issue or more likely due to modules being
            # destroyed from the main thread on process exit when the
            # background harvest thread is still running.

            if self._process_shutdown:
                _logger.exception(
                    "Unexpected exception in main harvest "
                    "loop when process being shutdown. This can occur "
                    "in rare cases due to the main thread cleaning up "
                    "and destroying objects while the background harvest "
                    "thread is still running. If this message occurs "
                    "rarely, it can be ignored. If the message occurs "
                    "on a regular basis, then please report it to New "
                    "Relic support for further investigation."
                )

            else:
                _logger.exception(
                    "Unexpected exception in main harvest "
                    "loop. Please report this problem to New Relic "
                    "support for further investigation."
                )

    def activate_agent(self):
        """Starts the main background for the agent."""
        with Agent._instance_lock:
            # Skip this if agent is not actually enabled.
            if not self._config.enabled:
                _logger.warning("The Python Agent is not enabled.")
                return
            elif self._config.serverless_mode.enabled:
                _logger.debug("Harvest thread is disabled due to serverless mode.")
                return
            elif self._config.debug.disable_harvest_until_shutdown:
                _logger.debug("Harvest thread is disabled.")
                return

            # Skip this if background thread already running.

            if self._harvest_thread.is_alive():
                return

            _logger.debug("Activating agent instance.")

            for callable in self._startup_callables:
                callable()

            _logger.debug("Start Python Agent main thread.")

            self._harvest_thread.start()

            self._process_id = os.getpid()

    def _atexit_shutdown(self):
        """Triggers agent shutdown but flags first that this is being
        done because process is being shutdown.

        """

        self._process_shutdown = True
        self.shutdown_agent()

    def shutdown_agent(self, timeout=None):
        if self._harvest_shutdown_is_set():
            return

        if timeout is None:
            timeout = self._config.shutdown_timeout

        _logger.info("New Relic Python Agent Shutdown")

        # Schedule final harvests. This is OK to schedule across threads since
        # the entries will only be added to the end of the list and won't be
        # popped until harvest_shutdown is set.
        self._scheduler.enter(float("inf"), 3, self._harvest_flexible, (True,))
        self._scheduler.enter(float("inf"), 4, self._harvest_default, (True,))

        self._harvest_shutdown.set()

        if self._config.debug.disable_harvest_until_shutdown:
            _logger.debug("Start Python Agent main thread on shutdown.")
            self._harvest_thread.start()

        if self._harvest_thread.is_alive():
            self._harvest_thread.join(timeout)


def agent_instance():
    """Returns the agent object. This function should always be used and
    instances of the agent object should never be created directly to
    ensure there is only ever one instance.

    Network connection details and the licence key needed to initialise the
    agent must have been set in the global default configuration settings
    prior to the first call of this function.

    """

    return Agent.agent_singleton()


def shutdown_agent(timeout=None):
    agent = agent_instance()
    agent.shutdown_agent(timeout)


def register_data_source(source, application=None, name=None, settings=None, **properties):
    agent = agent_instance()
    agent.register_data_source(source, application and application.name or None, name, settings, **properties)


def _remove_thread_utilization():
    agent = agent_instance()
    agent.remove_thread_utilization()


def remove_thread_utilization():
    with Agent._instance_lock:
        if Agent._instance:
            _remove_thread_utilization()
        else:
            Agent.run_on_startup(_remove_thread_utilization)

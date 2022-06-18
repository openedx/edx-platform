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

from newrelic.api.application import application_instance as default_application
from newrelic.common.object_wrapper import (wrap_function_wrapper,
        FunctionWrapper)
from newrelic.api.background_task import BackgroundTask
from newrelic.api.function_trace import FunctionTrace, wrap_function_trace
from newrelic.api.transaction import current_transaction
from newrelic.api.time_trace import current_trace
from newrelic.common.object_names import callable_name
from newrelic.api.external_trace import ExternalTrace

# Following wrappers are specifically for a gearman client.

def instrument_gearman_client(module):
    wrap_function_trace(module, 'GearmanClient.submit_job')
    wrap_function_trace(module, 'GearmanClient.submit_multiple_jobs')
    wrap_function_trace(module, 'GearmanClient.submit_multiple_requests')
    wrap_function_trace(module, 'GearmanClient.wait_until_jobs_accepted')
    wrap_function_trace(module, 'GearmanClient.wait_until_jobs_completed')
    wrap_function_trace(module, 'GearmanClient.get_job_status')
    wrap_function_trace(module, 'GearmanClient.get_job_statuses')
    wrap_function_trace(module, 'GearmanClient.wait_until_job_statuses_received')

def wrapper_GearmanConnectionManager_poll_connections_until_stopped(
        wrapped, instance, args, kwargs):

    def _bind_params(submitted_connections, *args, **kwargs):
        return submitted_connections

    # Because gearman uses a custom message based protocol over a raw
    # socket, we can't readily wrap a single function which is
    # performing a request and then returning a response. The best we
    # can do is wrap as an external the poll_connections_until_stopped()
    # function. This is what manages looking for whether data is
    # available from the server, or whether data can be written, and
    # then handles those events.
    #
    # This is complicated somewhat though due to a gearman client being
    # able to be supplied multiple servers to communicate with. We can
    # not actually determine which server communication will occur with
    # until the specific handle function for read, write or error is
    # called but that is too late in cases where a failure of some sort
    # occurs such as a timeout. What we therefore do is presume
    # initially that the server will be whatever is the first in the
    # list of server connections and we will override this latter based
    # on which server we ended up communicating with. It is possible this
    # still will not always be correct if data is handled for multiple
    # servers in the one call, but it is likely as close as we can get.
    # As likely that most clients will only be talking to a single
    # server, it likely will not matter too much.

    submitted_connections = _bind_params(*args, **kwargs)

    if not submitted_connections:
        return wrapped(*args, **kwargs)

    first_connection = list(submitted_connections)[0]

    url = 'gearman://%s:%s' % (first_connection.gearman_host,
            first_connection.gearman_port)

    with ExternalTrace('gearman', url):
        return wrapped(*args, **kwargs)

def wrapper_GearmanConnectionManager_handle_function(wrapped, instance,
        args, kwargs):

    def _bind_params(current_connection, *args, **kwargs):
        return current_connection

    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    tracer = current_trace()

    if not isinstance(tracer, ExternalTrace):
        return wrapped(*args, **kwargs)

    # Now override the URL for the external to be the specific server we
    # ended up communicating with. This could get overridden multiple
    # times in the context of a single poll_connections_until_stopped()
    # call and so will be set to the last server data was processed for.
    # This thus may not necessarily be correct if communicating with
    # multiple servers and data from more than one was being handled for
    # some reason. Can't really do much better than this though but will
    # be fine for the expected typical use case of a single server.

    if not tracer.url.startswith('gearman:'):
        return wrapped(*args, **kwargs)

    current_connection = _bind_params(*args, **kwargs)

    tracer.url = 'gearman://%s:%s' % (current_connection.gearman_host,
            current_connection.gearman_port)

    return wrapped(*args, **kwargs)

def instrument_gearman_connection_manager(module):
    wrap_function_wrapper(module, 'GearmanConnectionManager.handle_read',
            wrapper_GearmanConnectionManager_handle_function)
    wrap_function_wrapper(module, 'GearmanConnectionManager.handle_write',
            wrapper_GearmanConnectionManager_handle_function)
    wrap_function_wrapper(module, 'GearmanConnectionManager.handle_error',
            wrapper_GearmanConnectionManager_handle_function)

    wrap_function_wrapper(module,
            'GearmanConnectionManager.poll_connections_until_stopped',
            wrapper_GearmanConnectionManager_poll_connections_until_stopped)

# Following wrappers are specifically for a gearman worker.

def wrapper_GearmanWorker_on_job_execute(wrapped, instance, args, kwargs):
    def _bind_params(current_job, *args, **kwargs):
        return current_job

    # The background task is always created against the default
    # application specified by the agent configuration. The background
    # task is named after the name the task function was registered as,
    # and prefixed by the special 'Gearman' group.

    application = default_application()
    current_job = _bind_params(*args, **kwargs)

    with BackgroundTask(application, current_job.task, 'Gearman'):
        return wrapped(*args, **kwargs)

def wrapper_callback_function(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    # This tracks as a separate function trace the call of the actual
    # task function so that the original function name also appears in
    # the performance breakdown. We catch exceptions and record them at
    # this point as otherwise they are caught by the gearman worker
    # dispatch code and do not actually propagate up to the level of the
    # background task wrapper.

    with FunctionTrace(callable_name(wrapped)) as trace:
        try:
            return wrapped(*args, **kwargs)
        except:  # Catch all
            trace.notice_error()
            raise

def wrapper_GearmanWorker_register_task(wrapped, instance, args, kwargs):
    def _bind_params(task, callback_function, *args, **kwargs):
        return task, callback_function, args, kwargs

    # This applies a wrapper around the task function at the point that
    # it is registered. This is so we can later wrap execution with a
    # function trace and catch and record any exceptions in the task
    # function.

    task, callback_function, _args, _kwargs = _bind_params(*args, **kwargs)
    callback_function = FunctionWrapper(callback_function,
            wrapper_callback_function)

    return wrapped(task, callback_function, *_args, **_kwargs)

def instrument_gearman_worker(module):
    wrap_function_wrapper(module, 'GearmanWorker.on_job_execute',
            wrapper_GearmanWorker_on_job_execute)
    wrap_function_wrapper(module, 'GearmanWorker.register_task',
            wrapper_GearmanWorker_register_task)

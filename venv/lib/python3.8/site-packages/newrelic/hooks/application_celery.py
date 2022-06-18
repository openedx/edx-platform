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

"""This module provides instrumentation for Celery.

Note that Celery has a habit of moving things around in code base or of
completely rewriting stuff across minor versions. See additional notes
about this below.

"""

import functools

from newrelic.api.application import application_instance
from newrelic.api.background_task import BackgroundTask
from newrelic.api.function_trace import FunctionTrace
from newrelic.api.pre_function import wrap_pre_function
from newrelic.api.object_wrapper import callable_name, ObjectWrapper
from newrelic.api.transaction import current_transaction
from newrelic.core.agent import shutdown_agent


def CeleryTaskWrapper(wrapped, application=None, name=None):

    def wrapper(wrapped, instance, args, kwargs):
        transaction = current_transaction(active_only=False)

        if callable(name):
            # Start Hotfix v2.2.1.
            # if instance and inspect.ismethod(wrapped):
            #     _name = name(instance, *args, **kwargs)
            # else:
            #     _name = name(*args, **kwargs)

            if instance is not None:
                _name = name(instance, *args, **kwargs)
            else:
                _name = name(*args, **kwargs)
            # End Hotfix v2.2.1.

        elif name is None:
            _name = callable_name(wrapped)

        else:
            _name = name

        # Helper for obtaining the appropriate application object. If
        # has an activate() method assume it is a valid application
        # object. Don't check by type so se can easily mock it for
        # testing if need be.

        def _application():
            if hasattr(application, 'activate'):
                return application
            return application_instance(application)

        # A Celery Task can be called either outside of a transaction, or
        # within the context of an existing transaction. There are 3
        # possibilities we need to handle:
        #
        #   1. In an inactive transaction
        #
        #      If the end_of_transaction() or ignore_transaction() API calls
        #      have been invoked, this task may be called in the context
        #      of an inactive transaction. In this case, don't wrap the task
        #      in any way. Just run the original function.
        #
        #   2. In an active transaction
        #
        #      Run the original function inside a FunctionTrace.
        #
        #   3. Outside of a transaction
        #
        #      This is the typical case for a celery Task. Since it's not
        #      running inside of an existing transaction, we want to create
        #      a new background transaction for it.

        if transaction and (transaction.ignore_transaction or
                transaction.stopped):
            return wrapped(*args, **kwargs)

        elif transaction:
            with FunctionTrace(callable_name(wrapped)):
                return wrapped(*args, **kwargs)

        else:
            with BackgroundTask(_application(), _name, 'Celery'):
                return wrapped(*args, **kwargs)

    # Start Hotfix v2.2.1.
    # obj = ObjectWrapper(wrapped, None, wrapper)
    # End Hotfix v2.2.1.

    # Celery tasks that inherit from celery.app.task must implement a run()
    # method.
    # ref: (http://docs.celeryproject.org/en/2.5/reference/
    #                            celery.app.task.html#celery.app.task.BaseTask)
    # Celery task's __call__ method then calls the run() method to execute the
    # task. But celery does a micro-optimization where if the __call__ method
    # was not overridden by an inherited task, then it will directly execute
    # the run() method without going through the __call__ method. Our
    # instrumentation via ObjectWrapper() relies on __call__ being called which
    # in turn executes the wrapper() function defined above. Since the micro
    # optimization bypasses __call__ method it breaks our instrumentation of
    # celery. To circumvent this problem, we added a run() attribute to our
    # ObjectWrapper which points to our __call__ method. This causes Celery
    # to execute our __call__ method which in turn applies the wrapper
    # correctly before executing the task.
    #
    # This is only a problem in Celery versions 2.5.3 to 2.5.5. The later
    # versions included a monkey-patching provision which did not perform this
    # optimization on functions that were monkey-patched.

    # Start Hotfix v2.2.1.
    # obj.__dict__['run'] = obj.__call__

    class _ObjectWrapper(ObjectWrapper):
        def run(self, *args, **kwargs):
            return self.__call__(*args, **kwargs)

    obj = _ObjectWrapper(wrapped, None, wrapper)
    # End Hotfix v2.2.1.

    return obj


def instrument_celery_app_task(module):

    # Triggered for both 'celery.app.task' and 'celery.task.base'.

    if hasattr(module, 'BaseTask'):

        # Need to add a wrapper for background task entry point.

        # In Celery 2.2 the 'BaseTask' class actually resided in the
        # module 'celery.task.base'. In Celery 2.3 the 'BaseTask' class
        # moved to 'celery.app.task' but an alias to it was retained in
        # the module 'celery.task.base'. We need to detect both module
        # imports, but we check the module name associated with
        # 'BaseTask' to ensure that we do not instrument the class via
        # the alias in Celery 2.3 and later.

        # In Celery 2.5+, although 'BaseTask' still exists execution of
        # the task doesn't pass through it. For Celery 2.5+ need to wrap
        # the tracer instead.

        def task_name(task, *args, **kwargs):
            return task.name

        if module.BaseTask.__module__ == module.__name__:
            module.BaseTask.__call__ = CeleryTaskWrapper(
                    module.BaseTask.__call__, name=task_name)


def instrument_celery_execute_trace(module):

    # Triggered for 'celery.execute_trace'.

    if hasattr(module, 'build_tracer'):

        # Need to add a wrapper for background task entry point.

        # In Celery 2.5+ we need to wrap the task when tracer is being
        # created. Note that in Celery 2.5 the 'build_tracer' function
        # actually resided in the module 'celery.execute.task'. In
        # Celery 3.0 the 'build_tracer' function moved to
        # 'celery.task.trace'.

        _build_tracer = module.build_tracer

        def build_tracer(name, task, *args, **kwargs):
            task = task or module.tasks[name]
            task = CeleryTaskWrapper(task, name=name)
            return _build_tracer(name, task, *args, **kwargs)

        module.build_tracer = build_tracer


def instrument_celery_worker(module):

    # Triggered for 'celery.worker' and 'celery.concurrency.processes'.

    if hasattr(module, 'process_initializer'):

        # We try and force registration of default application after
        # fork of worker process rather than lazily on first request.

        # Originally the 'process_initializer' function was located in
        # 'celery.worker'. In Celery 2.5 the function 'process_initializer'
        # was moved to the module 'celery.concurrency.processes'.

        _process_initializer = module.process_initializer

        @functools.wraps(module.process_initializer)
        def process_initializer(*args, **kwargs):
            application_instance().activate()
            return _process_initializer(*args, **kwargs)

        module.process_initializer = process_initializer


def instrument_celery_loaders_base(module):

    def force_application_activation(*args, **kwargs):
        application_instance().activate()

    wrap_pre_function(module, 'BaseLoader.init_worker',
            force_application_activation)


def instrument_billiard_pool(module):

    def force_agent_shutdown(*args, **kwargs):
        shutdown_agent()

    if hasattr(module, 'Worker'):
        wrap_pre_function(module, 'Worker._do_exit', force_agent_shutdown)

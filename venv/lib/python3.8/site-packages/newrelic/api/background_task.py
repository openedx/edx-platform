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

import functools
import sys

from newrelic.api.application import Application, application_instance
from newrelic.api.transaction import Transaction, current_transaction
from newrelic.common.async_proxy import async_proxy, TransactionContext
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import FunctionWrapper, wrap_object


class BackgroundTask(Transaction):

    def __init__(self, application, name, group=None):

        # Initialise the common transaction base class.

        super(BackgroundTask, self).__init__(application)

        # Mark this as a background task even if disabled.

        self.background_task = True

        # Set async related attributes

        self._ref_count = 0
        self._is_finalized = False
        self._request_handler_finalize = False
        self._server_adapter_finalize = False

        # Bail out if the transaction is running in a
        # disabled state.

        if not self.enabled:
            return

        # Name the web transaction from supplied values.

        self.set_transaction_name(name, group, priority=1)


def BackgroundTaskWrapper(wrapped, application=None, name=None, group=None):

    def wrapper(wrapped, instance, args, kwargs):
        if callable(name):
            if instance is not None:
                _name = name(instance, *args, **kwargs)
            else:
                _name = name(*args, **kwargs)

        elif name is None:
            _name = callable_name(wrapped)

        else:
            _name = name

        if callable(group):
            if instance is not None:
                _group = group(instance, *args, **kwargs)
            else:
                _group = group(*args, **kwargs)

        else:
            _group = group

        if type(application) != Application:
            _application = application_instance(application)
        else:
            _application = application

        def create_transaction(transaction):
            if transaction:
                # If there is any active transaction we will return without
                # applying a new WSGI application wrapper context. In the
                # case of a transaction which is being ignored or which has
                # been stopped, we do that without doing anything further.

                if transaction.ignore_transaction or transaction.stopped:
                    return None

                if not transaction.background_task:
                    transaction.background_task = True
                    transaction.set_transaction_name(_name, _group)

                return None

            return BackgroundTask(_application, _name, _group)

        proxy = async_proxy(wrapped)

        if proxy:
            context_manager = TransactionContext(create_transaction)
            return proxy(wrapped(*args, **kwargs), context_manager)

        manager = create_transaction(current_transaction(active_only=False))

        if not manager:
            return wrapped(*args, **kwargs)
        success = True

        try:
            manager.__enter__()
            try:
                return wrapped(*args, **kwargs)
            except:
                success = False
                if not manager.__exit__(*sys.exc_info()):
                    raise
        finally:
            if success and manager._ref_count == 0:
                manager._is_finalized = True
                manager.__exit__(None, None, None)
            else:
                manager._request_handler_finalize = True
                manager._server_adapter_finalize = True

                old_transaction = current_transaction()
                if old_transaction is not None:
                    old_transaction.drop_transaction()

    return FunctionWrapper(wrapped, wrapper)


def background_task(application=None, name=None, group=None):
    return functools.partial(BackgroundTaskWrapper,
            application=application, name=name, group=group)


def wrap_background_task(module, object_path, application=None,
        name=None, group=None):
    wrap_object(module, object_path, BackgroundTaskWrapper,
            (application, name, group))

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
import sys
import weakref
import UserList

import newrelic.api.application
import newrelic.api.object_wrapper
import newrelic.api.transaction
import newrelic.api.web_transaction
import newrelic.api.function_trace
import newrelic.api.error_trace

from newrelic.api.time_trace import notice_error

_logger = logging.getLogger(__name__)

class RequestProcessWrapper(object):

    def __init__(self, wrapped):
        if isinstance(wrapped, tuple):
            (instance, wrapped) = wrapped
        else:
            instance = None

        newrelic.api.object_wrapper.update_wrapper(self, wrapped)

        self._nr_instance = instance
        self._nr_next_object = wrapped

        if not hasattr(self, '_nr_last_object'):
            self._nr_last_object = wrapped

    def __get__(self, instance, klass):
        if instance is None:
            return self
        descriptor = self._nr_next_object.__get__(instance, klass)
        return self.__class__((instance, descriptor))

    def __call__(self):
        assert self._nr_instance != None

        transaction = newrelic.api.transaction.current_transaction()

        # Check to see if we are being called within the context of any
        # sort of transaction. If we are, then we don't bother doing
        # anything and just call the wrapped function. This should not
        # really ever occur with Twisted.Web wrapper but check anyway.

        if transaction:
            return self._nr_next_object()

        # Always use the default application specified in the agent
        # configuration.

        application = newrelic.api.application.application_instance()

        # We need to fake up a WSGI like environ dictionary with the key
        # bits of information we need.

        environ = {}

        environ['REQUEST_URI'] = self._nr_instance.path

        # Now start recording the actual web transaction.

        transaction = newrelic.api.web_transaction.WSGIWebTransaction(
                application, environ)

        if not transaction.enabled:
            return self._nr_next_object()

        transaction.__enter__()

        self._nr_instance._nr_transaction = transaction

        self._nr_instance._nr_is_deferred_callback = False
        self._nr_instance._nr_is_request_finished = False
        self._nr_instance._nr_wait_function_trace = None

        # We need to add a reference to the Twisted.Web request object
        # in the transaction as only able to stash the transaction in a
        # deferred. Need to use a weakref to avoid an object cycle which
        # may prevent cleanup of transaction.

        transaction._nr_current_request = weakref.ref(self._nr_instance)

        try:
            # Call the original method in a trace object to give better
            # context in transaction traces. Three things can happen
            # within this call. The render() function which is in turn
            # called can return a result immediately which means user
            # code should have called finish() on the request, it can
            # raise an exception which is caught in process() function
            # where error handling calls finish(), or it can return that
            # it is not done yet and register deferred callbacks to
            # complete the request.

            with newrelic.api.function_trace.FunctionTrace(
                    name='Request/Process', group='Python/Twisted'):
                result = self._nr_next_object()

            # In the case of a result having being returned or an
            # exception occuring, then finish() will have been called.
            # We can't just exit the transaction in the finish call
            # however as need to still pop back up through the above
            # function trace. So if flagged that have finished, then we
            # exit the transaction here. Otherwise we setup a function
            # trace to track wait time for deferred and manually pop the
            # transaction as being the current one for this thread.

            if self._nr_instance._nr_is_request_finished:
                transaction.__exit__(None, None, None)
                self._nr_instance._nr_transaction = None
                self._nr_instance = None

            else:
                self._nr_instance._nr_wait_function_trace = \
                        newrelic.api.function_trace.FunctionTrace(
                        name='Deferred/Wait',
                        group='Python/Twisted')

                self._nr_instance._nr_wait_function_trace.__enter__()
                transaction.drop_transaction()

        except:  # Catch all
            # If an error occurs assume that transaction should be
            # exited. Technically don't believe this should ever occur
            # unless our code here has an error or Twisted.Web is
            # broken.

            _logger.exception('Unexpected exception raised by Twisted.Web '
                    'Request.process() exception.')

            transaction.__exit__(*sys.exc_info())
            self._nr_instance._nr_transaction = None
            self._nr_instance = None

            raise

        return result

class RequestFinishWrapper(object):

    def __init__(self, wrapped):
        if isinstance(wrapped, tuple):
            (instance, wrapped) = wrapped
        else:
            instance = None

        newrelic.api.object_wrapper.update_wrapper(self, wrapped)

        self._nr_instance = instance
        self._nr_next_object = wrapped

        if not hasattr(self, '_nr_last_object'):
            self._nr_last_object = wrapped

    def __get__(self, instance, klass):
        if instance is None:
            return self
        descriptor = self._nr_next_object.__get__(instance, klass)
        return self.__class__((instance, descriptor))

    def __call__(self):
        assert self._nr_instance != None

        # Call finish() method straight away if request is not even
        # associated with a transaction.

        if not hasattr(self._nr_instance, '_nr_transaction'):
            return self._nr_next_object()

        # Technically we should only be able to be called here without
        # an active transaction if we are in the wait state. If we
        # are called in context of original request process() function
        # or a deferred the transaction should already be registered.

        transaction = self._nr_instance._nr_transaction

        if self._nr_instance._nr_wait_function_trace:
            if newrelic.api.transaction.current_transaction():
                _logger.debug('The Twisted.Web request finish() method is '
                        'being called while in wait state but there is '
                        'already a current transaction.')
            else:
                transaction.save_transaction()

        elif not newrelic.api.transaction.current_transaction():
            _logger.debug('The Twisted.Web request finish() method is '
                    'being called from request process() method or a '
                    'deferred but there is not a current transaction.')

        # Except for case of being called when in wait state, we can't
        # actually exit the transaction at this point as may be called
        # in context of an outer function trace node. We thus flag that
        # are finished and pop back out allowing outer scope to actually
        # exit the transaction.

        self._nr_instance._nr_is_request_finished = True

        # Now call the original finish() function.

        if self._nr_instance._nr_is_deferred_callback:

            # If we are in a deferred callback log any error against the
            # transaction here so we know we will capture it. We
            # possibly don't need to do it here as outer scope may catch
            # it anyway. Duplicate will be ignored so not too important.
            # Most likely the finish() call would never fail anyway.

            try:
                with newrelic.api.function_trace.FunctionTrace(
                        name='Request/Finish', group='Python/Twisted'):
                    result = self._nr_next_object()

            except:  # Catch all
                notice_error(sys.exc_info())
                raise

        elif self._nr_instance._nr_wait_function_trace:

            # Now handle the special case where finish() was called
            # while in the wait state. We might get here through
            # Twisted.Web itself somehow calling finish() when still
            # waiting for a deferred. If this were to occur though then
            # the transaction will not be popped if we simply marked
            # request as finished as no outer scope to see that and
            # clean up. We will thus need to end the function trace and
            # exit the transaction. We end function trace here and then
            # the transaction down below.

            try:
                self._nr_instance._nr_wait_function_trace.__exit__(
                        None, None, None)

                with newrelic.api.function_trace.FunctionTrace(
                        name='Request/Finish', group='Python/Twisted'):
                    result = self._nr_next_object()

                transaction.__exit__(None, None, None)

            except:  # Catch all
                transaction.__exit__(*sys.exc_info())
                raise

            finally:
                self._nr_instance._nr_wait_function_trace = None
                self._nr_instance._nr_transaction = None
                self._nr_instance = None

        else:
            # This should be the case where finish() is being called in
            # the original render() function.

            with newrelic.api.function_trace.FunctionTrace(
                    name='Request/Finish', group='Python/Twisted'):
                result = self._nr_next_object()

        return result

class ResourceRenderWrapper(object):

    def __init__(self, wrapped):
        if isinstance(wrapped, tuple):
            (instance, wrapped) = wrapped
        else:
            instance = None

        newrelic.api.object_wrapper.update_wrapper(self, wrapped)

        self._nr_instance = instance
        self._nr_next_object = wrapped

        if not hasattr(self, '_nr_last_object'):
            self._nr_last_object = wrapped

    def __get__(self, instance, klass):
        if instance is None:
            return self
        descriptor = self._nr_next_object.__get__(instance, klass)
        return self.__class__((instance, descriptor))

    def __call__(self, *args):

        # Temporary work around due to customer calling class method
        # directly with 'self' as first argument. Need to work out best
        # practice for dealing with this.

        if len(args) == 2:
            # Assume called as unbound method with (self, request).
            instance, request = args
        else:
            # Assume called as bound method with (request).
            instance = self._nr_instance
            request = args[-1]

        assert instance != None

        transaction = newrelic.api.transaction.current_transaction()

        if transaction is None:
            return self._nr_next_object(*args)

        # This is wrapping the render() function of the resource. We
        # name the function node and the web transaction after the name
        # of the handler function augmented with the method type for the
        # request.

        name = "%s.render_%s" % (
                newrelic.api.object_wrapper.callable_name(
                instance), request.method)
        transaction.set_transaction_name(name, priority=1)

        with newrelic.api.function_trace.FunctionTrace(name):
            return self._nr_next_object(*args)

class DeferredUserList(UserList.UserList):

    def pop(self, i=-1):
        import twisted.internet.defer
        item = super(DeferredUserList, self).pop(i)

        item0 = item[0]
        item1 = item[1]

        if item0[0] != twisted.internet.defer._CONTINUE:
            item0 = (newrelic.api.function_trace.FunctionTraceWrapper(
                     item0[0], group='Python/Twisted/Callback'),
                     item0[1], item0[2])

        if item1[0] != twisted.internet.defer._CONTINUE:
            item1 = (newrelic.api.function_trace.FunctionTraceWrapper(
                     item1[0], group='Python/Twisted/Errback'),
                     item1[1], item1[2])

        return (item0, item1)

class DeferredWrapper(object):

    def __init__(self, wrapped):
        if isinstance(wrapped, tuple):
            (instance, wrapped) = wrapped
        else:
            instance = None

        newrelic.api.object_wrapper.update_wrapper(self, wrapped)

        self._nr_instance = instance
        self._nr_next_object = wrapped

        if not hasattr(self, '_nr_last_object'):
            self._nr_last_object = wrapped

    def __get__(self, instance, klass):
        if instance is None:
            return self
        descriptor = self._nr_next_object.__get__(instance, klass)
        return self.__class__((instance, descriptor))

    def __call__(self, *args, **kwargs):

        # This is wrapping the __init__() function so call that first.

        self._nr_next_object(*args, **kwargs)

        # We now wrap the list of deferred callbacks so can track when
        # each callback is actually called.

        if self._nr_instance:
            transaction = newrelic.api.transaction.current_transaction()
            if transaction:
                self._nr_instance._nr_transaction = transaction
                self._nr_instance.callbacks = DeferredUserList(
                        self._nr_instance.callbacks)

class DeferredCallbacksWrapper(object):

    def __init__(self, wrapped):
        if isinstance(wrapped, tuple):
            (instance, wrapped) = wrapped
        else:
            instance = None

        newrelic.api.object_wrapper.update_wrapper(self, wrapped)

        self._nr_instance = instance
        self._nr_next_object = wrapped

        if not hasattr(self, '_nr_last_object'):
            self._nr_last_object = wrapped

    def __get__(self, instance, klass):
        if instance is None:
            return self
        descriptor = self._nr_next_object.__get__(instance, klass)
        return self.__class__((instance, descriptor))

    def __call__(self):
        assert self._nr_instance != None

        transaction = newrelic.api.transaction.current_transaction()

        # If there is an active transaction then deferred is being
        # called within a context of another deferred so simply call the
        # callback and return.

        if transaction:
            return self._nr_next_object()

        # If there is no transaction recorded against the deferred then
        # don't need to do anything and can simply call the callback and
        # return.

        if not hasattr(self._nr_instance, '_nr_transaction'):
            return self._nr_next_object()

        transaction = self._nr_instance._nr_transaction

        # If we can't find a Twisted.Web request object associated with
        # the transaction or it is no longer valid then simply call the
        # callback and return.

        if not hasattr(transaction, '_nr_current_request'):
            return self._nr_next_object()

        request = transaction._nr_current_request()

        if not request:
            return self._nr_next_object()

        try:
            # Save the transaction recorded against the deferred as the
            # active transaction.

            transaction.save_transaction()

            # Record that are calling a deferred. This changes what we
            # do if the request finish() method is being called.

            request._nr_is_deferred_callback = True

            # We should always be calling into a deferred when we are
            # in the wait state for the request. We need to exit that
            # wait state.

            if request._nr_wait_function_trace:
                request._nr_wait_function_trace.__exit__(None, None, None)
                request._nr_wait_function_trace = None

            else:
                _logger.debug('Called a Twisted.Web deferred when we were '
                        'not in a wait state.')

            # Call the deferred and capture any errors that may come
            # back from it.

            with newrelic.api.error_trace.ErrorTrace():
                with newrelic.api.function_trace.FunctionTrace(
                        name='Deferred/Call',
                        group='Python/Twisted'):
                    return self._nr_next_object()

        finally:
            # If the request finish() method was called from the
            # deferred then we need to exit the transaction. Other wise
            # we need to create a new function trace node for a new wait
            # state and pop the transaction.

            if request._nr_is_request_finished:
                transaction.__exit__(None, None, None)
                self._nr_instance._nr_transaction = None

            else:
                # XXX Should we be removing the transaction from the
                # deferred object as well. Can the same deferred be
                # called multiple times for same request. It probably
                # can be reregistered.

                request._nr_wait_function_trace = \
                        newrelic.api.function_trace.FunctionTrace(
                        name='Deferred/Wait',
                        group='Python/Twisted')

                request._nr_wait_function_trace.__enter__()
                transaction.drop_transaction()

            request._nr_is_deferred_callback = False

class InlineGeneratorWrapper(object):

    def __init__(self, wrapped, generator):
        self._nr_wrapped = wrapped
        self._nr_generator = generator

    def __iter__(self):
        name = newrelic.api.object_wrapper.callable_name(self._nr_wrapped)
        iterable = iter(self._nr_generator)
        while 1:
            with newrelic.api.function_trace.FunctionTrace(
                  name, group='Python/Twisted/Generator'):
                yield next(iterable)

class InlineCallbacksWrapper(object):

    def __init__(self, wrapped):
        if isinstance(wrapped, tuple):
            (instance, wrapped) = wrapped
        else:
            instance = None

        newrelic.api.object_wrapper.update_wrapper(self, wrapped)

        self._nr_instance = instance
        self._nr_next_object = wrapped

        if not hasattr(self, '_nr_last_object'):
            self._nr_last_object = wrapped

    def __get__(self, instance, klass):
        if instance is None:
            return self
        descriptor = self._nr_next_object.__get__(instance, klass)
        return self.__class__((instance, descriptor))

    def __call__(self, *args, **kwargs):
        transaction = newrelic.api.transaction.current_transaction()

        if not transaction:
            return self._nr_next_object(*args, **kwargs)

        result = self._nr_next_object(*args, **kwargs)

        if not result:
            return result

        return iter(InlineGeneratorWrapper(self._nr_next_object, result))

def instrument_twisted_web_server(module):
    module.Request.process = RequestProcessWrapper(module.Request.process)

def instrument_twisted_web_http(module):
    module.Request.finish = RequestFinishWrapper(module.Request.finish)

def instrument_twisted_web_resource(module):
    module.Resource.render = ResourceRenderWrapper(module.Resource.render)

def instrument_twisted_internet_defer(module):
    module.Deferred.__init__ = DeferredWrapper(module.Deferred.__init__)
    module.Deferred._runCallbacks = DeferredCallbacksWrapper(
            module.Deferred._runCallbacks)

    #_inlineCallbacks = module.inlineCallbacks
    #def inlineCallbacks(f):
    #    return _inlineCallbacks(InlineCallbacksWrapper(f))
    #module.inlineCallbacks = inlineCallbacks

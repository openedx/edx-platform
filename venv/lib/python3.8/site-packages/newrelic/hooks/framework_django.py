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

import sys
import threading
import logging
import functools

from newrelic.packages import six

from newrelic.api.application import register_application
from newrelic.api.background_task import BackgroundTask
from newrelic.api.error_trace import wrap_error_trace
from newrelic.api.function_trace import (FunctionTrace, wrap_function_trace,
        FunctionTraceWrapper)
from newrelic.api.html_insertion import insert_html_snippet
from newrelic.api.transaction import current_transaction
from newrelic.api.time_trace import notice_error
from newrelic.api.transaction_name import wrap_transaction_name
from newrelic.api.wsgi_application import WSGIApplicationWrapper

from newrelic.common.object_wrapper import (FunctionWrapper, wrap_in_function,
        wrap_post_function, wrap_function_wrapper, function_wrapper)
from newrelic.common.object_names import callable_name
from newrelic.config import extra_settings
from newrelic.core.config import global_settings
from newrelic.common.coroutine import is_coroutine_function, is_asyncio_coroutine

if six.PY3:
    from newrelic.hooks.framework_django_py3 import (
        _nr_wrapper_BaseHandler_get_response_async_,
        _nr_wrap_converted_middleware_async_,
    )

_logger = logging.getLogger(__name__)

_boolean_states = {
       '1': True, 'yes': True, 'true': True, 'on': True,
       '0': False, 'no': False, 'false': False, 'off': False
}


def _setting_boolean(value):
    if value.lower() not in _boolean_states:
        raise ValueError('Not a boolean: %s' % value)
    return _boolean_states[value.lower()]


def _setting_set(value):
    return set(value.split())


_settings_types = {
    'browser_monitoring.auto_instrument': _setting_boolean,
    'instrumentation.templates.inclusion_tag': _setting_set,
    'instrumentation.background_task.startup_timeout': float,
    'instrumentation.scripts.django_admin': _setting_set,
}

_settings_defaults = {
    'browser_monitoring.auto_instrument': True,
    'instrumentation.templates.inclusion_tag': set(),
    'instrumentation.background_task.startup_timeout': 10.0,
    'instrumentation.scripts.django_admin': set(),
}

django_settings = extra_settings('import-hook:django',
        types=_settings_types, defaults=_settings_defaults)


def should_add_browser_timing(response, transaction):

    # Don't do anything if receive a streaming response which
    # was introduced in Django 1.5. Need to avoid this as there
    # will be no 'content' attribute. Alternatively there may be
    # a 'content' attribute which flattens the stream, which if
    # we access, will break the streaming and/or buffer what is
    # potentially a very large response in memory contrary to
    # what user wanted by explicitly using a streaming response
    # object in the first place. To preserve streaming but still
    # do RUM insertion, need to move to a WSGI middleware and
    # deal with how to update the content length.

    if hasattr(response, 'streaming_content'):
        return False

    # Need to be running within a valid web transaction.

    if not transaction or not transaction.enabled:
        return False

    # Only insert RUM JavaScript headers and footers if enabled
    # in configuration and not already likely inserted.

    if not transaction.settings.browser_monitoring.enabled:
        return False

    if transaction.autorum_disabled:
        return False

    if not django_settings.browser_monitoring.auto_instrument:
        return False

    if transaction.rum_header_generated:
        return False

    # Only possible if the content type is one of the allowed
    # values. Normally this is just text/html, but optionally
    # could be defined to be list of further types. For example
    # a user may want to also perform insertion for
    # 'application/xhtml+xml'.

    ctype = response.get('Content-Type', '').lower().split(';')[0]

    if ctype not in transaction.settings.browser_monitoring.content_type:
        return False

    # Don't risk it if content encoding already set.

    if response.has_header('Content-Encoding'):
        return False

    # Don't risk it if content is actually within an attachment.

    cdisposition = response.get('Content-Disposition', '').lower()

    if cdisposition.split(';')[0].strip().lower() == 'attachment':
        return False

    return True


# Response middleware for automatically inserting RUM header and
# footer into HTML response returned by application

def browser_timing_insertion(response, transaction):

    # No point continuing if header is empty. This can occur if
    # RUM is not enabled within the UI. It is assumed at this
    # point that if header is not empty, then footer will not be
    # empty. We don't want to generate the footer just yet as
    # want to do that as late as possible so that application
    # server time in footer is as accurate as possible. In
    # particular, if the response content is generated on demand
    # then the flattening of the response could take some time
    # and we want to track that. We thus generate footer below
    # at point of insertion.

    header = transaction.browser_timing_header()

    if not header:
        return response

    def html_to_be_inserted():
        return six.b(header) + six.b(transaction.browser_timing_footer())

    # Make sure we flatten any content first as it could be
    # stored as a list of strings in the response object. We
    # assign it back to the response object to avoid having
    # multiple copies of the string in memory at the same time
    # as we progress through steps below.

    result = insert_html_snippet(response.content, html_to_be_inserted)

    if result is not None:
        if transaction.settings.debug.log_autorum_middleware:
            _logger.debug('RUM insertion from Django middleware '
                    'triggered. Bytes added was %r.',
                    len(result) - len(response.content))

        response.content = result

        if response.get('Content-Length', None):
            response['Content-Length'] = str(len(response.content))

    return response


# Template tag functions for manually inserting RUM header and
# footer into HTML response. A template tag library for
# 'newrelic' will be automatically inserted into set of tag
# libraries when performing step to instrument the middleware.

def newrelic_browser_timing_header():
    from django.utils.safestring import mark_safe

    transaction = current_transaction()
    return transaction and mark_safe(transaction.browser_timing_header()) or ''


def newrelic_browser_timing_footer():
    from django.utils.safestring import mark_safe

    transaction = current_transaction()
    return transaction and mark_safe(transaction.browser_timing_footer()) or ''


# Addition of instrumentation for middleware. Can only do this
# after Django itself has constructed the list of middleware. We
# also insert the RUM middleware into the response middleware.

middleware_instrumentation_lock = threading.Lock()


def wrap_leading_middleware(middleware):

    # Wrapper to be applied to middleware executed prior to the
    # view handler being executed. Records the time spent in the
    # middleware as separate function node and also attempts to
    # name the web transaction after the name of the middleware
    # with success being determined by the priority.

    def wrapper(wrapped):
        # The middleware if a class method would already be
        # bound at this point, so is safe to determine the name
        # when it is being wrapped rather than on each
        # invocation.

        name = callable_name(wrapped)

        def wrapper(wrapped, instance, args, kwargs):
            transaction = current_transaction()

            if transaction is None:
                return wrapped(*args, **kwargs)

            before = (transaction.name, transaction.group)

            with FunctionTrace(name=name):
                try:
                    return wrapped(*args, **kwargs)

                finally:
                    # We want to name the transaction after this
                    # middleware but only if the transaction wasn't
                    # named from within the middleware itself explicitly.

                    after = (transaction.name, transaction.group)
                    if before == after:
                        transaction.set_transaction_name(name, priority=2)

        return FunctionWrapper(wrapped, wrapper)

    for wrapped in middleware:
        yield wrapper(wrapped)


def wrap_view_middleware(middleware):

    # XXX This is no longer being used. The changes to strip the
    # wrapper from the view handler when passed into the function
    # urlresolvers.reverse() solves most of the problems. To back
    # that up, the object wrapper now proxies various special
    # methods so that comparisons like '==' will work. The object
    # wrapper can even be used as a standin for the wrapped object
    # when used as a key in a dictionary and will correctly match
    # the original wrapped object.

    # Wrapper to be applied to view middleware. Records the time
    # spent in the middleware as separate function node and also
    # attempts to name the web transaction after the name of the
    # middleware with success being determined by the priority.
    # This wrapper is special in that it must strip the wrapper
    # from the view handler when being passed to the view
    # middleware to avoid issues where middleware wants to do
    # comparisons between the passed middleware and some other
    # value. It is believed that the view handler should never
    # actually be called from the view middleware so not an
    # issue that no longer wrapped at this point.

    def wrapper(wrapped):
        # The middleware if a class method would already be
        # bound at this point, so is safe to determine the name
        # when it is being wrapped rather than on each
        # invocation.

        name = callable_name(wrapped)

        def wrapper(wrapped, instance, args, kwargs):
            transaction = current_transaction()

            def _wrapped(request, view_func, view_args, view_kwargs):
                # This strips the view handler wrapper before call.

                if hasattr(view_func, '_nr_last_object'):
                    view_func = view_func._nr_last_object

                return wrapped(request, view_func, view_args, view_kwargs)

            if transaction is None:
                return _wrapped(*args, **kwargs)

            before = (transaction.name, transaction.group)

            with FunctionTrace(name=name):
                try:
                    return _wrapped(*args, **kwargs)

                finally:
                    # We want to name the transaction after this
                    # middleware but only if the transaction wasn't
                    # named from within the middleware itself explicitly.

                    after = (transaction.name, transaction.group)
                    if before == after:
                        transaction.set_transaction_name(name, priority=2)

        return FunctionWrapper(wrapped, wrapper)

    for wrapped in middleware:
        yield wrapper(wrapped)


def wrap_trailing_middleware(middleware):

    # Wrapper to be applied to trailing middleware executed
    # after the view handler. Records the time spent in the
    # middleware as separate function node. Transaction is never
    # named after these middleware.

    def wrapper(wrapped):
        # The middleware if a class method would already be
        # bound at this point, so is safe to determine the name
        # when it is being wrapped rather than on each
        # invocation.

        name = callable_name(wrapped)

        def wrapper(wrapped, instance, args, kwargs):
            with FunctionTrace(name=name):
                return wrapped(*args, **kwargs)

        return FunctionWrapper(wrapped, wrapper)

    for wrapped in middleware:
        yield wrapper(wrapped)


def insert_and_wrap_middleware(handler, *args, **kwargs):

    # Use lock to control access by single thread but also as
    # flag to indicate if done the initialisation. Lock will be
    # None if have already done this.

    global middleware_instrumentation_lock

    if not middleware_instrumentation_lock:
        return

    lock = middleware_instrumentation_lock

    lock.acquire()

    # Check again in case two threads grab lock at same time.

    if not middleware_instrumentation_lock:
        lock.release()
        return

    # Set lock to None so we know have done the initialisation.

    middleware_instrumentation_lock = None

    try:

        # Wrap the middleware to undertake timing and name
        # the web transaction. The naming is done as lower
        # priority than that for view handler so view handler
        # name always takes precedence.

        if hasattr(handler, '_request_middleware'):
            handler._request_middleware = list(
                    wrap_leading_middleware(
                    handler._request_middleware))

        if hasattr(handler, '_view_middleware'):
            handler._view_middleware = list(
                    wrap_leading_middleware(
                    handler._view_middleware))

        if hasattr(handler, '_template_response_middleware'):
            handler._template_response_middleware = list(
                  wrap_trailing_middleware(
                  handler._template_response_middleware))

        if hasattr(handler, '_response_middleware'):
            handler._response_middleware = list(
                    wrap_trailing_middleware(
                    handler._response_middleware))

        if hasattr(handler, '_exception_middleware'):
            handler._exception_middleware = list(
                    wrap_trailing_middleware(
                    handler._exception_middleware))

    finally:
        lock.release()


def _nr_wrapper_GZipMiddleware_process_response_(wrapped, instance, args,
        kwargs):

    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    def _bind_params(request, response, *args, **kwargs):
        return request, response

    request, response = _bind_params(*args, **kwargs)

    if should_add_browser_timing(response, transaction):
        with FunctionTrace(
                name=callable_name(browser_timing_insertion)):
            response_with_browser = browser_timing_insertion(
                    response, transaction)

        return wrapped(request, response_with_browser)

    return wrapped(request, response)


def _bind_get_response(request, *args, **kwargs):
    return request


def _nr_wrapper_BaseHandler_get_response_(wrapped, instance, args, kwargs):
    response = wrapped(*args, **kwargs)

    if current_transaction() is None:
        return response

    request = _bind_get_response(*args, **kwargs)

    if hasattr(request, '_nr_exc_info'):
        notice_error(error=request._nr_exc_info, status_code=response.status_code)
        delattr(request, '_nr_exc_info')

    return response


# Post import hooks for modules.

def instrument_django_core_handlers_base(module):

    # Attach a post function to load_middleware() method of
    # BaseHandler to trigger insertion of browser timing
    # middleware and wrapping of middleware for timing etc.

    wrap_post_function(module, 'BaseHandler.load_middleware',
            insert_and_wrap_middleware)

    if six.PY3 and hasattr(module.BaseHandler, 'get_response_async'):
        wrap_function_wrapper(module, 'BaseHandler.get_response_async',
                _nr_wrapper_BaseHandler_get_response_async_)

    wrap_function_wrapper(module, 'BaseHandler.get_response',
            _nr_wrapper_BaseHandler_get_response_)


def instrument_django_gzip_middleware(module):

    wrap_function_wrapper(module, 'GZipMiddleware.process_response',
            _nr_wrapper_GZipMiddleware_process_response_)


def wrap_handle_uncaught_exception(middleware):

    # Wrapper to be applied to handler called when exceptions
    # propagate up to top level from middleware. Records the
    # time spent in the handler as separate function node. Names
    # the web transaction after the name of the handler if not
    # already named at higher priority and capture further
    # errors in the handler.

    name = callable_name(middleware)

    def wrapper(wrapped, instance, args, kwargs):
        transaction = current_transaction()

        if transaction is None:
            return wrapped(*args, **kwargs)

        def _wrapped(request, resolver, exc_info):
            transaction.set_transaction_name(name, priority=1)
            notice_error(exc_info)

            try:
                return wrapped(request, resolver, exc_info)

            except:  # Catch all
                notice_error()
                raise

        with FunctionTrace(name=name):
            return _wrapped(*args, **kwargs)

    return FunctionWrapper(middleware, wrapper)


def instrument_django_core_handlers_wsgi(module):

    # Wrap the WSGI application entry point. If this is also
    # wrapped from the WSGI script file or by the WSGI hosting
    # mechanism then those will take precedence.

    import django

    framework = ('Django', django.get_version())

    module.WSGIHandler.__call__ = WSGIApplicationWrapper(
          module.WSGIHandler.__call__, framework=framework)

    # Wrap handle_uncaught_exception() of WSGIHandler so that
    # can capture exception details of any exception which
    # wasn't caught and dealt with by an exception middleware.
    # The handle_uncaught_exception() function produces a 500
    # error response page and otherwise suppresses the
    # exception, so last chance to do this as exception will not
    # propagate up to the WSGI application.

    if hasattr(module.WSGIHandler, 'handle_uncaught_exception'):
        module.WSGIHandler.handle_uncaught_exception = (
                wrap_handle_uncaught_exception(
                module.WSGIHandler.handle_uncaught_exception))


def wrap_view_handler(wrapped, priority=3):

    # Ensure we don't wrap the view handler more than once. This
    # looks like it may occur in cases where the resolver is
    # called recursively. We flag that view handler was wrapped
    # using the '_nr_django_view_handler' attribute.

    if hasattr(wrapped, '_nr_django_view_handler'):
        return wrapped

    if hasattr(wrapped, "view_class"):
        name = callable_name(wrapped.view_class)
    else:
        name = callable_name(wrapped)

    def wrapper(wrapped, instance, args, kwargs):
        transaction = current_transaction()

        if transaction is None:
            return wrapped(*args, **kwargs)

        transaction.set_transaction_name(name, priority=priority)

        with FunctionTrace(name=name):
            try:
                return wrapped(*args, **kwargs)

            except:  # Catch all
                exc_info = sys.exc_info()
                try:
                    # Store exc_info on the request to check response code
                    # prior to reporting
                    args[0]._nr_exc_info = exc_info
                except:
                    notice_error(exc_info)
                raise

    result = FunctionWrapper(wrapped, wrapper)
    result._nr_django_view_handler = True

    return result


def wrap_url_resolver(wrapped):

    # Wrap URL resolver. If resolver returns valid result then
    # wrap the view handler returned. The type of the result
    # changes across Django versions so need to check and adapt
    # as necessary. For a 404 then a user supplied 404 handler
    # or the default 404 handler should get later invoked and
    # transaction should be named after that.

    name = callable_name(wrapped)

    def wrapper(wrapped, instance, args, kwargs):
        transaction = current_transaction()

        if transaction is None:
            return wrapped(*args, **kwargs)

        if hasattr(transaction, '_nr_django_url_resolver'):
            return wrapped(*args, **kwargs)

        # Tag the transaction so we know when we are in the top
        # level call to the URL resolver as don't want to show
        # the inner ones as would be one for each url pattern.

        transaction._nr_django_url_resolver = True

        def _wrapped(path):
            # XXX This can raise a Resolver404. If this is not dealt
            # with, is this the source of our unnamed 404 requests.

            with FunctionTrace(name=name, label=path):
                result = wrapped(path)

                if type(result) is tuple:
                    callback, callback_args, callback_kwargs = result
                    result = (wrap_view_handler(callback, priority=5),
                            callback_args, callback_kwargs)
                else:
                    result.func = wrap_view_handler(result.func, priority=5)

                return result

        try:
            return _wrapped(*args, **kwargs)

        finally:
            del transaction._nr_django_url_resolver

    return FunctionWrapper(wrapped, wrapper)


def wrap_url_resolver_nnn(wrapped, priority=1):

    # Wrapper to be applied to the URL resolver for errors.

    name = callable_name(wrapped)

    def wrapper(wrapped, instance, args, kwargs):
        transaction = current_transaction()

        if transaction is None:
            return wrapped(*args, **kwargs)

        with FunctionTrace(name=name):
            result = wrapped(*args, **kwargs)
            if callable(result):
                return wrap_view_handler(result, priority=priority)
            else:
                callback, param_dict = result
                return (wrap_view_handler(callback, priority=priority),
                        param_dict)

    return FunctionWrapper(wrapped, wrapper)


def wrap_url_reverse(wrapped):

    # Wrap the URL resolver reverse lookup. Where the view
    # handler is passed in we need to strip any instrumentation
    # wrapper to ensure that it doesn't interfere with the
    # lookup process. Technically this may now not be required
    # as we have improved the proxying in the object wrapper,
    # but do it just to avoid any potential for problems.

    def wrapper(wrapped, instance, args, kwargs):
        def execute(viewname, *args, **kwargs):
            if hasattr(viewname, '_nr_last_object'):
                viewname = viewname._nr_last_object
            return wrapped(viewname, *args, **kwargs)
        return execute(*args, **kwargs)

    return FunctionWrapper(wrapped, wrapper)


def instrument_django_core_urlresolvers(module):

    # Wrap method which maps a string version of a function
    # name as used in urls.py pattern so can capture any
    # exception which is raised during that process.
    # Normally Django captures import errors at this point
    # and then reraises a ViewDoesNotExist exception with
    # details of the original error and traceback being
    # lost. We thus intercept it here so can capture that
    # traceback which is otherwise lost.

    wrap_error_trace(module, 'get_callable')

    # Wrap methods which resolves a request to a view handler.
    # This can be called against a resolver initialised against
    # a custom URL conf associated with a specific request, or a
    # resolver which uses the default URL conf.

    if hasattr(module, 'RegexURLResolver'):
        urlresolver = module.RegexURLResolver
    else:
        urlresolver = module.URLResolver

    urlresolver.resolve = wrap_url_resolver(
            urlresolver.resolve)

    # Wrap methods which resolve error handlers. For 403 and 404
    # we give these higher naming priority over any prior
    # middleware or view handler to give them visibility. For a
    # 500, which will be triggered for unhandled exception, we
    # leave any original name derived from a middleware or view
    # handler in place so error details identify the correct
    # transaction.

    if hasattr(urlresolver, 'resolve403'):
        urlresolver.resolve403 = wrap_url_resolver_nnn(
                urlresolver.resolve403, priority=3)

    if hasattr(urlresolver, 'resolve404'):
        urlresolver.resolve404 = wrap_url_resolver_nnn(
                urlresolver.resolve404, priority=3)

    if hasattr(urlresolver, 'resolve500'):
        urlresolver.resolve500 = wrap_url_resolver_nnn(
                urlresolver.resolve500, priority=1)

    if hasattr(urlresolver, 'resolve_error_handler'):
        urlresolver.resolve_error_handler = wrap_url_resolver_nnn(
                urlresolver.resolve_error_handler, priority=1)

    # Wrap function for performing reverse URL lookup to strip any
    # instrumentation wrapper when view handler is passed in.

    if hasattr(module, 'reverse'):
        module.reverse = wrap_url_reverse(module.reverse)


def instrument_django_urls_base(module):

    # Wrap function for performing reverse URL lookup to strip any
    # instrumentation wrapper when view handler is passed in.

    if hasattr(module, 'reverse'):
        module.reverse = wrap_url_reverse(module.reverse)


def instrument_django_template(module):

    # Wrap methods for rendering of Django templates. The name
    # of the method changed in between Django versions so need
    # to check for which one we have. The name of the function
    # trace node is taken from the name of the template. This
    # should be a relative path with the template loader
    # uniquely associating it with a specific template library.
    # Therefore do not need to worry about making it absolute as
    # meaning should be known in the context of the specific
    # Django site.

    def template_name(template, *args):
        return template.name

    if hasattr(module.Template, '_render'):
        wrap_function_trace(module, 'Template._render',
                name=template_name, group='Template/Render')
    else:
        wrap_function_trace(module, 'Template.render',
                name=template_name, group='Template/Render')

    # Django 1.8 no longer has module.libraries. As automatic way is not
    # preferred we can just skip this now.

    if not hasattr(module, 'libraries'):
        return

    # Register template tags used for manual insertion of RUM
    # header and footer.
    #
    # TODO This can now be installed as a separate tag library
    # so should possibly look at deprecating this automatic
    # way of doing things.

    library = module.Library()
    library.simple_tag(newrelic_browser_timing_header)
    library.simple_tag(newrelic_browser_timing_footer)

    module.libraries['django.templatetags.newrelic'] = library


def wrap_template_block(wrapped):
    def wrapper(wrapped, instance, args, kwargs):
        with FunctionTrace(name=instance.name,
                group='Template/Block'):
            return wrapped(*args, **kwargs)

    return FunctionWrapper(wrapped, wrapper)


def instrument_django_template_loader_tags(module):

    # Wrap template block node for timing, naming the node after
    # the block name as defined in the template rather than
    # function name.

    module.BlockNode.render = wrap_template_block(module.BlockNode.render)


def instrument_django_core_servers_basehttp(module):

    # Allow 'runserver' to be used with Django <= 1.3. To do
    # this we wrap the WSGI application argument on the way in
    # so that the run() method gets the wrapped instance.
    #
    # Although this works, if anyone wants to use it and make
    # it reliable, they may need to first need to patch Django
    # as explained in the ticket:
    #
    #   https://code.djangoproject.com/ticket/16241
    #
    # as the Django 'runserver' is not WSGI compliant due to a
    # bug in its handling of errors when writing response.
    #
    # The way the agent now uses a weakref dictionary for the
    # transaction object may be enough to ensure the prior
    # transaction is cleaned up properly when it is deleted,
    # but not absolutely sure that will always work. Thus is
    # still a risk of error on subsequent request saying that
    # there is an active transaction.
    #
    # TODO Later versions of Django use the wsgiref server
    # instead which will likely need to be dealt with via
    # instrumentation of the wsgiref module or some other means.

    def wrap_wsgi_application_entry_point(server, application, **kwargs):
        return ((server, WSGIApplicationWrapper(application,
            framework='Django'),), kwargs)

    if (not hasattr(module, 'simple_server') and
            hasattr(module.ServerHandler, 'run')):

        # Patch the server to make it work properly.

        def run(self, application):
            try:
                self.setup_environ()
                self.result = application(self.environ, self.start_response)
                self.finish_response()
            except Exception:
                self.handle_error()
            finally:
                self.close()

        def close(self):
            if self.result is not None:
                try:
                    self.request_handler.log_request(
                            self.status.split(' ', 1)[0], self.bytes_sent)
                finally:
                    try:
                        if hasattr(self.result, 'close'):
                            self.result.close()
                    finally:
                        self.result = None
                        self.headers = None
                        self.status = None
                        self.environ = None
                        self.bytes_sent = 0
                        self.headers_sent = False

        # Leaving this out for now to see whether weakref solves
        # the problem.

        # module.ServerHandler.run = run
        # module.ServerHandler.close = close

        # Now wrap it with our instrumentation.

        wrap_in_function(module, 'ServerHandler.run',
                wrap_wsgi_application_entry_point)


def instrument_django_contrib_staticfiles_views(module):
    if not hasattr(module.serve, '_nr_django_view_handler'):
        module.serve = wrap_view_handler(module.serve, priority=3)


def instrument_django_contrib_staticfiles_handlers(module):
    wrap_transaction_name(module, 'StaticFilesHandler.serve')


def instrument_django_views_debug(module):

    # Wrap methods for handling errors when Django debug
    # enabled. For 404 we give this higher naming priority over
    # any prior middleware or view handler to give them
    # visibility. For a 500, which will be triggered for
    # unhandled exception, we leave any original name derived
    # from a middleware or view handler in place so error
    # details identify the correct transaction.

    module.technical_404_response = wrap_view_handler(
            module.technical_404_response, priority=3)
    module.technical_500_response = wrap_view_handler(
            module.technical_500_response, priority=1)


def resolve_view_handler(view, request):
    # We can't intercept the delegated view handler when it
    # is looked up by the dispatch() method so we need to
    # duplicate the lookup mechanism.

    if request.method.lower() in view.http_method_names:
        handler = getattr(view, request.method.lower(),
                view.http_method_not_allowed)
    else:
        handler = view.http_method_not_allowed

    return handler


def wrap_view_dispatch(wrapped):

    # Wrapper to be applied to dispatcher for class based views.

    def wrapper(wrapped, instance, args, kwargs):
        transaction = current_transaction()

        if transaction is None:
            return wrapped(*args, **kwargs)

        def _args(request, *args, **kwargs):
            return request

        view = instance
        request = _args(*args, **kwargs)

        handler = resolve_view_handler(view, request)

        name = callable_name(handler)

        # The priority to be used when naming the transaction is
        # bit tricky. If the transaction name is already that of
        # the class based view, but not the method, then we want
        # the name of the method to override. This can occur
        # where the class based view was registered directly in
        # urls.py as the view handler. In this case we use the
        # priority of 5, matching what would be used by the view
        # handler so that it can override the transaction name.
        #
        # If however the transaction name is unrelated, we
        # preferably don't want it overridden. This can happen
        # where the class based view was invoked explicitly
        # within an existing view handler. In this case we use
        # the priority of 4 so it will not override the view
        # handler name where used as the transaction name.

        priority = 4

        if transaction.group == 'Function':
            if transaction.name == callable_name(view):
                priority = 5

        transaction.set_transaction_name(name, priority=priority)

        with FunctionTrace(name=name):
            return wrapped(*args, **kwargs)

    return FunctionWrapper(wrapped, wrapper)


def instrument_django_views_generic_base(module):
    module.View.dispatch = wrap_view_dispatch(module.View.dispatch)


def instrument_django_http_multipartparser(module):
    wrap_function_trace(module, 'MultiPartParser.parse')


def instrument_django_core_mail(module):
    wrap_function_trace(module, 'mail_admins')
    wrap_function_trace(module, 'mail_managers')
    wrap_function_trace(module, 'send_mail')


def instrument_django_core_mail_message(module):
    wrap_function_trace(module, 'EmailMessage.send')


def _nr_wrapper_BaseCommand___init___(wrapped, instance, args, kwargs):
    instance.handle = FunctionTraceWrapper(instance.handle)
    if hasattr(instance, 'handle_noargs'):
        instance.handle_noargs = FunctionTraceWrapper(instance.handle_noargs)
    return wrapped(*args, **kwargs)


def _nr_wrapper_BaseCommand_run_from_argv_(wrapped, instance, args, kwargs):
    def _args(argv, *args, **kwargs):
        return argv

    _argv = _args(*args, **kwargs)

    subcommand = _argv[1]

    commands = django_settings.instrumentation.scripts.django_admin
    startup_timeout = \
            django_settings.instrumentation.background_task.startup_timeout

    if subcommand not in commands:
        return wrapped(*args, **kwargs)

    application = register_application(timeout=startup_timeout)

    with BackgroundTask(application, subcommand, 'Django'):
        return wrapped(*args, **kwargs)


def instrument_django_core_management_base(module):
    wrap_function_wrapper(module, 'BaseCommand.__init__',
            _nr_wrapper_BaseCommand___init___)
    wrap_function_wrapper(module, 'BaseCommand.run_from_argv',
            _nr_wrapper_BaseCommand_run_from_argv_)


@function_wrapper
def _nr_wrapper_django_inclusion_tag_wrapper_(wrapped, instance,
        args, kwargs):

    name = hasattr(wrapped, '__name__') and wrapped.__name__

    if name is None:
        return wrapped(*args, **kwargs)

    qualname = callable_name(wrapped)

    tags = django_settings.instrumentation.templates.inclusion_tag

    if '*' not in tags and name not in tags and qualname not in tags:
        return wrapped(*args, **kwargs)

    with FunctionTrace(name, group='Template/Tag'):
        return wrapped(*args, **kwargs)


@function_wrapper
def _nr_wrapper_django_inclusion_tag_decorator_(wrapped, instance,
        args, kwargs):

    def _bind_params(func, *args, **kwargs):
        return func, args, kwargs

    func, _args, _kwargs = _bind_params(*args, **kwargs)

    func = _nr_wrapper_django_inclusion_tag_wrapper_(func)

    return wrapped(func, *_args, **_kwargs)


def _nr_wrapper_django_template_base_Library_inclusion_tag_(wrapped,
        instance, args, kwargs):

    return _nr_wrapper_django_inclusion_tag_decorator_(
            wrapped(*args, **kwargs))


@function_wrapper
def _nr_wrapper_django_template_base_InclusionNode_render_(wrapped,
        instance, args, kwargs):

    if wrapped.__self__ is None:
        return wrapped(*args, **kwargs)

    file_name = getattr(wrapped.__self__, '_nr_file_name', None)

    if file_name is None:
        return wrapped(*args, **kwargs)

    name = wrapped.__self__._nr_file_name

    with FunctionTrace(name, 'Template/Include'):
        return wrapped(*args, **kwargs)


def _nr_wrapper_django_template_base_generic_tag_compiler_(wrapped, instance,
        args, kwargs):

    if wrapped.__code__.co_argcount > 6:
        # Django > 1.3.

        def _bind_params(parser, token, params, varargs, varkw, defaults,
                name, takes_context, node_class, *args, **kwargs):
            return node_class
    else:
        # Django <= 1.3.

        def _bind_params(params, defaults, name, node_class, parser, token,
                *args, **kwargs):
            return node_class

    node_class = _bind_params(*args, **kwargs)

    if node_class.__name__ == 'InclusionNode':
        result = wrapped(*args, **kwargs)

        result.render = (
                _nr_wrapper_django_template_base_InclusionNode_render_(
                result.render))

        return result

    return wrapped(*args, **kwargs)


def _nr_wrapper_django_template_base_Library_tag_(wrapped, instance,
        args, kwargs):

    def _bind_params(name=None, compile_function=None, *args, **kwargs):
        return compile_function

    compile_function = _bind_params(*args, **kwargs)

    if not callable(compile_function):
        return wrapped(*args, **kwargs)

    def _get_node_class(compile_function):

        node_class = None

        # Django >= 1.4 uses functools.partial

        if isinstance(compile_function, functools.partial):
            node_class = compile_function.keywords.get('node_class')

        # Django < 1.4 uses their home-grown "curry" function,
        # not functools.partial.

        if (hasattr(compile_function, 'func_closure') and
                hasattr(compile_function, '__name__') and
                compile_function.__name__ == '_curried'):

            # compile_function here is generic_tag_compiler(), which has been
            # curried. To get node_class, we first get the function obj, args,
            # and kwargs of the curried function from the cells in
            # compile_function.func_closure. But, the order of the cells
            # is not consistent from platform to platform, so we need to map
            # them to the variables in compile_function.__code__.co_freevars.

            cells = dict(zip(compile_function.__code__.co_freevars,
                    (c.cell_contents for c in compile_function.func_closure)))

            # node_class is the 4th arg passed to generic_tag_compiler()

            if 'args' in cells and len(cells['args']) > 3:
                node_class = cells['args'][3]

        return node_class

    node_class = _get_node_class(compile_function)

    if node_class is None or node_class.__name__ != 'InclusionNode':
        return wrapped(*args, **kwargs)

    # Climb stack to find the file_name of the include template.
    # While you only have to go up 1 frame when using python with
    # extensions, pure python requires going up 2 frames.

    file_name = None
    stack_levels = 2

    for i in range(1, stack_levels + 1):
        frame = sys._getframe(i)

        if ('generic_tag_compiler' in frame.f_code.co_names and
                'file_name' in frame.f_code.co_freevars):
            file_name = frame.f_locals.get('file_name')

    if file_name is None:
        return wrapped(*args, **kwargs)

    if isinstance(file_name, module_django_template_base.Template):
        file_name = file_name.name

    node_class._nr_file_name = file_name

    return wrapped(*args, **kwargs)


def instrument_django_template_base(module):
    global module_django_template_base
    module_django_template_base = module

    settings = global_settings()

    if 'django.instrumentation.inclusion-tags.r1' in settings.feature_flag:

        if hasattr(module, 'generic_tag_compiler'):
            wrap_function_wrapper(module, 'generic_tag_compiler',
                    _nr_wrapper_django_template_base_generic_tag_compiler_)

        if hasattr(module, 'Library'):
            wrap_function_wrapper(module, 'Library.tag',
                    _nr_wrapper_django_template_base_Library_tag_)

            wrap_function_wrapper(module, 'Library.inclusion_tag',
                _nr_wrapper_django_template_base_Library_inclusion_tag_)


def _nr_wrap_converted_middleware_(middleware, name):

    @function_wrapper
    def _wrapper(wrapped, instance, args, kwargs):
        transaction = current_transaction()

        if transaction is None:
            return wrapped(*args, **kwargs)

        transaction.set_transaction_name(name, priority=2)

        with FunctionTrace(name=name):
            return wrapped(*args, **kwargs)

    return _wrapper(middleware)


def _nr_wrapper_convert_exception_to_response_(wrapped, instance, args,
        kwargs):

    def _bind_params(original_middleware, *args, **kwargs):
        return original_middleware

    original_middleware = _bind_params(*args, **kwargs)
    converted_middleware = wrapped(*args, **kwargs)
    name = callable_name(original_middleware)

    if is_coroutine_function(converted_middleware) or is_asyncio_coroutine(converted_middleware):
        return _nr_wrap_converted_middleware_async_(converted_middleware, name)
    return _nr_wrap_converted_middleware_(converted_middleware, name)


def instrument_django_core_handlers_exception(module):

    if hasattr(module, 'convert_exception_to_response'):
        wrap_function_wrapper(module, 'convert_exception_to_response',
                _nr_wrapper_convert_exception_to_response_)

    if hasattr(module, 'handle_uncaught_exception'):
        module.handle_uncaught_exception = (
                wrap_handle_uncaught_exception(
                module.handle_uncaught_exception))


def instrument_django_core_handlers_asgi(module):
    import django

    framework = ('Django', django.get_version())

    if hasattr(module, 'ASGIHandler'):
        from newrelic.api.asgi_application import wrap_asgi_application
        wrap_asgi_application(module, 'ASGIHandler.__call__', framework=framework)

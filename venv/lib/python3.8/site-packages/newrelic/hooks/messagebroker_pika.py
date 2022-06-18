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
import time
import types

from newrelic.api.application import application_instance
from newrelic.api.message_transaction import MessageTransaction
from newrelic.api.function_trace import FunctionTrace
from newrelic.api.message_trace import MessageTrace
from newrelic.api.transaction import current_transaction
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import (wrap_function_wrapper, wrap_object,
        FunctionWrapper, function_wrapper, resolve_path, apply_patch)


_START_KEY = '_nr_start_time'
KWARGS_ERROR = 'Supportability/hooks/pika/kwargs_error'


def _add_consume_rabbitmq_trace(transaction, method, properties,
        nr_start_time, queue_name=None):

    routing_key = None
    if hasattr(method, 'routing_key'):
        routing_key = method.routing_key

    properties = properties and properties.__dict__ or {}

    correlation_id = properties.get('correlation_id')
    reply_to = properties.get('reply_to')
    headers = properties.get('headers')

    # Do not record dt headers in the segment parameters
    if headers:
        headers.pop(
                MessageTrace.cat_id_key, None)
        headers.pop(
                MessageTrace.cat_transaction_key, None)
        headers.pop(
                MessageTrace.cat_distributed_trace_key, None)
        headers.pop('traceparent', None)
        headers.pop('tracestate', None)

    # The transaction may have started after the message was received. In this
    # case, the start time is reset to the true transaction start time.
    transaction.start_time = min(nr_start_time,
            transaction.start_time)

    params = {}
    if routing_key is not None:
        params['routing_key'] = routing_key
    if correlation_id is not None:
        params['correlation_id'] = correlation_id
    if reply_to is not None:
        params['reply_to'] = reply_to
    if headers is not None:
        params['headers'] = headers
    if queue_name is not None:
        params['queue_name'] = queue_name

    # create a trace starting at the time the message was received
    trace = MessageTrace(library='RabbitMQ',
            operation='Consume',
            destination_type='Exchange',
            destination_name=method.exchange or 'Default',
            params=params)
    trace.__enter__()
    trace.start_time = nr_start_time
    trace.__exit__(None, None, None)


def _bind_basic_publish(
        exchange, routing_key, body, properties=None, *args, **kwargs):
    return (exchange, routing_key, body, properties, args, kwargs)


def _nr_wrapper_basic_publish(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    from pika import BasicProperties

    (exchange, routing_key, body, properties, args, kwargs) = (
            _bind_basic_publish(*args, **kwargs))
    properties = properties or BasicProperties()
    properties.headers = properties.headers or {}
    user_headers = properties.headers.copy()

    # Do not record dt headers in the segment parameters
    user_headers.pop(MessageTrace.cat_id_key, None)
    user_headers.pop(MessageTrace.cat_transaction_key, None)
    user_headers.pop(MessageTrace.cat_distributed_trace_key, None)
    user_headers.pop("traceparent", None)
    user_headers.pop("tracestate", None)

    args = (exchange, routing_key, body, properties) + args

    params = {}
    if routing_key is not None:
        params['routing_key'] = routing_key
    if properties.correlation_id is not None:
        params['correlation_id'] = properties.correlation_id
    if properties.reply_to is not None:
        params['reply_to'] = properties.reply_to
    if user_headers:
        params['headers'] = user_headers

    with MessageTrace(library='RabbitMQ',
            operation='Produce',
            destination_type='Exchange',
            destination_name=exchange or 'Default',
            params=params):
        cat_headers = MessageTrace.generate_request_headers(transaction)
        properties.headers.update(cat_headers)
        return wrapped(*args, **kwargs)


def _wrap_Channel_get_callback(module, obj, wrap_get):
    def _nr_wrapper_basic_get(wrapped, instance, args, kwargs):

        @function_wrapper
        def callback_wrapper(callback, _instance, _args, _kwargs):
            transaction = current_transaction()

            if transaction is None:
                return callback(*_args, **_kwargs)

            if not _kwargs:
                method, properties = _args[1:3]
                start_time = getattr(callback_wrapper, '_nr_start_time', None)

                _add_consume_rabbitmq_trace(transaction,
                        method=method,
                        properties=properties,
                        nr_start_time=start_time,
                        queue_name=queue)
            else:
                m = transaction._transaction_metrics.get(KWARGS_ERROR, 0)
                transaction._transaction_metrics[KWARGS_ERROR] = m + 1

            name = callable_name(callback)
            with FunctionTrace(name=name):
                return callback(*_args, **_kwargs)

        callback_wrapper._nr_start_time = time.time()
        queue, args, kwargs = wrap_get(callback_wrapper, *args, **kwargs)
        return wrapped(*args, **kwargs)

    wrap_function_wrapper(module, obj, _nr_wrapper_basic_get)


def _nr_wrapper_Basic_Deliver_init_(wrapper, instance, args, kwargs):
    ret = wrapper(*args, **kwargs)
    instance._nr_start_time = time.time()
    return ret


def _nr_wrap_BlockingChannel___init__(wrapped, instance, args, kwargs):
    ret = wrapped(*args, **kwargs)
    impl = getattr(instance, '_impl', None)
    # Patch in the original basic_consume to avoid wrapping twice
    if impl and hasattr(impl, '_nr_basic_consume'):
        impl.basic_consume = impl.basic_consume.__wrapped__
    return ret


def _wrap_basic_consume_BlockingChannel_old(wrapper,
        consumer_callback, queue, *args, **kwargs):
    args = (wrapper(consumer_callback), queue) + args
    return queue, args, kwargs


def _wrap_basic_consume_Channel_old(wrapper, consumer_callback, queue='',
        *args, **kwargs):
    return queue, (wrapper(consumer_callback), queue) + args, kwargs


def _wrap_basic_consume_Channel(wrapper, queue, on_message_callback, *args,
        **kwargs):
    args = (queue, wrapper(on_message_callback)) + args
    return queue, args, kwargs


def _wrap_basic_get_Channel(wrapper, queue, callback, *args, **kwargs):
    args = (queue, wrapper(callback)) + args
    return queue, args, kwargs


def _wrap_basic_get_Channel_old(wrapper, callback=None, queue='',
        *args, **kwargs):
    if callback is not None:
        callback = wrapper(callback)
    args = (callback, queue) + args
    return queue, args, kwargs


def _ConsumeGeneratorWrapper(wrapped):

    def wrapper(wrapped, instance, args, kwargs):
        def _possibly_create_traces(yielded):
            # This generator can be called either outside of a transaction, or
            # within the context of an existing transaction.  There are 3
            # possibilities we need to handle: (Note that this is similar to
            # our Celery instrumentation)
            #
            #   1. In an inactive transaction
            #
            #      If the end_of_transaction() or ignore_transaction() API
            #      calls have been invoked, this generator may be called in the
            #      context of an inactive transaction. In this case, don't wrap
            #      the generator in any way. Just run the original generator.
            #
            #   2. In an active transaction
            #
            #      Do nothing.
            #
            #   3. Outside of a transaction
            #
            #      Since it's not running inside of an existing transaction, we
            #      want to create a new background transaction for it but only
            #      when we've subscribed.

            transaction = current_transaction(active_only=False)
            method, properties, _ = yielded

            if transaction:
                # 1. In an inactive transaction
                # 2. In an active transaction
                return

            else:
                # 3. Outside of a transaction
                exchange = method.exchange or 'Default'
                routing_key = getattr(method, 'routing_key', None)
                headers = None
                reply_to = None
                correlation_id = None
                if properties is not None:
                    headers = getattr(properties, 'headers', None)
                    reply_to = getattr(properties, 'reply_to', None)
                    correlation_id = getattr(
                            properties, 'correlation_id', None)

                # Create a messagebroker task for each iteration through the
                # generator. This is important because it is foreseeable that
                # the generator process lasts a long time and consumes many
                # many messages.

                bt = MessageTransaction(
                        application=application_instance(),
                        library='RabbitMQ',
                        destination_type='Exchange',
                        destination_name=exchange,
                        routing_key=routing_key,
                        headers=headers,
                        reply_to=reply_to,
                        correlation_id=correlation_id)
                bt.__enter__()

                return bt

        def _generator(generator):
            try:
                value = None
                exc = (None, None, None)
                created_bt = None

                while True:
                    if any(exc):
                        to_throw = exc
                        exc = (None, None, None)
                        yielded = generator.throw(*to_throw)
                    else:
                        yielded = generator.send(value)

                    if yielded is not None and any(yielded):
                        created_bt = _possibly_create_traces(yielded)

                    try:
                        value = yield yielded
                    except Exception:
                        exc = sys.exc_info()

                    if created_bt:
                        created_bt.__exit__(*exc)

            except GeneratorExit:
                raise
            except StopIteration:
                pass
            except Exception:
                exc = sys.exc_info()
                raise

            finally:
                generator.close()
                if created_bt:
                    created_bt.__exit__(*exc)

        try:
            result = wrapped(*args, **kwargs)
        except:
            raise
        else:
            if isinstance(result, types.GeneratorType):
                return _generator(result)
            else:
                return result

    return FunctionWrapper(wrapped, wrapper)


def _wrap_Channel_consume_callback(module, obj, wrap_consume):

    @function_wrapper
    def _nr_wrapper_Channel_consume_(wrapped, channel, args, kwargs):

        @function_wrapper
        def callback_wrapper(wrapped, instance, args, kwargs):
            name = callable_name(wrapped)

            transaction = current_transaction(active_only=False)

            if transaction and (transaction.ignore_transaction or
                    transaction.stopped):
                return wrapped(*args, **kwargs)
            elif transaction:
                with FunctionTrace(name=name):
                    return wrapped(*args, **kwargs)
            else:
                if hasattr(channel, '_nr_disable_txn_tracing'):
                    return wrapped(*args, **kwargs)

                # Keyword arguments are unknown since this is a user
                # defined callback
                exchange = 'Unknown'
                routing_key = None
                headers = None
                reply_to = None
                correlation_id = None
                unknown_kwargs = False
                if not kwargs:
                    method, properties = args[1:3]
                    exchange = method.exchange or 'Default'
                    routing_key = getattr(method, 'routing_key', None)
                    if properties is not None:
                        headers = getattr(properties, 'headers', None)
                        reply_to = getattr(properties, 'reply_to', None)
                        correlation_id = getattr(
                                properties, 'correlation_id', None)
                else:
                    unknown_kwargs = True

                with MessageTransaction(
                        application=application_instance(),
                        library='RabbitMQ',
                        destination_type='Exchange',
                        destination_name=exchange,
                        routing_key=routing_key,
                        headers=headers,
                        queue_name=queue,
                        reply_to=reply_to,
                        correlation_id=correlation_id) as mt:

                    # Improve transaction naming
                    _new_txn_name = 'RabbitMQ/Exchange/%s/%s' % (exchange,
                            name)
                    mt.set_transaction_name(_new_txn_name, group='Message')

                    # Record that something went horribly wrong
                    if unknown_kwargs:
                        m = mt._transaction_metrics.get(KWARGS_ERROR, 0)
                        mt._transaction_metrics[KWARGS_ERROR] = m + 1

                    return wrapped(*args, **kwargs)

        queue, args, kwargs = wrap_consume(callback_wrapper, *args, **kwargs)
        return wrapped(*args, **kwargs)

    # Normally, wrap_object(module, object, ...) would be used here.
    # Since we need to attach the _nr_basic_consume attribute to the class, we
    # use resolve_path to retrieve the class object (parent), apply the
    # patch (as wrap_object would) and attach the _nr_basic_consume attribute
    # after patching the method.
    (parent, attribute, original) = resolve_path(module, obj)
    apply_patch(parent, attribute, _nr_wrapper_Channel_consume_(original))
    parent._nr_basic_consume = True


def _disable_channel_transactions(wrapped, instance, args, kwargs):
    ch = wrapped(*args, **kwargs)
    ch._nr_disable_txn_tracing = True
    return ch


def instrument_pika_adapters(module):
    import pika
    version = tuple(int(num) for num in pika.__version__.split('.', 1)[0])

    if version[0] < 1:
        wrap_consume = _wrap_basic_consume_BlockingChannel_old
    else:
        wrap_consume = _wrap_basic_consume_Channel

    _wrap_Channel_consume_callback(
            module.blocking_connection,
            'BlockingChannel.basic_consume',
            wrap_consume)
    wrap_function_wrapper(module.blocking_connection,
            'BlockingChannel.__init__', _nr_wrap_BlockingChannel___init__)
    wrap_object(module.blocking_connection, 'BlockingChannel.consume',
            _ConsumeGeneratorWrapper)

    if hasattr(module, 'tornado_connection'):
        wrap_function_wrapper(module.tornado_connection,
                'TornadoConnection.channel', _disable_channel_transactions)


def instrument_pika_spec(module):
    wrap_function_wrapper(module.Basic.Deliver, '__init__',
            _nr_wrapper_Basic_Deliver_init_)


def instrument_pika_channel(module):
    import pika
    version = tuple(int(num) for num in pika.__version__.split('.', 1)[0])

    if version[0] < 1:
        wrap_consume = _wrap_basic_consume_Channel_old
        wrap_get = _wrap_basic_get_Channel_old
    else:
        wrap_consume = _wrap_basic_consume_Channel
        wrap_get = _wrap_basic_get_Channel

    wrap_function_wrapper(module, 'Channel.basic_publish',
            _nr_wrapper_basic_publish)

    _wrap_Channel_get_callback(module, 'Channel.basic_get', wrap_get)
    _wrap_Channel_consume_callback(
            module,
            'Channel.basic_consume',
            wrap_consume)

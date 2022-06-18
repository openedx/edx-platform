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

from newrelic.api.message_trace import message_trace
from newrelic.api.datastore_trace import datastore_trace
from newrelic.api.external_trace import ExternalTrace
from newrelic.common.object_wrapper import wrap_function_wrapper


def extract_sqs(*args, **kwargs):
    queue_value = kwargs.get('QueueUrl', 'Unknown')
    return queue_value.rsplit('/', 1)[-1]


def extract(argument_names, default=None):
    def extractor_list(*args, **kwargs):
        for argument_name in argument_names:
            argument_value = kwargs.get(argument_name)
            if argument_value:
                return argument_value
        return default

    def extractor_string(*args, **kwargs):
        return kwargs.get(argument_names, default)

    if isinstance(argument_names, str):
        return extractor_string

    return extractor_list


CUSTOM_TRACE_POINTS = {
    ('sns', 'publish'): message_trace(
            'SNS', 'Produce', 'Topic',
            extract(('TopicArn', 'TargetArn'), 'PhoneNumber')),
    ('dynamodb', 'put_item'): datastore_trace(
            'DynamoDB', extract('TableName'), 'put_item'),
    ('dynamodb', 'get_item'): datastore_trace(
            'DynamoDB', extract('TableName'), 'get_item'),
    ('dynamodb', 'update_item'): datastore_trace(
            'DynamoDB', extract('TableName'), 'update_item'),
    ('dynamodb', 'delete_item'): datastore_trace(
            'DynamoDB', extract('TableName'), 'delete_item'),
    ('dynamodb', 'create_table'): datastore_trace(
            'DynamoDB', extract('TableName'), 'create_table'),
    ('dynamodb', 'delete_table'): datastore_trace(
            'DynamoDB', extract('TableName'), 'delete_table'),
    ('dynamodb', 'query'): datastore_trace(
            'DynamoDB', extract('TableName'), 'query'),
    ('dynamodb', 'scan'): datastore_trace(
            'DynamoDB', extract('TableName'), 'scan'),
    ('sqs', 'send_message'): message_trace(
            'SQS', 'Produce', 'Queue', extract_sqs),
    ('sqs', 'send_message_batch'): message_trace(
            'SQS', 'Produce', 'Queue', extract_sqs),
    ('sqs', 'receive_message'): message_trace(
            'SQS', 'Consume', 'Queue', extract_sqs),
}


def bind__create_api_method(py_operation_name, operation_name, service_model,
        *args, **kwargs):
    return (py_operation_name, service_model)


def _nr_clientcreator__create_api_method_(wrapped, instance, args, kwargs):
    (py_operation_name, service_model) = \
            bind__create_api_method(*args, **kwargs)

    service_name = service_model.service_name.lower()
    tracer = CUSTOM_TRACE_POINTS.get((service_name, py_operation_name))

    wrapped = wrapped(*args, **kwargs)

    if not tracer:
        return wrapped

    return tracer(wrapped)


def _bind_make_request_params(operation_model, request_dict, *args, **kwargs):
    return operation_model, request_dict


def _nr_endpoint_make_request_(wrapped, instance, args, kwargs):
    operation_model, request_dict = _bind_make_request_params(*args, **kwargs)
    url = request_dict.get('url', '')
    method = request_dict.get('method', None)

    with ExternalTrace(library='botocore', url=url, method=method) as trace:

        try:
            trace._add_agent_attribute('aws.operation', operation_model.name)
        except:
            pass

        result = wrapped(*args, **kwargs)
        try:
            request_id = result[1]['ResponseMetadata']['RequestId']
            trace._add_agent_attribute('aws.requestId', request_id)
        except:
            pass
        return result


def instrument_botocore_endpoint(module):
    wrap_function_wrapper(module, 'Endpoint.make_request',
            _nr_endpoint_make_request_)


def instrument_botocore_client(module):
    wrap_function_wrapper(module, 'ClientCreator._create_api_method',
            _nr_clientcreator__create_api_method_)

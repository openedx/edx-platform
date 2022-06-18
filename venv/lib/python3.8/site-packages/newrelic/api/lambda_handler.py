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
import warnings
from newrelic.common.object_wrapper import FunctionWrapper
from newrelic.api.transaction import current_transaction
from newrelic.api.web_transaction import WebTransaction
from newrelic.api.application import application_instance
from newrelic.core.attribute import truncate
from newrelic.core.config import global_settings


COLD_START_RECORDED = False
MEGABYTE_IN_BYTES = 2**20


def extract_event_source_arn(event):
    try:
        arn = event.get('streamArn') or \
              event.get('deliveryStreamArn')

        if not arn:
            record = event['Records'][0]
            arn = record.get('eventSourceARN') or \
                  record.get('EventSubscriptionArn') or \
                  record['s3']['bucket']['arn']

        return truncate(str(arn))
    except Exception:
        pass


def _LambdaHandlerWrapper(wrapped, application=None, name=None,
        group=None):

    def _nr_lambda_handler_wrapper_(wrapped, instance, args, kwargs):
        # Check to see if any transaction is present, even an inactive
        # one which has been marked to be ignored or which has been
        # stopped already.

        transaction = current_transaction(active_only=False)

        if transaction:
            return wrapped(*args, **kwargs)

        try:
            event, context = args[:2]
        except Exception:
            return wrapped(*args, **kwargs)

        target_application = application

        # If application has an activate() method we assume it is an
        # actual application. Do this rather than check type so that
        # can easily mock it for testing.

        # FIXME Should this allow for multiple apps if a string.

        if not hasattr(application, 'activate'):
            target_application = application_instance(application)

        try:
            request_method = event['httpMethod']
            request_path = event['path']
            headers = event['headers']
            query_params = event.get('multiValueQueryStringParameters')
            background_task = False
        except Exception:
            request_method = None
            request_path = None
            headers = None
            query_params = None
            background_task = True

        transaction_name = name or getattr(context, 'function_name', None)

        transaction = WebTransaction(
                target_application,
                transaction_name,
                group=group,
                request_method=request_method,
                request_path=request_path,
                headers=headers)

        transaction.background_task = background_task

        request_id = getattr(context, 'aws_request_id', None)
        aws_arn = getattr(context, 'invoked_function_arn', None)
        event_source = extract_event_source_arn(event)

        if request_id:
            transaction._add_agent_attribute('aws.requestId', request_id)
        if aws_arn:
            transaction._add_agent_attribute('aws.lambda.arn', aws_arn)
        if event_source:
            transaction._add_agent_attribute(
                    'aws.lambda.eventSource.arn', event_source)

        # COLD_START_RECORDED is initialized to "False" when the container
        # first starts up, and will remain that way until the below lines
        # of code are encountered during the first transaction after the cold
        # start. We record this occurence on the transaction so that an
        # attribute is created, and then set COLD_START_RECORDED to False so
        # that the attribute is not created again during future invocations of
        # this container.

        global COLD_START_RECORDED
        if COLD_START_RECORDED is False:
            transaction._add_agent_attribute('aws.lambda.coldStart', True)
            COLD_START_RECORDED = True

        settings = global_settings()
        if query_params and not settings.high_security:
            try:
                transaction._request_params.update(query_params)
            except:
                pass

        if not settings.aws_lambda_metadata and aws_arn:
            settings.aws_lambda_metadata['arn'] = aws_arn

        with transaction:
            result = wrapped(*args, **kwargs)

            if not background_task:
                try:
                    status_code = result.get('statusCode')
                    response_headers = result.get('headers')

                    try:
                        response_headers = response_headers.items()
                    except Exception:
                        response_headers = None

                    transaction.process_response(status_code, response_headers)
                except Exception:
                    pass

            return result

    return FunctionWrapper(wrapped, _nr_lambda_handler_wrapper_)


def LambdaHandlerWrapper(*args, **kwargs):

    warnings.warn((
        'The LambdaHandlerWrapper API has been deprecated. Please use the '
        'APIs provided in the newrelic-lambda package.'
    ), DeprecationWarning)

    return _LambdaHandlerWrapper(*args, **kwargs)


def lambda_handler(application=None, name=None, group=None):

    warnings.warn((
        'The lambda_handler API has been deprecated. Please use the '
        'APIs provided in the newrelic-lambda package.'
    ), DeprecationWarning)

    return functools.partial(_LambdaHandlerWrapper, application=application,
            name=name, group=group)

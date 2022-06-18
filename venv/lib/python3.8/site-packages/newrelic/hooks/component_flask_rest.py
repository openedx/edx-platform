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

from newrelic.api.transaction import current_transaction
from newrelic.api.time_trace import notice_error
from newrelic.common.object_wrapper import wrap_function_wrapper


def status_code(exc, value, tb):
    from werkzeug.exceptions import HTTPException

    # Werkzeug HTTPException can be raised internally by Flask or in
    # user code if they mix Flask with Werkzeug. Filter based on the
    # HTTP status code.

    if isinstance(value, HTTPException):
        return value.code


def _nr_wrap_Api_handle_error_(wrapped, instance, args, kwargs):

    # If calling wrapped raises an exception, the error will bubble up to
    # flask's exception handler and we will capture it there.
    resp = wrapped(*args, **kwargs)

    notice_error(status_code=status_code)

    return resp


def instrument_flask_rest(module):
    wrap_function_wrapper(module, 'Api.handle_error',
            _nr_wrap_Api_handle_error_)

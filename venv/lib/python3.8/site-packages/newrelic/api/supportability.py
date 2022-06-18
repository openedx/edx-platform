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
from newrelic.common.object_wrapper import function_wrapper
from newrelic.core.config import global_settings


def wrap_api_call(method, method_name):
    metric_name = 'Supportability/api/%s' % method_name

    @function_wrapper
    def _nr_wrap_api_call_(wrapped, instance, args, kwargs):
        settings = global_settings()

        # agent is not initialized / enabled
        if settings.debug.disable_api_supportability_metrics:
            return wrapped(*args, **kwargs)

        transaction = current_transaction()

        if transaction:
            m = transaction._transaction_metrics.get(metric_name, 0)
            transaction._transaction_metrics[metric_name] = m + 1

        return wrapped(*args, **kwargs)

    return _nr_wrap_api_call_(method)

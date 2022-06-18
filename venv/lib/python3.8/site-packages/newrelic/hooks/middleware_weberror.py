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

from newrelic.api.external_trace import wrap_external_trace
from newrelic.api.function_trace import wrap_function_trace

def instrument_weberror_errormiddleware(module):

    wrap_function_trace(module, 'handle_exception')

def instrument_weberror_reporter(module):

    def smtp_url(reporter, *args, **kwargs):
        return 'smtp://' + reporter.smtp_server

    wrap_external_trace(module, 'EmailReporter.report', 'weberror', smtp_url)
    wrap_function_trace(module, 'EmailReporter.report')

    wrap_function_trace(module, 'LogReporter.report')
    wrap_function_trace(module, 'FileReporter.report')

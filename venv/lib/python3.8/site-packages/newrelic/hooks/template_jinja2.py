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

import newrelic.api.function_trace

def name_template_render(self, *args, **kwargs):
    return self.name or self.filename

def name_template_compile(self, source, name=None, filename=None, raw=False,
            defer_init=False):
    return name or '<template>'

def instrument(module):

    if module.__name__ == 'jinja2.environment':

        newrelic.api.function_trace.wrap_function_trace(
                module, 'Template.render',
                name_template_render, 'Template/Render')
        newrelic.api.function_trace.wrap_function_trace(
                module, 'Environment.compile',
                name_template_compile, 'Template/Compile')

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

import newrelic.api.solr_trace

def instrument(module):

    if hasattr(module.Solr, 'search'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.search', 'pysolr', 'query')
    if hasattr(module.Solr, 'more_like_this'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.more_like_this', 'pysolr', 'query')
    if hasattr(module.Solr, 'suggest_terms'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.suggest_terms', 'pysolr', 'query')
    if hasattr(module.Solr, 'add'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.add', 'pysolr', 'add')
    if hasattr(module.Solr, 'delete'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.delete', 'pysolr', 'delete')
    if hasattr(module.Solr, 'commit'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.commit', 'pysolr', 'commit')
    if hasattr(module.Solr, 'optimize'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.optimize', 'pysolr', 'optimize')

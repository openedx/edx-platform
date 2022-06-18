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

from newrelic.packages import six

from newrelic.api.datastore_trace import DatastoreTrace
from newrelic.api.transaction import current_transaction
from newrelic.common.object_wrapper import wrap_function_wrapper

# An index name can be a string, None or a sequence. In the case of None
# an empty string or '*', it is the same as using '_all'. When a string
# it can also be a comma separated list of index names. A sequence
# obviously can also be more than one index name. Where we are certain
# there is only a single index name we use it, otherwise we use 'other'.

def _index_name(index):
    if not index or index == '*':
        return '_all'
    if not isinstance(index, six.string_types) or ',' in index:
        return 'other'
    return index

def _extract_kwargs_index(*args, **kwargs):
    return _index_name(kwargs.get('index'))

def _extract_args_index(index=None, *args, **kwargs):
    return _index_name(index)

def _extract_args_metric_index(metric=None, index=None, *args, **kwargs):
    return _index_name(index)

_elasticsearch_client_methods = (
    ('bulk', None),
    ('bulk_index', _extract_args_index),
    ('close_index', None),
    ('cluster_state', _extract_args_metric_index),
    ('count', _extract_kwargs_index),
    ('create_index', _extract_args_index),
    ('delete', _extract_args_index),
    ('delete_all', _extract_args_index),
    ('delete_all_indexes', None),
    ('delete_by_query', _extract_args_index),
    ('delete_index', _extract_args_index),
    ('flush', _extract_args_index),
    ('gateway_snapshot', _extract_args_index),
    ('get', _extract_args_index),
    ('get_aliases', _extract_args_index),
    ('get_mapping', _extract_args_index),
    ('get_settings', _extract_args_index),
    ('health', _extract_args_index),
    ('index', _extract_args_index),
    ('more_like_this', _extract_args_index),
    ('multi_get', None),
    ('open_index', _extract_args_index),
    ('optimize', _extract_args_index),
    ('percolate', _extract_args_index),
    ('put_mapping', _extract_args_index),
    ('refresh', _extract_args_index),
    ('search', _extract_kwargs_index),
    ('send_request', None),
    ('status', _extract_args_index),
    ('update', _extract_args_index),
    ('update_aliases', None),
    ('update_all_settings', None),
    ('update_settings', _extract_args_index),
)

def wrap_elasticsearch_client_method(module, name, arg_extractor):
    def _nr_wrapper_ElasticSearch_method_(wrapped, instance, args, kwargs):
        transaction = current_transaction()

        if transaction is None:
            return wrapped(*args, **kwargs)

        # When arg_extractor is None, it means there is no target field
        # associated with this method. Hence this method will only
        # create an operation metric and no statement metric. This is
        # handled by setting the target to None when calling the
        # DatastoreTrace.

        if arg_extractor is None:
            index = None
        else:
            index = arg_extractor(*args, **kwargs)

        with DatastoreTrace(product='Elasticsearch',
                target=index, operation=name):
            return wrapped(*args, **kwargs)

    if hasattr(module.ElasticSearch, name):
        wrap_function_wrapper(module.ElasticSearch, name,
                _nr_wrapper_ElasticSearch_method_)

def instrument_pyelasticsearch_client(module):
    for name, arg_extractor in _elasticsearch_client_methods:
        wrap_elasticsearch_client_method(module, name, arg_extractor)

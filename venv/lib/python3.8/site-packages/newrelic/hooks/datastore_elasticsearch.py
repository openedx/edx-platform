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

def _extract_args_body_index(body=None, index=None, *args, **kwargs):
    return _index_name(index)

def _extract_args_doctype_body_index(doc_type=None, body=None, index=None,
        *args, **kwargs):
    return _index_name(index)

def _extract_args_field_index(field=None, index=None, *args, **kwargs):
    return _index_name(index)

def _extract_args_name_body_index(name=None, body=None, index=None,
        *args, **kwargs):
    return _index_name(index)

def _extract_args_name_index(name=None, index=None, *args, **kwargs):
    return _index_name(index)

def _extract_args_metric_index(metric=None, index=None, *args, **kwargs):
    return _index_name(index)

def wrap_elasticsearch_client_method(owner, name, arg_extractor, prefix=None):
    def _nr_wrapper_Elasticsearch_method_(wrapped, instance, args, kwargs):
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

        if prefix:
            operation = '%s.%s' % (prefix, name)
        else:
            operation = name

        transaction._nr_datastore_instance_info = (None, None, None)

        dt = DatastoreTrace(
                product='Elasticsearch',
                target=index,
                operation=operation
        )

        with dt:
            result = wrapped(*args, **kwargs)

            instance_info = transaction._nr_datastore_instance_info
            host, port_path_or_id, _ = instance_info

            dt.host = host
            dt.port_path_or_id = port_path_or_id

            return result

    if hasattr(owner, name):
        wrap_function_wrapper(owner, name, _nr_wrapper_Elasticsearch_method_)

_elasticsearch_client_methods = (
    ('abort_benchmark', None),
    ('benchmark', _extract_args_index),
    ('bulk', None),
    ('clear_scroll', None),
    ('count', _extract_args_index),
    ('count_percolate', _extract_args_index),
    ('create', _extract_args_index),
    ('delete', _extract_args_index),
    ('delete_by_query', _extract_args_index),
    ('delete_script', None),
    ('delete_template', None),
    ('exists', _extract_args_index),
    ('explain', _extract_args_index),
    ('get', _extract_args_index),
    ('get_script', None),
    ('get_source', _extract_args_index),
    ('get_template', None),
    ('index', _extract_args_index),
    ('info', None),
    ('list_benchmarks', _extract_args_index),
    ('mget', None),
    ('mlt', _extract_args_index),
    ('mpercolate', _extract_args_body_index),
    ('msearch', None),
    ('mtermvectors', None),
    ('percolate', _extract_args_index),
    ('ping', None),
    ('put_script', None),
    ('put_template', None),
    ('scroll', None),
    ('search', _extract_args_index),
    ('search_exists', _extract_args_index),
    ('search_shards', _extract_args_index),
    ('search_template', _extract_args_index),
    ('suggest', _extract_args_body_index),
    ('termvector', _extract_args_index),
    ('termvectors', None),
    ('update', _extract_args_index),
)

def instrument_elasticsearch_client(module):
    for name, arg_extractor in _elasticsearch_client_methods:
        wrap_elasticsearch_client_method(module.Elasticsearch, name,
                arg_extractor)

_elasticsearch_client_indices_methods = (
    ('analyze', _extract_args_index),
    ('clear_cache', _extract_args_index),
    ('close', _extract_args_index),
    ('create', _extract_args_index),
    ('delete', _extract_args_index),
    ('delete_alias', _extract_args_index),
    ('delete_mapping', _extract_args_index),
    ('delete_template', None),
    ('delete_warmer', _extract_args_index),
    ('exists', _extract_args_index),
    ('exists_alias', _extract_args_name_index),
    ('exists_template', None),
    ('exists_type', _extract_args_index),
    ('flush', _extract_args_index),
    ('get', _extract_args_index),
    ('get_alias', _extract_args_index),
    ('get_aliases', _extract_args_index),
    ('get_mapping', _extract_args_index),
    ('get_field_mapping', _extract_args_field_index),
    ('get_settings', _extract_args_index),
    ('get_template', None),
    ('get_upgrade', _extract_args_index),
    ('get_warmer', _extract_args_index),
    ('open', _extract_args_index),
    ('optimize', _extract_args_index),
    ('put_alias', _extract_args_name_index),
    ('put_mapping', _extract_args_doctype_body_index),
    ('put_settings', _extract_args_body_index),
    ('put_template', None),
    ('put_warmer', _extract_args_name_body_index),
    ('recovery', _extract_args_index),
    ('refresh', _extract_args_index),
    ('segments', _extract_args_index),
    ('snapshot_index', _extract_args_index),
    ('stats', _extract_args_index),
    ('status', _extract_args_index),
    ('update_aliases', None),
    ('upgrade', _extract_args_index),
    ('validate_query', _extract_args_index),
)

def instrument_elasticsearch_client_indices(module):
    for name, arg_extractor in _elasticsearch_client_indices_methods:
        wrap_elasticsearch_client_method(module.IndicesClient, name,
                arg_extractor, 'indices')

_elasticsearch_client_cat_methods = (
    ('aliases', None),
    ('allocation', None),
    ('count', _extract_args_index),
    ('fielddata', None),
    ('health', None),
    ('help', None),
    ('indices', _extract_args_index),
    ('master', None),
    ('nodes', None),
    ('pending_tasks', None),
    ('plugins', None),
    ('recovery', _extract_args_index),
    ('shards', _extract_args_index),
    ('segments', _extract_args_index),
    ('thread_pool', None),
)

def instrument_elasticsearch_client_cat(module):
    for name, arg_extractor in _elasticsearch_client_cat_methods:
        wrap_elasticsearch_client_method(module.CatClient, name,
                arg_extractor, 'cat')

_elasticsearch_client_cluster_methods = (
    ('get_settings', None),
    ('health', _extract_args_index),
    ('pending_tasks', None),
    ('put_settings', None),
    ('reroute', None),
    ('state', _extract_args_metric_index),
    ('stats', None),
)

def instrument_elasticsearch_client_cluster(module):
    for name, arg_extractor in _elasticsearch_client_cluster_methods:
        wrap_elasticsearch_client_method(module.ClusterClient, name,
                arg_extractor, 'cluster')

_elasticsearch_client_nodes_methods = (
    ('hot_threads', None),
    ('info', None),
    ('shutdown', None),
    ('stats', None),
)

def instrument_elasticsearch_client_nodes(module):
    for name, arg_extractor in _elasticsearch_client_nodes_methods:
        wrap_elasticsearch_client_method(module.NodesClient, name,
                arg_extractor, 'nodes')

_elasticsearch_client_snapshot_methods = (
    ('create', None),
    ('create_repository', None),
    ('delete', None),
    ('delete_repository', None),
    ('get', None),
    ('get_repository', None),
    ('restore', None),
    ('status', None),
    ('verify_repository', None),
)

def instrument_elasticsearch_client_snapshot(module):
    for name, arg_extractor in _elasticsearch_client_snapshot_methods:
        wrap_elasticsearch_client_method(module.SnapshotClient, name,
                arg_extractor, 'snapshot')

_elasticsearch_client_tasks_methods = (
    ('list', None),
    ('cancel', None),
    ('get', None),
)

def instrument_elasticsearch_client_tasks(module):
    for name, arg_extractor in _elasticsearch_client_tasks_methods:
        wrap_elasticsearch_client_method(module.TasksClient, name,
                arg_extractor, 'tasks')

_elasticsearch_client_ingest_methods = (
    ('get_pipeline', None),
    ('put_pipeline', None),
    ('delete_pipeline', None),
    ('simulate', None),
)

def instrument_elasticsearch_client_ingest(module):
    for name, arg_extractor in _elasticsearch_client_ingest_methods:
        wrap_elasticsearch_client_method(module.IngestClient, name,
                arg_extractor, 'ingest')

#
# Instrumentation to get Datastore Instance Information
#

def _nr_Connection__init__wrapper(wrapped, instance, args, kwargs):
    """Cache datastore instance info on Connection object"""

    def _bind_params(host='localhost', port=9200, *args, **kwargs):
        return host, port

    host, port = _bind_params(*args, **kwargs)
    port = str(port)
    instance._nr_host_port = (host, port)

    return wrapped(*args, **kwargs)

def instrument_elasticsearch_connection_base(module):
    wrap_function_wrapper(module.Connection, '__init__',
            _nr_Connection__init__wrapper)

def _nr_get_connection_wrapper(wrapped, instance, args, kwargs):
    """Read instance info from Connection and stash on Transaction."""

    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    conn = wrapped(*args, **kwargs)

    instance_info = (None, None, None)
    try:
        tracer_settings = transaction.settings.datastore_tracer

        if tracer_settings.instance_reporting.enabled:
            host, port_path_or_id = conn._nr_host_port
            instance_info = (host, port_path_or_id, None)
    except:
        instance_info = ('unknown', 'unknown', None)

    transaction._nr_datastore_instance_info = instance_info

    return conn

def instrument_elasticsearch_transport(module):
    wrap_function_wrapper(module.Transport, 'get_connection',
            _nr_get_connection_wrapper)

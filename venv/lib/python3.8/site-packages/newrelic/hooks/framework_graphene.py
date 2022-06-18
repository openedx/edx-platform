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

from newrelic.common.object_wrapper import wrap_function_wrapper


def framework_details():
    import graphene

    return ("Graphene", getattr(graphene, "__version__", None))


def wrap_schema_init(wrapped, instance, args, kwargs):
    result = wrapped(*args, **kwargs)
    if hasattr(instance, "graphql_schema"):
        instance.graphql_schema._nr_framework = framework_details()
    else:
        instance._nr_framework = framework_details()

    return result  # Should never actually be defined


def instrument_graphene_types_schema(module):
    if hasattr(module, "Schema"):
        wrap_function_wrapper(module, "Schema.__init__", wrap_schema_init)

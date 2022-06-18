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

"""GraphQL utilities that wrap SQL utilities for reuse."""

import weakref

from newrelic.core.database_utils import SQLStatement


class GraphQLStyle(object):
    """Helper class to initialize SQLStatement instances."""

    quoting_style = "single+double"


class GraphQLStatement(SQLStatement):
    """Wrap SQLStatements to allow usage with GraphQL."""

    def __init__(self, graphql):
        super(GraphQLStatement, self).__init__(graphql, GraphQLStyle())
        # Preset unapplicable fields to empty
        self._operation = ""
        self._target = ""


_graphql_statements = weakref.WeakValueDictionary()


def graphql_statement(graphql):
    result = _graphql_statements.get(graphql, None)

    if result is not None:
        return result

    result = GraphQLStatement(graphql)

    _graphql_statements[graphql] = result

    return result

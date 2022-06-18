# Copyright 2009-present MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Python driver for MongoDB."""

ASCENDING = 1
"""Ascending sort order."""
DESCENDING = -1
"""Descending sort order."""

GEO2D = "2d"
"""Index specifier for a 2-dimensional `geospatial index`_.

.. _geospatial index: http://docs.mongodb.org/manual/core/2d/
"""

GEOHAYSTACK = "geoHaystack"
"""**DEPRECATED** - Index specifier for a 2-dimensional `haystack index`_.

**DEPRECATED** - :attr:`GEOHAYSTACK` is deprecated and will be removed in
PyMongo 4.0. geoHaystack indexes (and the geoSearch command) were deprecated
in MongoDB 4.4. Instead, create a 2d index and use $geoNear or $geoWithin.
See https://dochub.mongodb.org/core/4.4-deprecate-geoHaystack.

.. versionchanged:: 3.11
   Deprecated.

.. _haystack index: http://docs.mongodb.org/manual/core/geohaystack/
"""

GEOSPHERE = "2dsphere"
"""Index specifier for a `spherical geospatial index`_.

.. versionadded:: 2.5

.. _spherical geospatial index: http://docs.mongodb.org/manual/core/2dsphere/
"""

HASHED = "hashed"
"""Index specifier for a `hashed index`_.

.. versionadded:: 2.5

.. _hashed index: http://docs.mongodb.org/manual/core/index-hashed/
"""

TEXT = "text"
"""Index specifier for a `text index`_.

.. seealso:: MongoDB's `Atlas Search
   <https://docs.atlas.mongodb.com/atlas-search/>`_ which offers more advanced
   text search functionality.

.. versionadded:: 2.7.1

.. _text index: http://docs.mongodb.org/manual/core/index-text/
"""

OFF = 0
"""**DEPRECATED** - No database profiling.

**DEPRECATED** - :attr:`OFF` is deprecated and will be removed in PyMongo 4.0.
Instead, specify this profiling level using the numeric value ``0``.
See https://docs.mongodb.com/manual/tutorial/manage-the-database-profiler

.. versionchanged:: 3.12
   Deprecated
"""
SLOW_ONLY = 1
"""**DEPRECATED** - Only profile slow operations.

**DEPRECATED** - :attr:`SLOW_ONLY` is deprecated and will be removed in
PyMongo 4.0. Instead, specify this profiling level using the numeric
value ``1``.
See https://docs.mongodb.com/manual/tutorial/manage-the-database-profiler

.. versionchanged:: 3.12
   Deprecated
"""
ALL = 2
"""**DEPRECATED** - Profile all operations.

**DEPRECATED** - :attr:`ALL` is deprecated and will be removed in PyMongo 4.0.
Instead, specify this profiling level using the numeric value ``2``.
See https://docs.mongodb.com/manual/tutorial/manage-the-database-profiler

.. versionchanged:: 3.12
   Deprecated
"""

version_tuple = (3, 12, 3)

def get_version_string():
    if isinstance(version_tuple[-1], str):
        return '.'.join(map(str, version_tuple[:-1])) + version_tuple[-1]
    return '.'.join(map(str, version_tuple))

__version__ = version = get_version_string()
"""Current version of PyMongo."""

from pymongo.collection import ReturnDocument
from pymongo.common import (MIN_SUPPORTED_WIRE_VERSION,
                            MAX_SUPPORTED_WIRE_VERSION)
from pymongo.cursor import CursorType
from pymongo.mongo_client import MongoClient
from pymongo.mongo_replica_set_client import MongoReplicaSetClient
from pymongo.operations import (IndexModel,
                                InsertOne,
                                DeleteOne,
                                DeleteMany,
                                UpdateOne,
                                UpdateMany,
                                ReplaceOne)
from pymongo.read_preferences import ReadPreference
from pymongo.write_concern import WriteConcern

def has_c():
    """Is the C extension installed?"""
    try:
        from pymongo import _cmessage
        return True
    except ImportError:
        return False

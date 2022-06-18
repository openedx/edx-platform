# Copyright 2014-present MongoDB, Inc.
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

"""**DEPRECATED** Parse a response to the 'ismaster' command.

.. versionchanged:: 3.12
  This module is deprecated and will be removed in PyMongo 4.0.
"""

from pymongo.hello import *

class IsMaster(Hello):
    """**DEPRECATED** A hello response from the server.

    .. versionchanged:: 3.12
       Deprecated. Use :class:`~pymongo.hello.Hello` instead to parse
       server hello responses.
    """
    pass

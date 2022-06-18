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

import newrelic.core.config

settings = newrelic.core.config.global_settings

RECORDSQL_OFF = 'off'
RECORDSQL_RAW = 'raw'
RECORDSQL_OBFUSCATED = 'obfuscated'

COMPRESSED_CONTENT_ENCODING_DEFLATE = 'deflate'
COMPRESSED_CONTENT_ENCODING_GZIP = 'gzip'

STRIP_EXCEPTION_MESSAGE = ("Message removed by New Relic "
        "'strip_exception_messages' setting")

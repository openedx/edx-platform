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

class StringTable(object):

    def __init__(self):
        self.__values = []
        self.__mapping = {}

    def cache(self, value):
        if not value in self.__mapping:
            token = '`%d' % len(self.__values)
            self.__mapping[value] = token
            self.__values.append(value)
        return self.__mapping[value]

    def values(self):
        return self.__values

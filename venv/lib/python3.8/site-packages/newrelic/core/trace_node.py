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

from collections import namedtuple

RootNode = namedtuple('RootNode',
        ['start_time', 'empty0', 'empty1', 'root', 'attributes'])

def root_start_time(root):
    return root.start_time * 1000.0

TraceNode = namedtuple('TraceNode',
        ['start_time', 'end_time', 'name', 'params', 'children', 'label'])

def node_start_time(root, node):
    return (node.start_time - root.start_time) * 1000.0

def node_end_time(root, node):
    return (node.end_time - root.start_time) * 1000.0

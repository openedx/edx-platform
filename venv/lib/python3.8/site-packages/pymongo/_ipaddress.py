# Copyright 2021-present MongoDB, Inc.
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

"""Test if a string is an IP Address"""

import socket

from bson.py3compat import _unicode

try:
    from ipaddress import ip_address
    def is_ip_address(address):
        try:
            ip_address(_unicode(address))
            return True
        except (ValueError, UnicodeError):
            return False
except ImportError:
    if hasattr(socket, 'inet_pton') and socket.has_ipv6:
        # Most *nix, Windows newer than XP
        def is_ip_address(address):
            try:
                # inet_pton rejects IPv4 literals with leading zeros
                # (e.g. 192.168.0.01), inet_aton does not, and we
                # can connect to them without issue. Use inet_aton.
                socket.inet_aton(address)
                return True
            except socket.error:
                try:
                    socket.inet_pton(socket.AF_INET6, address)
                    return True
                except socket.error:
                    return False
    else:
        # No inet_pton
        def is_ip_address(address):
            try:
                socket.inet_aton(address)
                return True
            except socket.error:
                if ':' in address:
                    # ':' is not a valid character for a hostname.
                    return True
                return False


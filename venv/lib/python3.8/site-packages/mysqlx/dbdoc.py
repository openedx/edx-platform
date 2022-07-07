# Copyright (c) 2016, 2021, Oracle and/or its affiliates. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License, version 2.0, as
# published by the Free Software Foundation.
#
# This program is also distributed with certain software (including
# but not limited to OpenSSL) that is licensed under separate terms,
# as designated in a particular file or component or in included license
# documentation.  The authors of MySQL hereby grant you an
# additional permission to link the program and your derivative works
# with the separately licensed software that they have included with
# MySQL.
#
# Without limiting anything contained in the foregoing, this file,
# which is part of MySQL Connector/Python, is also subject to the
# Universal FOSS Exception, version 1.0, a copy of which can be found at
# http://oss.oracle.com/licenses/universal-foss-exception.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License, version 2.0, for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA

"""Implementation of the DbDoc."""

import json

from .errors import ProgrammingError


class ExprJSONEncoder(json.JSONEncoder):
    """A :class:`json.JSONEncoder` subclass, which enables encoding of
    :class:`mysqlx.ExprParser` objects."""
    def default(self, o):  # pylint: disable=E0202
        if hasattr(o, "expr"):
            return "{0}".format(o)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, o)


class DbDoc(object):
    """Represents a generic document in JSON format.

    Args:
        value (object): The value can be a JSON string or a dict.

    Raises:
        ValueError: If ``value`` type is not a basestring or dict.
    """
    def __init__(self, value):
        if isinstance(value, dict):
            self.__dict__ = value
        elif isinstance(value, str):
            self.__dict__ = json.loads(value)
        else:
            raise ValueError("Unable to handle type: {0}".format(type(value)))

    def __str__(self):
        return self.as_str()

    def __repr__(self):
        return repr(self.__dict__)

    def __setitem__(self, index, value):
        if index == "_id":
            raise ProgrammingError("Cannot modify _id")
        self.__dict__[index] = value

    def __getitem__(self, index):
        return self.__dict__[index]

    def __contains__(self, item):
        return item in self.__dict__

    def copy(self, doc_id=None):
        """Returns a new copy of a :class:`mysqlx.DbDoc` object containing the
        `doc_id` provided. If `doc_id` is not provided, it will be removed from
        new :class:`mysqlx.DbDoc` object.

        Args:
            doc_id (Optional[str]): Document ID

        Returns:
            mysqlx.DbDoc: A new instance of DbDoc containing the _id provided
        """
        new_dict = self.__dict__.copy()
        if doc_id:
            new_dict["_id"] = doc_id
        elif "_id" in new_dict:
            del new_dict["_id"]
        return DbDoc(new_dict)

    def keys(self):
        """Returns the keys.

        Returns:
            `list`: The keys.
        """
        return self.__dict__.keys()

    def as_str(self):
        """Serialize :class:`mysqlx.DbDoc` to a JSON formatted ``str``.

        Returns:
            str: A JSON formatted ``str`` representation of the document.

        .. versionadded:: 8.0.16
        """
        return json.dumps(self.__dict__, cls=ExprJSONEncoder)

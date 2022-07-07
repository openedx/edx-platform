# Copyright (c) 2020, Oracle and/or its affiliates.
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

import subprocess

from django.db.backends.base.client import BaseDatabaseClient


class DatabaseClient(BaseDatabaseClient):
    executable_name = 'mysql'

    @classmethod
    def settings_to_cmd_args(cls, settings_dict):
        args = [cls.executable_name]

        db = settings_dict['OPTIONS'].get('database', settings_dict['NAME'])
        user = settings_dict['OPTIONS'].get('user',
                                            settings_dict['USER'])
        passwd = settings_dict['OPTIONS'].get('password',
                                              settings_dict['PASSWORD'])
        host = settings_dict['OPTIONS'].get('host', settings_dict['HOST'])
        port = settings_dict['OPTIONS'].get('port', settings_dict['PORT'])
        defaults_file = settings_dict['OPTIONS'].get('read_default_file')

        # --defaults-file should always be the first option
        if defaults_file:
            args.append('--defaults-file={0}'.format(defaults_file))

        # We force SQL_MODE to TRADITIONAL
        args.append('--init-command=SET @@session.SQL_MODE=TRADITIONAL')

        if user:
            args.append('--user={0}'.format(user))
        if passwd:
            args.append('--password={0}'.format(passwd))

        if host:
            if '/' in host:
                args.append('--socket={0}'.format(host))
            else:
                args.append('--host={0}'.format(host))

        if port:
            args.append('--port={0}'.format(port))

        if db:
            args.append('--database={0}'.format(db))

        return args

    def runshell(self):
        args = DatabaseClient.settings_to_cmd_args(
            self.connection.settings_dict)
        subprocess.call(args)

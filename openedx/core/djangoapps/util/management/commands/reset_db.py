# -*- coding: utf-8 -*-
"""
reset_db
========

Django command to drop and recreate a database.
Useful when running tests against a database which may previously have
had different migrations applied to it.

This handles the one specific use case of the "reset_db" command from
django-extensions that we were actually using.

originally from http://www.djangosnippets.org/snippets/828/ by dnordberg
"""


import logging

import django
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from six.moves import configparser


class Command(BaseCommand):
    help = "Resets the database for this project."

    def add_arguments(self, parser):
        parser.add_argument(
            '-R', '--router', action='store', dest='router', default='default',
            help='Use this router-database other than defined in settings.py')

    def handle(self, *args, **options):
        """
        Resets the database for this project.

        Note: Transaction wrappers are in reverse as a work around for
        autocommit, anybody know how to do this the right way?
        """
        router = options.get('router')
        dbinfo = settings.DATABASES.get(router)
        if dbinfo is None:
            raise CommandError(u"Unknown database router %s" % router)

        engine = dbinfo.get('ENGINE').split('.')[-1]

        user = password = database_name = database_host = database_port = ''
        if engine == 'mysql':
            (user, password, database_name, database_host, database_port) = parse_mysql_cnf(dbinfo)

        user = dbinfo.get('USER') or user
        password = dbinfo.get('PASSWORD') or password
        owner = user

        database_name = dbinfo.get('NAME') or database_name
        if database_name == '':
            raise CommandError("You need to specify DATABASE_NAME in your Django settings file.")

        database_host = dbinfo.get('HOST') or database_host
        database_port = dbinfo.get('PORT') or database_port

        verbosity = int(options.get('verbosity', 1))

        if engine in ('sqlite3', 'spatialite'):
            import os
            try:
                logging.info(u"Unlinking %s database", engine)
                os.unlink(database_name)
            except OSError:
                pass

        elif engine in ('mysql',):
            import MySQLdb as Database
            kwargs = {
                'user': user,
                'passwd': password,
            }
            if database_host.startswith('/'):
                kwargs['unix_socket'] = database_host
            else:
                kwargs['host'] = database_host

            if database_port:
                kwargs['port'] = int(database_port)

            connection = Database.connect(**kwargs)
            drop_query = u'DROP DATABASE IF EXISTS `%s`' % database_name
            utf8_support = 'CHARACTER SET utf8'
            create_query = u'CREATE DATABASE `%s` %s' % (database_name, utf8_support)
            logging.info('Executing... "' + drop_query + '"')
            connection.query(drop_query)
            logging.info('Executing... "' + create_query + '"')
            connection.query(create_query)

        elif engine in ('postgresql', 'postgresql_psycopg2', 'postgis'):
            if engine == 'postgresql' and django.VERSION < (1, 9):
                import psycopg as Database  # NOQA
            elif engine in ('postgresql', 'postgresql_psycopg2', 'postgis'):
                import psycopg2 as Database  # NOQA

            conn_params = {'database': 'template1'}
            if user:
                conn_params['user'] = user
            if password:
                conn_params['password'] = password
            if database_host:
                conn_params['host'] = database_host
            if database_port:
                conn_params['port'] = database_port

            connection = Database.connect(**conn_params)
            connection.set_isolation_level(0)  # autocommit false
            cursor = connection.cursor()

            drop_query = u"DROP DATABASE \"%s\";" % database_name
            logging.info('Executing... "' + drop_query + '"')
            try:
                cursor.execute(drop_query)
            except Database.ProgrammingError as e:
                logging.exception(u"Error: %s", e)

            create_query = u"CREATE DATABASE \"%s\"" % database_name
            if owner:
                create_query += u" WITH OWNER = \"%s\" " % owner
            create_query += u" ENCODING = 'UTF8'"

            if engine == 'postgis' and django.VERSION < (1, 9):
                # For PostGIS 1.5, fetch template name if it exists
                from django.contrib.gis.db.backends.postgis.base import DatabaseWrapper
                postgis_template = DatabaseWrapper(dbinfo).template_postgis
                if postgis_template is not None:
                    create_query += u' TEMPLATE = %s' % postgis_template

            if settings.DEFAULT_TABLESPACE:
                create_query += u' TABLESPACE = %s;' % settings.DEFAULT_TABLESPACE
            else:
                create_query += u';'

            logging.info('Executing... "' + create_query + '"')
            cursor.execute(create_query)

        else:
            raise CommandError(u"Unknown database engine %s" % engine)

        if verbosity >= 2:
            print("Reset successful.")


def parse_mysql_cnf(dbinfo):
    """
    Attempt to parse mysql database config file for connection settings.
    Ideally we would hook into django's code to do this, but read_default_file is handled by the mysql C libs
    so we have to emulate the behaviour

    Settings that are missing will return ''
    returns (user, password, database_name, database_host, database_port)
    """
    read_default_file = dbinfo.get('OPTIONS', {}).get('read_default_file')
    if read_default_file:
        config = configparser.RawConfigParser({
            'user': '',
            'password': '',
            'database': '',
            'host': '',
            'port': '',
            'socket': '',
        })
        import os
        config.read(os.path.expanduser(read_default_file))
        try:
            user = config.get('client', 'user')
            password = config.get('client', 'password')
            database_name = config.get('client', 'database')
            database_host = config.get('client', 'host')
            database_port = config.get('client', 'port')
            socket = config.get('client', 'socket')

            if database_host == 'localhost' and socket:
                # mysql actually uses a socket if host is localhost
                database_host = socket

            return user, password, database_name, database_host, database_port

        except configparser.NoSectionError:
            pass

    return '', '', '', '', ''

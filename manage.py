#!/usr/bin/env python
"""
Usage: manage.py {lms|cms} [--settings env] ...

Run django management commands. Because edx-platform contains multiple django projects,
the first argument specifies which project to run (cms [Studio] or lms [Learning Management System]).

By default, those systems run in with a settings file appropriate for development. However,
by passing the --settings flag, you can specify what environment specific settings file to use.

Any arguments not understood by this manage.py will be passed to django-admin.py
"""

import os
import sys
import importlib
from argparse import ArgumentParser

def parse_args():
    """Parse edx specific arguments to manage.py"""
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(title='system', description='edX service to run')

    lms = subparsers.add_parser(
        'lms',
        help='Learning Management System',
        add_help=False,
        usage='%(prog)s [options] ...'
    )
    lms.add_argument('-h', '--help', action='store_true', help='show this help message and exit')
    lms.add_argument(
        '--settings',
        help="Which django settings module to use under lms.envs. If not provided, the DJANGO_SETTINGS_MODULE "
             "environment variable will be used if it is set, otherwise it will default to lms.envs.dev")
    lms.add_argument(
        '--service-variant',
        choices=['lms', 'lms-xml', 'lms-preview'],
        default='lms',
        help='Which service variant to run, when using the aws environment')
    lms.set_defaults(
        help_string=lms.format_help(),
        settings_base='lms/envs',
        default_settings='lms.envs.dev',
        startup='lms.startup',
    )

    cms = subparsers.add_parser(
        'cms',
        help='Studio',
        add_help=False,
        usage='%(prog)s [options] ...'
    )
    cms.add_argument(
        '--settings',
        help="Which django settings module to use under cms.envs. If not provided, the DJANGO_SETTINGS_MODULE "
             "environment variable will be used if it is set, otherwise it will default to cms.envs.dev")
    cms.add_argument('-h', '--help', action='store_true', help='show this help message and exit')
    cms.set_defaults(
        help_string=cms.format_help(),
        settings_base='cms/envs',
        default_settings='cms.envs.dev',
        service_variant='cms',
        startup='cms.startup',
    )

    edx_args, django_args = parser.parse_known_args()

    if edx_args.help:
        print "edX:"
        print edx_args.help_string

    return edx_args, django_args


if __name__ == "__main__":
    edx_args, django_args = parse_args()

    if edx_args.settings:
        os.environ["DJANGO_SETTINGS_MODULE"] = edx_args.settings_base.replace('/', '.') + "." + edx_args.settings
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", edx_args.default_settings)

    os.environ.setdefault("SERVICE_VARIANT", edx_args.service_variant)

    if edx_args.help:
        print "Django:"
        # This will trigger django-admin.py to print out its help
        django_args.append('--help')

    startup = importlib.import_module(edx_args.startup)
    startup.run()

    from django.core.management import execute_from_command_line

    execute_from_command_line([sys.argv[0]] + django_args)

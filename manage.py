#!/usr/bin/env python
"""
Django administration utility.

Standard idiomatic Django usage:

    DJANGO_SETTINGS_MODULE=lms.envs.production ./manage.py COMMAND ARGS...
    DJANGO_SETTINGS_MODULE=cms.envs.production ./manage.py COMMAND ARGS...

Legacy usage:

    ./manage.py lms [--settings=production] COMMAND ARGS...
    ./manage.py cms [--settings=production] COMMAND ARGS...
"""
# pylint: disable=wrong-import-order, wrong-import-position

from openedx.core.lib.logsettings import log_python_warnings
log_python_warnings()

# Patch the xml libs before anything else.
from openedx.core.lib.safe_lxml import defuse_xml_libs  # isort:skip
defuse_xml_libs()

import os
import sys
from argparse import ArgumentParser


def main():
    """
    Call the management command.

    Convert from legacy style into standard idiomatic django style if necessary.
    """

    env_settings_module = os.environ.get("DJANGO_SETTINGS_MODULE")

    # Final args and settings: We'll determine these based on whether we're using legacy usage or the new usage...
    final_settings_module: str
    final_args: list[str]

    if len(sys.argv) > 1 and sys.argv[1] in ["lms", "cms"]:
        # LEGACY USAGE:
        # The first arg after 'manage.py' is the service_variant, either 'lms' or 'cms'.
        # Additionally, the '--settings' flag may be provided, which points to module within {service_variant}.envs.
        # We remove both service_variant and --settings, but use them to determine a DJANGO_SETTINGS_MODULE.
        # For example:
        #    ./manage.py cms migrate --foo bar --settings blah --baz quux
        # Gets converted to:
        #    DJANGO_SETTINGS_MODULE=cms.envs.blah ./manage.py migrate --foo bar --baz quux
        manage_py = sys.argv[0]  # ./manage.py, manage.py, or path/to/manage.py
        service_variant = sys.argv[1]  # lms or cms
        settings_and_management_args = sys.argv[2:]  # everything else

        # Parse --settings, if it's there.
        parse_settings_module = ArgumentParser()
        parse_settings_module.add_argument(
            '--settings',
            help=(
                f"Which django settings module to use under {service_variant}.envs. "
                f"If unspecified, will default to {service_variant}.envs.devstack."
            ),
        )
        settings_arg, management_args = parse_settings_module.parse_known_args(settings_and_management_args)

        # Compute final args and settings.
        # Order of precedence: --settings, $DJANGO_SETTINGS_MODULE, $EDX_PLATFORM_SETTINGS, devstack
        final_settings_module = (
            f"{service_variant}.envs.{settings_arg.settings}"
            if settings_arg.settings
            else (
                f"{service_variant}.envs.{env_settings_name}"
                if (env_settings_name := os.environ.get("EDX_PLATFORM_SETTINGS")) and not env_settings_module
                else (
                    env_settings_module
                    if env_settings_module
                    else f"{service_variant}.envs.devstack"
                )
            )
        )
        final_args = [manage_py, *management_args]

    else:
        # STANDARD IDIOMATIC DJANGO USAGE (new):
        # The first arg after 'manage.py' is a management command... anything other than 'lms' or 'cms'.
        # The '--settings' flag is not accepted.
        # Instead, operators can use the DJANGO_SETTINGS_MODULE variable, which default to LMS devstack settings.
        # For example:
        #    DJANGO_SETTINGS_MODULE=cms.envs.blah ./manage.py migrate --foo bar --baz quux
        final_settings_module = env_settings_module or "lms.envs.devstack"
        final_args = sys.argv

    # The rest of this is just standard Django boilerplate.
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other exceptions.
        try:
            import django  # pylint: disable=unused-import, wrong-import-position
        except ImportError as import_error:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            ) from import_error
        raise

    print(
        f"{final_args[0]}: Effective DJANGO_SETTINGS_MODULE == \"{final_settings_module}\"",
        file=sys.stderr
    )
    os.environ["DJANGO_SETTINGS_MODULE"] = final_settings_module
    execute_from_command_line(final_args)


if __name__ == "__main__":
    main()

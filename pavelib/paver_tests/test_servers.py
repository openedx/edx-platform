"""Unit tests for the Paver server tasks."""

import ddt
import os
from paver.easy import call_task

from .utils import PaverTestCase

EXPECTED_COFFEE_COMMAND = (
    "node_modules/.bin/coffee --compile `find {platform_root}/lms "
    "{platform_root}/cms {platform_root}/common -type f -name \"*.coffee\"`"
)
EXPECTED_SASS_COMMAND = (
    "sass --update --cache-location /tmp/sass-cache --default-encoding utf-8 --style compressed"
    " --quiet --load-path common/static --load-path common/static/sass"
    " --load-path lms/static/sass --load-path lms/static/certificates/sass"
    " --load-path cms/static/sass --load-path common/static/sass"
    " lms/static/sass:lms/static/css lms/static/certificates/sass:lms/static/certificates/css"
    " cms/static/sass:cms/static/css common/static/sass:common/static/css"
)
EXPECTED_PREPROCESS_ASSETS_COMMAND = (
    "python manage.py {system} --settings={asset_settings} preprocess_assets"
)
EXPECTED_COLLECT_STATIC_COMMAND = (
    "python manage.py {system} --settings={asset_settings} collectstatic --noinput > /dev/null"
)
EXPECTED_CELERY_COMMAND = (
    "python manage.py lms --settings={settings} celery worker --beat --loglevel=INFO --pythonpath=."
)
EXPECTED_RUN_SERVER_COMMAND = (
    "python manage.py {system} --settings={settings} runserver --traceback --pythonpath=. 0.0.0.0:{port}"
)


@ddt.ddt
class TestPaverServerTasks(PaverTestCase):
    """
    Test the Paver server tasks.
    """
    @ddt.data(
        [{}],
        [{"settings": "aws"}],
        [{"asset-settings": "test_static_optimized"}],
        [{"settings": "devstack_optimized", "asset-settings": "test_static_optimized"}],
        [{"fast": True}],
        [{"port": 8030}],
    )
    @ddt.unpack
    def test_lms(self, options):
        """
        Test the "devstack" task.
        """
        self.verify_server_task("lms", options)

    @ddt.data(
        [{}],
        [{"settings": "aws"}],
        [{"asset-settings": "test_static_optimized"}],
        [{"settings": "devstack_optimized", "asset-settings": "test_static_optimized"}],
        [{"fast": True}],
        [{"port": 8031}],
    )
    @ddt.unpack
    def test_studio(self, options):
        """
        Test the "devstack" task.
        """
        self.verify_server_task("studio", options)

    @ddt.data(
        [{}],
        [{"settings": "aws"}],
        [{"asset-settings": "test_static_optimized"}],
        [{"settings": "devstack_optimized", "asset-settings": "test_static_optimized"}],
        [{"fast": True}],
        [{"optimized": True}],
        [{"optimized": True, "fast": True}],
        [{"no-contracts": True}],
    )
    @ddt.unpack
    def test_devstack(self, server_options):
        """
        Test the "devstack" task.
        """
        options = server_options.copy()

        # First test with LMS
        options["system"] = "lms"
        self.verify_server_task("devstack", options, contracts_default=True)

        # Then test with Studio
        options["system"] = "cms"
        self.verify_server_task("devstack", options, contracts_default=True)

    @ddt.data(
        [{}],
        [{"settings": "aws"}],
        [{"asset_settings": "test_static_optimized"}],
        [{"settings": "devstack_optimized", "asset-settings": "test_static_optimized"}],
        [{"fast": True}],
        [{"optimized": True}],
        [{"optimized": True, "fast": True}],
    )
    @ddt.unpack
    def test_run_all_servers(self, options):
        """
        Test the "run_all_servers" task.
        """
        self.verify_run_all_servers_task(options)

    @ddt.data(
        [{}],
        [{"settings": "aws"}],
    )
    @ddt.unpack
    def test_celery(self, options):
        """
        Test the "celery" task.
        """
        settings = options.get("settings", "dev_with_worker")
        call_task("pavelib.servers.celery", options=options)
        self.assertEquals(self.task_messages, [EXPECTED_CELERY_COMMAND.format(settings=settings)])

    @ddt.data(
        [{}],
        [{"settings": "aws"}],
    )
    @ddt.unpack
    def test_update_db(self, options):
        """
        Test the "update_db" task.
        """
        settings = options.get("settings", "devstack")
        call_task("pavelib.servers.update_db", options=options)
        db_command = "python manage.py {server} --settings={settings} syncdb --migrate --traceback --pythonpath=."
        self.assertEquals(
            self.task_messages,
            [
                db_command.format(server="lms", settings=settings),
                db_command.format(server="cms", settings=settings),
            ]
        )

    @ddt.data(
        ["lms", {}],
        ["lms", {"settings": "aws"}],
        ["cms", {}],
        ["cms", {"settings": "aws"}],
    )
    @ddt.unpack
    def test_check_settings(self, system, options):
        """
        Test the "check_settings" task.
        """
        settings = options.get("settings", "devstack")
        call_task("pavelib.servers.check_settings", args=[system, settings])
        self.assertEquals(
            self.task_messages,
            [
                "echo 'import {system}.envs.{settings}' "
                "| python manage.py {system} --settings={settings} shell --plain --pythonpath=.".format(
                    system=system, settings=settings
                ),
            ]
        )

    def verify_server_task(self, task_name, options, contracts_default=False):
        """
        Verify the output of a server task.
        """
        settings = options.get("settings", None)
        asset_settings = options.get("asset-settings", None)
        is_optimized = options.get("optimized", False)
        is_fast = options.get("fast", False)
        no_contracts = options.get("no-contracts", not contracts_default)
        if task_name == "devstack":
            system = options.get("system")
        elif task_name == "studio":
            system = "cms"
        else:
            system = "lms"
        port = options.get("port", "8000" if system == "lms" else "8001")
        self.reset_task_messages()
        if task_name == "devstack":
            args = ["studio" if system == "cms" else system]
            if settings:
                args.append("--settings={settings}".format(settings=settings))
            if asset_settings:
                args.append("--asset-settings={asset_settings}".format(asset_settings=asset_settings))
            if is_optimized:
                args.append("--optimized")
            if is_fast:
                args.append("--fast")
            if no_contracts:
                args.append("--no-contracts")
            call_task("pavelib.servers.devstack", args=args)
        else:
            call_task("pavelib.servers.{task_name}".format(task_name=task_name), options=options)
        expected_messages = []
        expected_settings = settings if settings else "devstack"
        expected_asset_settings = asset_settings if asset_settings else expected_settings
        if is_optimized:
            expected_settings = "devstack_optimized"
            expected_asset_settings = "test_static_optimized"
        expected_collect_static = not is_fast and expected_settings != "devstack"
        platform_root = os.getcwd()
        if not is_fast:
            expected_messages.append(EXPECTED_PREPROCESS_ASSETS_COMMAND.format(
                system=system, asset_settings=expected_asset_settings
            ))
            expected_messages.append("xmodule_assets common/static/xmodule")
            expected_messages.append(EXPECTED_COFFEE_COMMAND.format(platform_root=platform_root))
            expected_messages.append(EXPECTED_SASS_COMMAND)
        if expected_collect_static:
            expected_messages.append(EXPECTED_COLLECT_STATIC_COMMAND.format(
                system=system, asset_settings=expected_asset_settings
            ))
        expected_run_server_command = EXPECTED_RUN_SERVER_COMMAND.format(
            system=system,
            settings=expected_settings,
            port=port,
        )
        if not no_contracts:
            expected_run_server_command += " --contracts"
        expected_messages.append(expected_run_server_command)
        self.assertEquals(self.task_messages, expected_messages)

    def verify_run_all_servers_task(self, options):
        """
        Verify the output of a server task.
        """
        settings = options.get("settings", None)
        asset_settings = options.get("asset_settings", None)
        is_optimized = options.get("optimized", False)
        is_fast = options.get("fast", False)
        self.reset_task_messages()
        call_task("pavelib.servers.run_all_servers", options=options)
        expected_settings = settings if settings else "devstack"
        expected_asset_settings = asset_settings if asset_settings else expected_settings
        if is_optimized:
            expected_settings = "devstack_optimized"
            expected_asset_settings = "test_static_optimized"
        expected_collect_static = not is_fast and expected_settings != "devstack"
        platform_root = os.getcwd()
        expected_messages = []
        if not is_fast:
            expected_messages.append(EXPECTED_PREPROCESS_ASSETS_COMMAND.format(
                system="lms", asset_settings=expected_asset_settings
            ))
            expected_messages.append(EXPECTED_PREPROCESS_ASSETS_COMMAND.format(
                system="cms", asset_settings=expected_asset_settings
            ))
            expected_messages.append("xmodule_assets common/static/xmodule")
            expected_messages.append(EXPECTED_COFFEE_COMMAND.format(platform_root=platform_root))
            expected_messages.append(EXPECTED_SASS_COMMAND)
        if expected_collect_static:
            expected_messages.append(EXPECTED_COLLECT_STATIC_COMMAND.format(
                system="lms", asset_settings=expected_asset_settings
            ))
            expected_messages.append(EXPECTED_COLLECT_STATIC_COMMAND.format(
                system="cms", asset_settings=expected_asset_settings
            ))
        expected_messages.append(
            EXPECTED_RUN_SERVER_COMMAND.format(
                system="lms",
                settings=expected_settings,
                port=8000,
            )
        )
        expected_messages.append(
            EXPECTED_RUN_SERVER_COMMAND.format(
                system="cms",
                settings=expected_settings,
                port=8001,
            )
        )
        expected_messages.append(EXPECTED_CELERY_COMMAND.format(settings="dev_with_worker"))
        self.assertEquals(self.task_messages, expected_messages)

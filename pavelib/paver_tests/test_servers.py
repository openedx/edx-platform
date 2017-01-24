"""Unit tests for the Paver server tasks."""

import ddt
from paver.easy import call_task

from .utils import PaverTestCase

EXPECTED_COFFEE_COMMAND = (
    u"node_modules/.bin/coffee --compile `find {platform_root}/lms "
    u"{platform_root}/cms {platform_root}/common -type f -name \"*.coffee\"`"
)
EXPECTED_SASS_COMMAND = (
    u"libsass {sass_directory}"
)
EXPECTED_COMMON_SASS_DIRECTORIES = [
    u"common/static/sass",
]
EXPECTED_LMS_SASS_DIRECTORIES = [
    u"lms/static/sass",
    u"lms/static/certificates/sass",
]
EXPECTED_CMS_SASS_DIRECTORIES = [
    u"cms/static/sass",
]
EXPECTED_LMS_SASS_COMMAND = [
    u"python manage.py lms --settings={asset_settings} compile_sass lms ",
]
EXPECTED_CMS_SASS_COMMAND = [
    u"python manage.py cms --settings={asset_settings} compile_sass cms ",
]
EXPECTED_COLLECT_STATIC_COMMAND = (
    u"python manage.py {system} --settings={asset_settings} collectstatic --noinput {log_string}"
)
EXPECTED_CELERY_COMMAND = (
    u"python manage.py lms --settings={settings} celery worker --beat --loglevel=INFO --pythonpath=."
)
EXPECTED_RUN_SERVER_COMMAND = (
    u"python manage.py {system} --settings={settings} runserver --traceback --pythonpath=. 0.0.0.0:{port}"
)
EXPECTED_INDEX_COURSE_COMMAND = (
    u"python manage.py {system} --settings={settings} reindex_course --setup"
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
        is_optimized = options.get("optimized", False)
        expected_settings = "devstack_optimized" if is_optimized else options.get("settings", "devstack")

        # First test with LMS
        options["system"] = "lms"
        options["expected_messages"] = [
            EXPECTED_INDEX_COURSE_COMMAND.format(
                system="cms",
                settings=expected_settings,
            )
        ]
        self.verify_server_task("devstack", options, contracts_default=True)

        # Then test with Studio
        options["system"] = "cms"
        options["expected_messages"] = [
            EXPECTED_INDEX_COURSE_COMMAND.format(
                system="cms",
                settings=expected_settings,
            )
        ]
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
        # pylint: disable=line-too-long
        db_command = "NO_EDXAPP_SUDO=1 EDX_PLATFORM_SETTINGS_OVERRIDE={settings} /edx/bin/edxapp-migrate-{server} --traceback --pythonpath=. "
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
        log_string = options.get("log_string", "> /dev/null")
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
        expected_messages = options.get("expected_messages", [])
        expected_settings = settings if settings else "devstack"
        expected_asset_settings = asset_settings if asset_settings else expected_settings
        if is_optimized:
            expected_settings = "devstack_optimized"
            expected_asset_settings = "test_static_optimized"
        expected_collect_static = not is_fast and expected_settings != "devstack"
        if not is_fast:
            expected_messages.append(u"xmodule_assets common/static/xmodule")
            expected_messages.append(u"install npm_assets")
            expected_messages.append(EXPECTED_COFFEE_COMMAND.format(platform_root=self.platform_root))
            expected_messages.extend(self.expected_sass_commands(system=system, asset_settings=expected_asset_settings))
        if expected_collect_static:
            expected_messages.append(EXPECTED_COLLECT_STATIC_COMMAND.format(
                system=system, asset_settings=expected_asset_settings, log_string=log_string
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
        log_string = options.get("log_string", "> /dev/null")
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
        expected_messages = []
        if not is_fast:
            expected_messages.append(u"xmodule_assets common/static/xmodule")
            expected_messages.append(u"install npm_assets")
            expected_messages.append(EXPECTED_COFFEE_COMMAND.format(platform_root=self.platform_root))
            expected_messages.extend(self.expected_sass_commands(asset_settings=expected_asset_settings))
        if expected_collect_static:
            expected_messages.append(EXPECTED_COLLECT_STATIC_COMMAND.format(
                system="lms", asset_settings=expected_asset_settings, log_string=log_string
            ))
            expected_messages.append(EXPECTED_COLLECT_STATIC_COMMAND.format(
                system="cms", asset_settings=expected_asset_settings, log_string=log_string
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

    def expected_sass_commands(self, system=None, asset_settings=u"test_static_optimized"):
        """
        Returns the expected SASS commands for the specified system.
        """
        expected_sass_commands = []
        if system != 'cms':
            expected_sass_commands.extend(EXPECTED_LMS_SASS_COMMAND)
        if system != 'lms':
            expected_sass_commands.extend(EXPECTED_CMS_SASS_COMMAND)
        return [command.format(asset_settings=asset_settings) for command in expected_sass_commands]

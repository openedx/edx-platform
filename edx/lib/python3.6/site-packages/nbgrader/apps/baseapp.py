#!/usr/bin/env python
# encoding: utf-8

from __future__ import print_function

import sys
import os
import traceback
import logging
import traitlets.log

from jupyter_core.application import JupyterApp
from textwrap import dedent
from tornado.log import LogFormatter
from traitlets import Unicode, List, Bool, Instance, default
from traitlets.config.application import catch_config_error
from traitlets.config.loader import Config

from ..coursedir import CourseDirectory


nbgrader_aliases = {
    'log-level' : 'Application.log_level',
    'student': 'CourseDirectory.student_id',
    'assignment': 'CourseDirectory.assignment_id',
    'notebook': 'CourseDirectory.notebook_id',
    'db': 'CourseDirectory.db_url',
    'course-dir': 'CourseDirectory.root'
}
nbgrader_flags = {
    'debug': (
        {'Application' : {'log_level' : 'DEBUG'}},
        "set log level to DEBUG (maximize logging output)"
    ),
    'quiet': (
        {'Application' : {'log_level' : 'CRITICAL'}},
        "set log level to CRITICAL (minimize logging output)"
    ),
}

def format_excepthook(etype, evalue, tb):
    traceback.print_exception(etype, evalue, tb)
    print(dedent(
        """
        If you suspect this is a nbgrader bug, please report it at:
            https://github.com/jupyter/nbgrader/issues
        """
    ), file=sys.stderr)


class NbGrader(JupyterApp):
    """A base class for all the nbgrader apps."""

    aliases = nbgrader_aliases
    flags = nbgrader_flags

    _log_formatter_cls = LogFormatter

    @default("log_level")
    def _log_level_default(self):
        return logging.INFO

    @default("log_datefmt")
    def _log_datefmt_default(self):
        return "%Y-%m-%d %H:%M:%S"

    @default("log_format")
    def _log_format_default(self):
        return "%(color)s[%(name)s | %(levelname)s]%(end_color)s %(message)s"

    logfile = Unicode(
        ".nbgrader.log",
        help=dedent(
            """
            Name of the logfile to log to.
            """
        )
    ).tag(config=True)

    def init_logging(self, handler_class, handler_args, color=True, subapps=False):
        handler = handler_class(*handler_args)

        if color:
            log_format = self.log_format
        else:
            log_format = self.log_format.replace("%(color)s", "").replace("%(end_color)s", "")

        _formatter = self._log_formatter_cls(
            fmt=log_format,
            datefmt=self.log_datefmt)
        handler.setFormatter(_formatter)

        self.log.addHandler(handler)

        if subapps and self.subapp:
            self.subapp.init_logging(handler_class, handler_args, color=color, subapps=subapps)

    def deinit_logging(self):
        if len(self.log.handlers) > 1:
            for handler in self.log.handlers[1:]:
                handler.close()
                self.log.removeHandler(handler)

    coursedir = Instance(CourseDirectory, allow_none=True)
    verbose_crash = Bool(False)

    # The classes added here determine how configuration will be documented
    classes = List()

    @default("classes")
    def _classes_default(self):
        return [NbGrader, CourseDirectory]

    @default("config_file_name")
    def _config_file_name_default(self):
        return u'nbgrader_config'

    def _load_config(self, cfg, **kwargs):
        if 'NbGraderConfig' in cfg:
            self.log.warning(
                "Use NbGrader in config, not NbGraderConfig. Outdated config:\n%s",
                '\n'.join(
                    'NbGraderConfig.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.NbGraderConfig.items()
                )
            )
            cfg.NbGrader.merge(cfg.NbGraderConfig)
            del cfg.NbGraderConfig

        if 'BasicConfig' in cfg:
            self.log.warning(
                "Use NbGrader in config, not BasicConfig. Outdated config:\n%s",
                '\n'.join(
                    'BasicConfig.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.BasicConfig.items()
                )
            )
            cfg.NbGrader.merge(cfg.BasicConfig)
            del cfg.BasicConfig

        if 'BaseNbGraderApp' in cfg:
            self.log.warning(
                "Use NbGrader in config, not BaseNbGraderApp. Outdated config:\n%s",
                '\n'.join(
                    'BaseNbGraderApp.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.BaseNbGraderApp.items()
                )
            )
            cfg.NbGrader.merge(cfg.BaseNbGraderApp)
            del cfg.BaseNbGraderApp

        if 'BaseApp' in cfg:
            self.log.warning(
                "Use NbGrader in config, not BaseApp. Outdated config:\n%s",
                '\n'.join(
                    'BaseApp.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.BaseApp.items()
                )
            )
            cfg.NbGrader.merge(cfg.BaseApp)
            del cfg.BaseApp

        coursedir_options = [
            ("student_id", "student_id"),
            ("assignment_id", "assignment_id"),
            ("notebook_id", "notebook_id"),
            ("directory_structure", "directory_structure"),
            ("source_directory", "source_directory"),
            ("release_directory", "release_directory"),
            ("submitted_directory", "submitted_directory"),
            ("autograded_directory", "autograded_directory"),
            ("feedback_directory", "feedback_directory"),
            ("db_url", "db_url"),
            ("db_assignments", "db_assignments"),
            ("db_students", "db_students"),
            ("course_directory", "root"),
            ("ignore", "ignore")
        ]

        for old_opt, new_opt in coursedir_options:
            if old_opt in cfg.NbGrader:
                self.log.warning("Outdated config: use CourseDirectory.{} rather than NbGrader.{}".format(new_opt, old_opt))
                setattr(cfg.CourseDirectory, new_opt, cfg.NbGrader[old_opt])
                delattr(cfg.NbGrader, old_opt)

        if "course_id" in cfg.NbGrader:
            self.log.warning("Outdated config: use Exchange.course_id rather than NbGrader.course_id")
            cfg.Exchange.course_id = cfg.NbGrader.course_id
            del cfg.NbGrader.course_id

        exchange_options = [
            ("timezone", "timezone"),
            ("timestamp_format", "timestamp_format"),
            ("exchange_directory", "root"),
            ("cache_directory", "cache")
        ]

        for old_opt, new_opt in exchange_options:
            if old_opt in cfg.TransferApp:
                self.log.warning("Outdated config: use Exchange.{} rather than TransferApp.{}".format(new_opt, old_opt))
                setattr(cfg.Exchange, new_opt, cfg.TransferApp[old_opt])
                delattr(cfg.TransferApp, old_opt)

        if 'TransferApp' in cfg and cfg.TransferApp:
            self.log.warning(
                "Use Exchange in config, not TransferApp. Outdated config:\n%s",
                '\n'.join(
                    'TransferApp.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.TransferApp.items()
                )
            )
            cfg.Exchange.merge(cfg.TransferApp)
            del cfg.TransferApp

        if 'BaseNbConvertApp' in cfg:
            self.log.warning(
                "Use BaseConverter in config, not BaseNbConvertApp. Outdated config:\n%s",
                '\n'.join(
                    'BaseNbConvertApp.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.BaseNbConvertApp.items()
                )
            )
            cfg.BaseConverter.merge(cfg.BaseNbConvertApp)
            del cfg.BaseNbConvertApp

        super(NbGrader, self)._load_config(cfg, **kwargs)
        if self.coursedir:
            self.coursedir._load_config(cfg)

    def fail(self, msg, *args):
        """Log the error msg using self.log.error and exit using sys.exit(1)."""
        self.log.error(msg, *args)
        sys.exit(1)

    def build_extra_config(self):
        return Config()

    def excepthook(self, etype, evalue, tb):
        format_excepthook(etype, evalue, tb)

    @catch_config_error
    def initialize(self, argv=None):
        self.update_config(self.build_extra_config())
        if self.logfile:
            self.init_logging(logging.FileHandler, [self.logfile], color=False)
        self.init_syspath()
        self.coursedir = CourseDirectory(parent=self)
        super(NbGrader, self).initialize(argv)

        # load config that is in the coursedir directory
        super(JupyterApp, self).load_config_file("nbgrader_config.py", path=self.coursedir.root)

    def init_syspath(self):
        """Add the cwd to the sys.path ($PYTHONPATH)"""
        sys.path.insert(0, os.getcwd())

    def reset(self):
        # stop logging
        self.deinit_logging()

        # recursively reset all subapps
        if self.subapp:
            self.subapp.reset()

        # clear the instance
        self.clear_instance()
        traitlets.log._logger = None

    def print_subcommands(self):
        for key, (app, desc) in self.subcommands.items():
            print("    {}\n{}\n".format(key, desc))

    def load_config_file(self, **kwargs):
        """Load the config file.
        By default, errors in loading config are handled, and a warning
        printed on screen. For testing, the suppress_errors option is set
        to False, so errors will make tests fail.
        """
        if self.config_file:
            paths = [os.path.abspath("{}.py".format(self.config_file))]
        else:
            paths = [os.path.join(x, "{}.py".format(self.config_file_name)) for x in self.config_file_paths]

        if not any(os.path.exists(x) for x in paths):
            self.log.warning("No nbgrader_config.py file found (rerun with --debug to see where nbgrader is looking)")

        super(NbGrader, self).load_config_file(**kwargs)

import os
import six
import sys
import shutil
import datetime

from dateutil.tz import gettz
from textwrap import dedent
from traitlets import Bool, Instance, Type, Unicode
from traitlets.config.application import catch_config_error, default

from .baseapp import NbGrader

from ..plugins import BasePlugin, ExtractorPlugin, FileNameCollectorPlugin
from ..utils import check_directory, rmtree, parse_utc
from ..utils import find_all_notebooks

aliases = {
    'log-level': 'Application.log_level',
    'extractor': 'ZipCollectApp.extractor_plugin',
    'collector': 'ZipCollectApp.collector_plugin',
    'zip_ext': 'ExtractorPlugin.zip_ext',
}
flags = {
    'debug': (
        {'Application': {'log_level': 'DEBUG'}},
        "set log level to DEBUG (maximize logging output)"
    ),
    'force': (
        {
            'ZipCollectApp': {'force': True},
            'ExtractorPlugin': {'force': True}
        },
        "Force overwrite of existing files."
    ),
    'strict': (
        {'ZipCollectApp': {'strict': True}},
        "Skip submitted notebooks with invalid names."
    ),
}


class ZipCollectApp(NbGrader):

    name = u'nbgrader-zip-collect'
    description = u'Collect assignments from archives (zip files).'

    aliases = aliases
    flags = flags

    examples = """
        Collect assignment submissions from files and/or archives (zip) files
        manually downloaded from a LMS. For the usage of instructors.

        This command is run from the top-level nbgrader folder. In order to
        facilitate the collect process, nbgrader places some constraints on how
        the manually downloaded archive (zip) files must be structured. By
        default, the directory structure must look like this:

            {downloaded}/{assignment_id}/{collect_step}

        where `downloaded` is the main directory, `assignment_id` is the name
        of the assignment and `collect_step` is the step in the collect
        process.

        Manually downloaded assignment submissions files and/or archives (zip)
        files must be placed in the `archive_directory`:

            {downloaded}/{assignment_id}/{archive_directory}

        It is expected that the instructor has already created this directory
        and placed the downloaded assignment submissions files and/or archives
        (zip) files in this directory.

        Archive (zip) files in the `archive_directory` will be extracted, and
        any non-archive files will be copied, to the `extracted_directory`:

            {downloaded}/{assignment_id}/{extracted_directory}

        After which the files in the `extracted_directory` will be collected
        and copied into the students `submitted_directory`:

            {submitted_directory}/{student_id}/{assignment_id}/{notebook_id}.ipynb

        By default the collection of files in the `extracted_directory` is
        managed via the :class:`~nbgrader.plugins.zipcollect.FileNameCollectorPlugin`
        plugin. Each filename is sent to the plugin, which in turn returns an
        object containing the `student_id`, `file_id`, `first_name`,
        `last_name`, `email`, and `timestamp` data. For more information run:

            nbgrader zip_collect --help-all

        To change the default plugin, you will need a class that inherits from
        :class:`~nbgrader.plugins.zipcollect.FileNameCollectorPlugin`. If your
        collector is named `MyCustomCollector` and is saved in the file
        `mycollector.py`, then:

            nbgrader zip_collect --collector=mycollector.MyCustomCollector

        """

    force = Bool(
        default_value=False,
        help="Force overwrite of existing files."
    ).tag(config=True)

    strict = Bool(
        default_value=False,
        help="Skip submitted notebooks with invalid names."
    ).tag(config=True)

    collect_directory_structure = Unicode(
        os.path.join(
            "{downloaded}", "{assignment_id}", "{collect_step}"),
        help=dedent(
            """
            Format string for the directory structure that nbgrader works over
            during the zip collect process. This MUST contain named keys for
            'downloaded', 'assignment_id', and 'collect_step'.
            """
        )
    ).tag(config=True)

    downloaded_directory = Unicode(
        'downloaded',
        help=dedent(
            """
            The main directory that corresponds to the `downloaded` variable in
            the `collect_structure` config option.
            """
        )
    ).tag(config=True)

    archive_directory = Unicode(
        'archive',
        help=dedent(
            """
            The name of the directory that contains assignment submission files
            and/or archives (zip) files manually downloaded from a LMS. This
            corresponds to the `collect_step` variable in the
            `collect_structure` config option.
            """
        )
    ).tag(config=True)

    extracted_directory = Unicode(
        'extracted',
        help=dedent(
            """
            The name of the directory that contains assignment submission files
            extracted or copied from the `archive_directory`. This corresponds
            to the `collect_step` variable in the `collect_structure` config
            option.
            """
        )
    ).tag(config=True)

    extractor_plugin = Type(
        ExtractorPlugin,
        klass=BasePlugin,
        help=dedent(
            """
            The plugin class for extracting the archive files in the
            `archive_directory`.
            """
        )
    ).tag(config=True)

    collector_plugin = Type(
        FileNameCollectorPlugin,
        klass=BasePlugin,
        help=dedent(
            """
            The plugin class for processing the submitted file names after
            they have been extracted into the `extracted_directory`.
            """
        )
    ).tag(config=True)

    collector_plugin_inst = Instance(FileNameCollectorPlugin).tag(config=False)
    extractor_plugin_inst = Instance(ExtractorPlugin).tag(config=False)

    @default("classes")
    def _classes_default(self):
        classes = super(ZipCollectApp, self)._classes_default()
        classes.append(ExtractorPlugin)
        classes.append(FileNameCollectorPlugin)
        classes.append(ZipCollectApp)
        return classes

    def _format_collect_path(self, collect_step):
        kwargs = dict(
            downloaded=self.downloaded_directory,
            assignment_id=self.coursedir.assignment_id,
            collect_step=collect_step,
        )

        path = os.path.join(
            self.coursedir.root,
            self.collect_directory_structure,
        ).format(**kwargs)

        return path

    def _mkdirs_if_missing(self, path):
        if not check_directory(path, write=True, execute=True):
            self.log.warning("Directory not found. Creating: {}".format(path))
            os.makedirs(path)

    def _clear_existing_files(self, path):
        if not os.listdir(path):
            return

        if self.force:
            self.log.warning("Clearing existing files in {}".format(path))
            rmtree(path)
            os.makedirs(path)
        else:
            self.fail(
                "Directory not empty: {}\nuse the --force option to clear "
                "previously existing files".format(path)
            )

    def extract_archive_files(self):
        """Extract archive (zip) files and submission files in the
        `archive_directory`. Files are extracted to the `extracted_directory`.
        Non-archive (zip) files found in the `archive_directory` are copied to
        the `extracted_directory`.
        """
        archive_path = self._format_collect_path(self.archive_directory)
        if not check_directory(archive_path, write=False, execute=True):
            self.log.warning("Directory not found: {}".format(archive_path))
            return

        extracted_path = self._format_collect_path(self.extracted_directory)
        self._mkdirs_if_missing(extracted_path)
        self._clear_existing_files(extracted_path)
        self.extractor_plugin_inst.extract(archive_path, extracted_path)

    def process_extracted_files(self):
        """Collect the files in the `extracted_directory` using a given plugin
        to process the filename of each file. Collected files are transfered to
        the students `submitted_directory`.
        """
        extracted_path = self._format_collect_path(self.extracted_directory)
        if not check_directory(extracted_path, write=False, execute=True):
            self.log.warning("Directory not found: {}".format(extracted_path))

        src_files = []
        for root, _, extracted_files in os.walk(extracted_path):
            for _file in extracted_files:
                src_files.append(os.path.join(root, _file))

        if not src_files:
            self.log.warning(
                "No files found in directory: {}".format(extracted_path))
            return

        src_files.sort()
        collected_data = self._collect_files(src_files)
        self._transfer_files(collected_data)

    def _collect_files(self, src_files):
        """Collect the files in the `extracted_directory` using a given plugin
        to process the filename of each file.

        Arguments
        ---------
        src_files: list
            List of all files in the `extracted_directory`

        Returns:
        --------
        Dict: Collected data object of the form
            {
                student_id: {
                    src_files: [src_file1, ...],
                    dest_files: [dest_file1, ...],
                    file_ids: [file_id1, ...],
                    timestamp: timestamp,
                }, ...
            }
        """
        self.log.info("Start collecting files...")
        released_path = self.coursedir.format_path(
            self.coursedir.release_directory, '.', self.coursedir.assignment_id)
        released_notebooks = find_all_notebooks(released_path)
        if not released_notebooks:
            self.log.warning(
                "No release notebooks found for assignment {}"
                "".format(self.coursedir.assignment_id)
            )

        data = dict()
        invalid_files = 0
        processed_files = 0
        for _file in src_files:
            self.log.info("Parsing file: {}".format(_file))
            info = self.collector_plugin_inst.collect(_file)
            if not info or info is None:
                self.log.warning(
                    "Skipped submission with no match information provided: {}".format(_file))
                invalid_files += 1
                continue

            for key in ['student_id', 'file_id']:
                if key not in info.keys():
                    self.fail(
                        "Expected collector {} to provide the {} from the "
                        "submission file name."
                        "".format(self.collector_plugin.__name__, key)
                    )
                if not isinstance(info[key], six.string_types):
                    self.fail(
                        "Expected collector {} to provide a string for {} from "
                        "the submission file name."
                        "".format(self.collector_plugin.__name__, key)
                    )

            _, ext = os.path.splitext(_file)
            submission = os.path.splitext(info['file_id'])[0] + ext
            if ext in ['.ipynb'] and submission not in released_notebooks:
                self.log.debug(
                    "Valid notebook names are: {}".format(released_notebooks))
                self.log.debug(
                    "Notebook name given was: {}".format(submission))
                if self.strict:
                    self.log.warning(
                        "Skipped notebook with invalid name '{}'".format(submission))
                    invalid_files += 1
                    continue
                self.log.warning(
                    "Invalid submission notebook name '{}'".format(submission))

            submitted_path = self.coursedir.format_path(
                self.coursedir.submitted_directory, info['student_id'], self.coursedir.assignment_id)
            dest_path = os.path.join(submitted_path, submission)

            timestamp = None
            if 'timestamp' in info.keys():
                timestamp = info['timestamp']

            if isinstance(timestamp, six.string_types):
                if not timestamp:
                    self.log.warning("Empty timestamp string provided.")
                    timestamp = None
                try:
                    timestamp = parse_utc(timestamp)
                except ValueError:
                    self.fail(
                        "Invalid timestamp string: {}".format(timestamp))

            student_id = info['student_id']

            # new student id record
            if student_id not in data.keys():
                data[student_id] = dict(
                    src_files=[_file],
                    dest_files=[dest_path],
                    file_ids=[submission],
                    timestamp=timestamp,
                )

            # existing student id record, new submission file
            elif submission not in data[student_id]['file_ids']:
                data[student_id]['src_files'].append(_file)
                data[student_id]['dest_files'].append(dest_path)
                data[student_id]['file_ids'].append(submission)
                # update timestamp with a newer one if given
                if timestamp is not None:
                    old_timestamp = data[student_id]['timestamp']
                    if old_timestamp is None:
                        data[student_id]['timestamp'] = timestamp
                    elif timestamp >= old_timestamp:
                        data[student_id]['timestamp'] = timestamp

            # existing student id record, duplicate submission file
            else:
                ind = data[student_id]['file_ids'].index(submission)
                old_timestamp = data[student_id]['timestamp']
                if timestamp is not None and old_timestamp is not None:
                    # keep if duplicate submission file has a newer timestamp
                    if timestamp >= old_timestamp:
                        data[student_id]['src_files'][ind] = _file
                        data[student_id]['dest_files'][ind] = dest_path
                        data[student_id]['file_ids'][ind] = submission
                        data[student_id]['timestamp'] = timestamp
                        self.log.warning(
                            "Replacing previously collected submission file "
                            "with one that has a newer timestamp"
                        )
                    else:
                        self.log.warning(
                            "Skipped submission file with older timestamp")
                    invalid_files += 1

                else:
                    # no way to compare so fail
                    self.fail(
                        "Duplicate submission file. No timestamps for comparison")

            processed_files += 1

        if invalid_files > 0:
            self.log.warning(
                "{} files collected, {} files skipped"
                "".format(processed_files, invalid_files)
            )
        else:
            self.log.info("{} files collected".format(processed_files))
        return data

    def _transfer_files(self, collected_data):
        """Transfer collected files to the students `submitted_directory`.

        Arguments
        ---------
        collect: dict
            Collect data object of the form
                {
                    student_id: {
                        src_files: [src_file1, ...],
                        dest_files: [dest_file1, ...],
                        file_ids: [file_id1, ...],
                        timestamp: timestamp,
                    }, ...
                }
        """
        if not collected_data:
            return

        self.log.info("Start transfering files...")
        for student_id, data in collected_data.items():
            dest_path = self.coursedir.format_path(
                self.coursedir.submitted_directory, student_id, self.coursedir.assignment_id)
            self._mkdirs_if_missing(dest_path)
            self._clear_existing_files(dest_path)

            for i in range(len(data['file_ids'])):
                src = data['src_files'][i]
                dest = data['dest_files'][i]
                self._mkdirs_if_missing(os.path.split(dest)[0])
                if os.path.exists(dest):
                    # should never get here, but just in case
                    self.fail(
                        "Trying to overwrite existing file: {}".format(dest))
                self.log.info('Copying from: {}'.format(src))
                self.log.info('  Copying to: {}'.format(dest))
                shutil.copy(src, dest)

            dest = os.path.join(dest_path, 'timestamp.txt')
            if os.path.exists(dest):
                self.log.info('Found collected timestamp file: {}'.format(dest))
            elif data['timestamp'] is not None:
                self.log.info('Creating timestamp: {}'.format(dest))
                with open(dest, 'w') as fh:
                    fh.write("{}".format(data['timestamp'].isoformat(' ')))

    def init_plugins(self):
        self.log.info(
            "Using file extractor: %s", self.extractor_plugin.__name__)
        self.extractor_plugin_inst = self.extractor_plugin(parent=self)

        self.log.info(
            "Using file collector: %s", self.collector_plugin.__name__)
        self.collector_plugin_inst = self.collector_plugin(parent=self)

    @catch_config_error
    def initialize(self, argv=None):
        cwd = os.getcwd()
        if cwd not in sys.path:
            # Add cwd to path so that custom plugins are found and loaded
            sys.path.insert(0, cwd)

        super(ZipCollectApp, self).initialize(argv)

        # set assignemnt and course
        if len(self.extra_args) == 1:
            self.coursedir.assignment_id = self.extra_args[0]
        elif len(self.extra_args) > 2:
            self.fail("Too many arguments")
        elif self.coursedir.assignment_id == "":
            self.fail(
                "Must provide assignment name:\n"
                "nbgrader zip_collect ASSIGNMENT"
            )

    def start(self):
        super(ZipCollectApp, self).start()
        self.init_plugins()
        self.extract_archive_files()
        self.process_extracted_files()

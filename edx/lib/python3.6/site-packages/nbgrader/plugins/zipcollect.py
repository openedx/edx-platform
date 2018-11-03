import os
import re
import shutil

from textwrap import dedent
from traitlets import Bool, List, Unicode

from .base import BasePlugin
from ..utils import unzip


class ExtractorPlugin(BasePlugin):
    """Submission archive files extractor plugin for the
    :class:`~nbgrader.apps.zipcollectapp.ZipCollectApp`.
    Extractor plugin subclasses MUST inherit from this class.
    """

    force = Bool(
        default_value=False,
        help="Force overwrite of existing files."
    ).tag(config=True)

    zip_ext = List(
        ['.zip', '.gz'],
        help=dedent(
            """
            List of valid archive (zip) filename extensions to extract. Any
            archive (zip) files with an extension not in this list are copied
            to the `extracted_directory`.
            """
        )
    ).tag(config=True)

    def extract(self, archive_path, extracted_path):
        """Extract archive (zip) files and submission files in the
        `archive_directory`. Files are extracted to the `extracted_directory`.
        Non-archive (zip) files found in the `archive_directory` are copied to
        the `extracted_directory`.
        This is the main function called by the
        :class:`~nbgrader.apps.zipcollectapp.ZipCollectApp` for each archive
        file to be extracted.

        Arguments
        ---------
        archive_path: str
            Absolute path to the `archive_directory`.
        extracted_path: str
            Absolute path to the `extracted_directory`.
        """
        if not os.listdir(archive_path):
            self.log.warning(
                "No files found in directory: {}".format(archive_path))
            return

        for root, _, archive_files in os.walk(archive_path):
            if not archive_files:
                continue

            extract_to = os.path.normpath(os.path.join(
                extracted_path,
                os.path.relpath(root, archive_path)
            ))
            if not os.path.isdir(extract_to):
                os.makedirs(extract_to)

            for zfile in archive_files:
                zfile = os.path.join(root, zfile)
                filename, ext = os.path.splitext(os.path.basename(zfile))
                # unzip (tree) each archive file in archive_path
                if ext in self.zip_ext:
                    # double splitext for .tar.gz
                    fname, ext = os.path.splitext(os.path.basename(filename))
                    if ext == '.tar':
                        filename = fname
                    self.log.info("Extracting from: {}".format(zfile))
                    self.log.info("  Extracting to: {}".format(
                        os.path.join(extract_to, filename)))
                    unzip(
                        zfile,
                        extract_to,
                        zip_ext=self.zip_ext,
                        create_own_folder=True,
                        tree=True
                    )

                # move each non-archive file in archive_path
                else:
                    dest = os.path.join(extract_to, os.path.basename(zfile))
                    self.log.info("Copying from: {}".format(zfile))
                    self.log.info("  Copying to: {}".format(dest))
                    shutil.copy(zfile, dest)


class FileNameCollectorPlugin(BasePlugin):
    """Submission filename collector plugin for the
    :class:`~nbgrader.apps.zipcollectapp.ZipCollectApp`.
    Collect plugin subclasses MUST inherit from this class.
    """

    named_regexp = Unicode(
        default_value='',
        help=dedent(
            """
            This regular expression is applied to each submission filename and
            MUST be supplied by the instructor. This regular expression MUST
            provide the `(?P<student_id>...)` and `(?P<file_id>...)` named
            group expressions. Optionally this regular expression can also
            provide the `(?P<first_name>...)`, `(?P<last_name>...)`,
            `(?P<email>...)`, and `(?P<timestamp>...)` named group expressions.
            For example if the filename is:

                `ps1_bitdiddle_attempt_2016-01-30-15-00-00_problem1.ipynb`

            then this `named_regexp` could be:

                ".*_(?P<student_id>\w+)_attempt_(?P<timestamp>[0-9\-]+)_(?P<file_id>\w+)"

            For named group regular expression examples see
            https://docs.python.org/howto/regex.html
            """
        )
    ).tag(config=True)

    valid_ext = List(
        default_value=['.ipynb'],
        help=dedent(
            """
            List of valid submission filename extensions to collect. Any
            submitted file with an extension not in this list is skipped.
            """
        )
    ).tag(config=True)

    def _match(self, filename):
        """Match the named group regular expression to the beginning of the
        filename and return the match groupdict or None if no match.
        """
        if not self.named_regexp:
            self.log.warning(
                "Regular expression not provided for plugin. Run with "
                "`--help-all` flag for more information."
            )
            return None

        match = re.match(self.named_regexp, filename)
        if not match or not match.groups():
            self.log.warning(
                "Regular expression '{}' did not match anything in: {}"
                "".format(self.named_regexp, filename)
            )
            return None

        gd = match.groupdict()
        self.log.debug(
            "Regular expression '{}' matched\n'{}' in: {}"
            "".format(self.named_regexp, gd, filename)
        )
        return gd

    def collect(self, submitted_file):
        """This is the main function called by the
        :class:`~nbgrader.apps.zipcollectapp.ZipCollectApp` for each submitted
        file. Note this function must also return a dictionary or None for
        sub-classed plugins.

        Arguments
        ---------
        submitted_file: str
            Each submitted file in the ``extracted_directory`` (absolute path).

        Returns
        -------
        groupdict: dict
            Collected data from the filename or None if the file should be
            skipped. Collected data is a dict of the form::

                {
                    file_id: file_id,  # MUST be provided
                    student_id: student_id,  # MUST be provided
                    timestamp: timestamp  # Can optional be provided
                }

            Note: ``file_id`` MUST include the the relative path to the
            assignment if you are collecting files in assignment sub-folders.
        """
        _, ext = os.path.splitext(submitted_file)

        # Skip any files without the correct extension
        if ext not in self.valid_ext:
            self.log.debug("Invalid file extension {}: {}".format(ext, submitted_file))
            return None

        groupdict = self._match(submitted_file)
        if not groupdict:
            return None
        return groupdict

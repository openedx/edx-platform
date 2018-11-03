import os
from stat import (
    S_IRUSR, S_IWUSR, S_IXUSR,
    S_IRGRP, S_IWGRP, S_IXGRP,
    S_IROTH, S_IWOTH, S_IXOTH
)

from textwrap import dedent
from traitlets import Bool

from .exchange import Exchange
from ..utils import get_username, check_mode, find_all_notebooks


class ExchangeSubmit(Exchange):

    strict = Bool(
        False,
        help=dedent(
            "Whether or not to submit the assignment if there are missing "
            "notebooks from the released assignment notebooks."
        )
    ).tag(config=True)

    def init_src(self):
        if self.path_includes_course:
            root = os.path.join(self.course_id, self.coursedir.assignment_id)
        else:
            root = self.coursedir.assignment_id
        self.src_path = os.path.abspath(root)
        self.coursedir.assignment_id = os.path.split(self.src_path)[-1]
        if not os.path.isdir(self.src_path):
            self.fail("Assignment not found: {}".format(self.src_path))

    def init_dest(self):
        if self.course_id == '':
            self.fail("No course id specified. Re-run with --course flag.")

        self.inbound_path = os.path.join(self.root, self.course_id, 'inbound')
        if not os.path.isdir(self.inbound_path):
            self.fail("Inbound directory doesn't exist: {}".format(self.inbound_path))
        if not check_mode(self.inbound_path, write=True, execute=True):
            self.fail("You don't have write permissions to the directory: {}".format(self.inbound_path))

        self.cache_path = os.path.join(self.cache, self.course_id)
        self.assignment_filename = '{}+{}+{}'.format(get_username(), self.coursedir.assignment_id, self.timestamp)

    def init_release(self):
        if self.course_id == '':
            self.fail("No course id specified. Re-run with --course flag.")

        course_path = os.path.join(self.root, self.course_id)
        outbound_path = os.path.join(course_path, 'outbound')
        self.release_path = os.path.join(outbound_path, self.coursedir.assignment_id)
        if not os.path.isdir(self.release_path):
            self.fail("Assignment not found: {}".format(self.release_path))
        if not check_mode(self.release_path, read=True, execute=True):
            self.fail("You don't have read permissions for the directory: {}".format(self.release_path))

    def check_filename_diff(self):
        released_notebooks = find_all_notebooks(self.release_path)
        submitted_notebooks = find_all_notebooks(self.src_path)

        # Look for missing notebooks in submitted notebooks
        missing = False
        release_diff = list()
        for filename in released_notebooks:
            if filename in submitted_notebooks:
                release_diff.append("{}: {}".format(filename, 'FOUND'))
            else:
                missing = True
                release_diff.append("{}: {}".format(filename, 'MISSING'))

        # Look for extra notebooks in submitted notebooks
        extra = False
        submitted_diff = list()
        for filename in submitted_notebooks:
            if filename in released_notebooks:
                submitted_diff.append("{}: {}".format(filename, 'OK'))
            else:
                extra = True
                submitted_diff.append("{}: {}".format(filename, 'EXTRA'))

        if missing or extra:
            diff_msg = (
                "Expected:\n\t{}\nSubmitted:\n\t{}".format(
                    '\n\t'.join(release_diff),
                    '\n\t'.join(submitted_diff),
                )
            )
            if missing and self.strict:
                self.fail(
                    "Assignment {} not submitted. "
                    "There are missing notebooks for the submission:\n{}"
                    "".format(self.coursedir.assignment_id, diff_msg)
                )
            else:
                self.log.warning(
                    "Possible missing notebooks and/or extra notebooks "
                    "submitted for assignment {}:\n{}"
                    "".format(self.coursedir.assignment_id, diff_msg)
                )

    def copy_files(self):
        self.init_release()

        dest_path = os.path.join(self.inbound_path, self.assignment_filename)
        cache_path = os.path.join(self.cache_path, self.assignment_filename)

        self.log.info("Source: {}".format(self.src_path))
        self.log.info("Destination: {}".format(dest_path))

        # copy to the real location
        self.check_filename_diff()
        self.do_copy(self.src_path, dest_path)
        with open(os.path.join(dest_path, "timestamp.txt"), "w") as fh:
            fh.write(self.timestamp)
        self.set_perms(
            dest_path,
            fileperms=(S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH),
            dirperms=(S_IRUSR | S_IWUSR | S_IXUSR | S_IRGRP | S_IXGRP | S_IROTH | S_IXOTH))

        # Make this 0777=ugo=rwx so the instructor can delete later. Hidden from other users by the timestamp.
        os.chmod(
            dest_path,
            S_IRUSR|S_IWUSR|S_IXUSR|S_IRGRP|S_IWGRP|S_IXGRP|S_IROTH|S_IWOTH|S_IXOTH
        )

        # also copy to the cache
        if not os.path.isdir(self.cache_path):
            os.makedirs(self.cache_path)
        self.do_copy(self.src_path, cache_path)
        with open(os.path.join(cache_path, "timestamp.txt"), "w") as fh:
            fh.write(self.timestamp)

        self.log.info("Submitted as: {} {} {}".format(
            self.course_id, self.coursedir.assignment_id, str(self.timestamp)
        ))

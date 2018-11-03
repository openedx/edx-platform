import os
import shutil
from stat import (
    S_IRUSR, S_IWUSR, S_IXUSR,
    S_IRGRP, S_IWGRP, S_IXGRP,
    S_IROTH, S_IWOTH, S_IXOTH,
    S_ISGID, ST_MODE
)

from traitlets import Bool

from .exchange import Exchange
from ..utils import self_owned


class ExchangeRelease(Exchange):

    force = Bool(False, help="Force overwrite existing files in the exchange.").tag(config=True)

    def ensure_root(self):
        perms = S_IRUSR|S_IWUSR|S_IXUSR|S_IRGRP|S_IWGRP|S_IXGRP|S_IROTH|S_IWOTH|S_IXOTH

        # if root doesn't exist, create it and set permissions
        if not os.path.exists(self.root):
            self.log.warning("Creating exchange directory: {}".format(self.root))
            try:
                os.makedirs(self.root)
                os.chmod(self.root, perms)
            except PermissionError:
                self.fail("Could not create {}, permission denied.".format(self.root))

        else:
            old_perms = oct(os.stat(self.root)[ST_MODE] & 0o777)
            new_perms = oct(perms & 0o777)
            if old_perms != new_perms:
                self.log.warning(
                    "Permissions for exchange directory ({}) are invalid, changing them from {} to {}".format(
                        self.root, old_perms, new_perms))
                try:
                    os.chmod(self.root, perms)
                except PermissionError:
                    self.fail("Could not change permissions of {}, permission denied.".format(self.root))

    def init_src(self):
        self.src_path = self.coursedir.format_path(self.coursedir.release_directory, '.', self.coursedir.assignment_id)
        if not os.path.isdir(self.src_path):
            source = self.coursedir.format_path(self.coursedir.source_directory, '.', self.coursedir.assignment_id)
            if os.path.isdir(source):
                # Looks like the instructor forgot to assign
                self.fail("Assignment found in '{}' but not '{}', run `nbgrader assign` first.".format(
                    source, self.src_path))
            else:
                self.fail("Assignment not found: {}".format(self.src_path))

    def init_dest(self):
        if self.course_id == '':
            self.fail("No course id specified. Re-run with --course flag.")

        self.course_path = os.path.join(self.root, self.course_id)
        self.outbound_path = os.path.join(self.course_path, 'outbound')
        self.inbound_path = os.path.join(self.course_path, 'inbound')
        self.dest_path = os.path.join(self.outbound_path, self.coursedir.assignment_id)
        # 0755
        self.ensure_directory(
            self.course_path,
            S_IRUSR|S_IWUSR|S_IXUSR|S_IRGRP|S_IXGRP|S_IROTH|S_IXOTH
        )
        # 0755
        self.ensure_directory(
            self.outbound_path,
            S_IRUSR|S_IWUSR|S_IXUSR|S_IRGRP|S_IXGRP|S_IROTH|S_IXOTH
        )
        # 0733 with set GID so student submission will have the instructors group
        self.ensure_directory(
            self.inbound_path,
            S_ISGID|S_IRUSR|S_IWUSR|S_IXUSR|S_IWGRP|S_IXGRP|S_IWOTH|S_IXOTH
        )

    def ensure_directory(self, path, mode):
        """Ensure that the path exists, has the right mode and is self owned."""
        if not os.path.isdir(path):
            os.mkdir(path)
            # For some reason, Python won't create a directory with a mode of 0o733
            # so we have to create and then chmod.
            os.chmod(path, mode)
        else:
            if not self_owned(path):
                self.fail("You don't own the directory: {}".format(path))

    def copy_files(self):
        if os.path.isdir(self.dest_path):
            if self.force:
                self.log.info("Overwriting files: {} {}".format(
                    self.course_id, self.coursedir.assignment_id
                ))
                shutil.rmtree(self.dest_path)
            else:
                self.fail("Destination already exists, add --force to overwrite: {} {}".format(
                    self.course_id, self.coursedir.assignment_id
                ))
        self.log.info("Source: {}".format(self.src_path))
        self.log.info("Destination: {}".format(self.dest_path))
        self.do_copy(self.src_path, self.dest_path)
        self.set_perms(
            self.dest_path,
            fileperms=(S_IRUSR|S_IWUSR|S_IRGRP|S_IROTH),
            dirperms=(S_IRUSR|S_IWUSR|S_IXUSR|S_IRGRP|S_IXGRP|S_IROTH|S_IXOTH))
        self.log.info("Released as: {} {}".format(self.course_id, self.coursedir.assignment_id))

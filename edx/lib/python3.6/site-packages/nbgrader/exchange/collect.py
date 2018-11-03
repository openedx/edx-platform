import os
import glob
import shutil
from collections import defaultdict

from traitlets import Bool

from .exchange import Exchange
from ..utils import check_mode, parse_utc


def groupby(l, key=lambda x: x):
    d = defaultdict(list)
    for item in l:
        d[key(item)].append(item)
    return d


class ExchangeCollect(Exchange):

    update = Bool(
        False,
        help="Update existing submissions with ones that have newer timestamps."
    ).tag(config=True)

    def _path_to_record(self, path):
        filename = os.path.split(path)[1]
        # Only split twice on +, giving three components. This allows usernames with +.
        filename_list = filename.rsplit('+', 2)
        if len(filename_list) != 3:
            self.fail("Invalid filename: {}".format(filename))
        username = filename_list[0]
        timestamp = parse_utc(filename_list[2])
        return {'username': username, 'filename': filename, 'timestamp': timestamp}

    def _sort_by_timestamp(self, records):
        return sorted(records, key=lambda item: item['timestamp'], reverse=True)

    def init_src(self):
        if self.course_id == '':
            self.fail("No course id specified. Re-run with --course flag.")

        self.course_path = os.path.join(self.root, self.course_id)
        self.inbound_path = os.path.join(self.course_path, 'inbound')
        if not os.path.isdir(self.inbound_path):
            self.fail("Course not found: {}".format(self.inbound_path))
        if not check_mode(self.inbound_path, read=True, execute=True):
            self.fail("You don't have read permissions for the directory: {}".format(self.inbound_path))
        student_id = self.coursedir.student_id if self.coursedir.student_id else '*'
        pattern = os.path.join(self.inbound_path, '{}+{}+*'.format(student_id, self.coursedir.assignment_id))
        records = [self._path_to_record(f) for f in glob.glob(pattern)]
        usergroups = groupby(records, lambda item: item['username'])
        self.src_records = [self._sort_by_timestamp(v)[0] for v in usergroups.values()]

    def init_dest(self):
        pass

    def copy_files(self):
        if len(self.src_records) == 0:
            self.log.warning("No submissions of '{}' for course '{}' to collect".format(
                self.coursedir.assignment_id,
                self.course_id))
        else:
            self.log.info("Processing {} submissions of '{}' for course '{}'".format(
                len(self.src_records),
                self.coursedir.assignment_id,
                self.course_id))

        for rec in self.src_records:
            student_id = rec['username']
            src_path = os.path.join(self.inbound_path, rec['filename'])
            dest_path = self.coursedir.format_path(self.coursedir.submitted_directory, student_id, self.coursedir.assignment_id)
            if not os.path.exists(os.path.dirname(dest_path)):
                os.makedirs(os.path.dirname(dest_path))

            copy = False
            updating = False
            if os.path.isdir(dest_path):
                existing_timestamp = self.coursedir.get_existing_timestamp(dest_path)
                new_timestamp = rec['timestamp']
                if self.update and (existing_timestamp is None or new_timestamp > existing_timestamp):
                    copy = True
                    updating = True
            else:
                copy = True

            if copy:
                if updating:
                    self.log.info("Updating submission: {} {}".format(student_id, self.coursedir.assignment_id))
                    shutil.rmtree(dest_path)
                else:
                    self.log.info("Collecting submission: {} {}".format(student_id, self.coursedir.assignment_id))
                self.do_copy(src_path, dest_path)
            else:
                if self.update:
                    self.log.info("No newer submission to collect: {} {}".format(
                        student_id, self.coursedir.assignment_id
                    ))
                else:
                    self.log.info("Submission already exists, use --update to update: {} {}".format(
                        student_id, self.coursedir.assignment_id
                    ))

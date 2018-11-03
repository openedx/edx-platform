import os
import glob
import shutil
import re

from traitlets import Bool

from .exchange import Exchange


class ExchangeList(Exchange):

    inbound = Bool(False, help="List inbound files rather than outbound.").tag(config=True)
    cached = Bool(False, help="List assignments in submission cache.").tag(config=True)
    remove = Bool(False, help="Remove, rather than list files.").tag(config=True)

    def init_src(self):
        pass

    def init_dest(self):
        course_id = self.course_id if self.course_id else '*'
        assignment_id = self.coursedir.assignment_id if self.coursedir.assignment_id else '*'
        student_id = self.coursedir.student_id if self.coursedir.student_id else '*'

        if self.inbound:
            pattern = os.path.join(self.root, course_id, 'inbound', '{}+{}+*'.format(student_id, assignment_id))
        elif self.cached:
            pattern = os.path.join(self.cache, course_id, '{}+{}+*'.format(student_id, assignment_id))
        else:
            pattern = os.path.join(self.root, course_id, 'outbound', '{}'.format(assignment_id))

        self.assignments = sorted(glob.glob(pattern))

    def parse_assignment(self, assignment):
        if self.inbound:
            regexp = r".*/(?P<course_id>.*)/inbound/(?P<student_id>.*)\+(?P<assignment_id>.*)\+(?P<timestamp>.*)"
        elif self.cached:
            regexp = r".*/(?P<course_id>.*)/(?P<student_id>.*)\+(?P<assignment_id>.*)\+(?P<timestamp>.*)"
        else:
            regexp = r".*/(?P<course_id>.*)/outbound/(?P<assignment_id>.*)"

        m = re.match(regexp, assignment)
        if m is None:
            raise RuntimeError("Could not match '%s' with regexp '%s'", assignment, regexp)
        return m.groupdict()

    def format_inbound_assignment(self, info):
        return "{course_id} {student_id} {assignment_id} {timestamp}".format(**info)

    def format_outbound_assignment(self, info):
        msg = "{course_id} {assignment_id}".format(**info)
        if os.path.exists(info['assignment_id']):
            msg += " (already downloaded)"
        return msg

    def copy_files(self):
        pass

    def parse_assignments(self):
        assignments = []
        for path in self.assignments:
            info = self.parse_assignment(path)
            if self.path_includes_course:
                root = os.path.join(info['course_id'], info['assignment_id'])
            else:
                root = info['assignment_id']

            if self.inbound or self.cached:
                info['status'] = 'submitted'
                info['path'] = path
            elif os.path.exists(root):
                info['status'] = 'fetched'
                info['path'] = os.path.abspath(root)
            else:
                info['status'] = 'released'
                info['path'] = path

            if self.remove:
                info['status'] = 'removed'

            info['notebooks'] = []
            for notebook in sorted(glob.glob(os.path.join(info['path'], '*.ipynb'))):
                info['notebooks'].append({
                    'notebook_id': os.path.splitext(os.path.split(notebook)[1])[0],
                    'path': os.path.abspath(notebook)
                })

            assignments.append(info)

        return assignments

    def list_files(self):
        """List files."""
        assignments = self.parse_assignments()

        if self.inbound or self.cached:
            self.log.info("Submitted assignments:")
            for info in assignments:
                self.log.info(self.format_inbound_assignment(info))
        else:
            self.log.info("Released assignments:")
            for info in assignments:
                self.log.info(self.format_outbound_assignment(info))

        return assignments

    def remove_files(self):
        """List and remove files."""
        assignments = self.parse_assignments()

        if self.inbound or self.cached:
            self.log.info("Removing submitted assignments:")
            for info in assignments:
                self.log.info(self.format_inbound_assignment(info))
        else:
            self.log.info("Removing released assignments:")
            for info in assignments:
                self.log.info(self.format_outbound_assignment(info))

        for assignment in self.assignments:
            shutil.rmtree(assignment)

        return assignments

    def start(self):
        if self.inbound and self.cached:
            self.fail("Options --inbound and --cached are incompatible.")

        super(ExchangeList, self).start()

        if self.remove:
            return self.remove_files()
        else:
            return self.list_files()

""" Contains Locations ___ """

import urllib
from xmodule.modulestore.keys import CourseKey
from xmodule.modulestore import Location


class SlashSeparatedCourseKey(CourseKey):
    """Course key for old style org/course/run course identifiers"""
    def __init__(self, org, course, run):
        self._org = org
        self._course = course
        self._run = run

    # three local attributes: catalog name, run

    @classmethod
    def _from_string(cls, serialized):
        # Turns encoded slashes into actual slashes
        return cls(*serialized.split('/'))

    def _to_string(self):
        # Turns slashes into encoded slashes
        return "/".join([self._org, self._course, self._run])

    @property
    def org(self):
        return self._org

    @property
    def run(self):
        return '/'.join([self._course, self._run])

    def make_asset_key(self, path):
        return Location('c4x', self._org, self._course, 'asset', path)

    def make_usage_key(self, block_type, name):
        return Location('i4x', self._org, self._course, block_type, name)

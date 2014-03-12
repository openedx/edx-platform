""" Contains Locations ___ """

from xmodule.modulestore.keys import CourseKey

class CourseLocation(CourseKey):
    def __init__(org, course, run):
        self.org = org
        self.course = course
        self.run = run

    # three local attributes: catalog name, run

    @classmethod
    def _from_string(cls, serialized):
        # Turns encoded slashes into actual slashes
        serialized = django.utils.http.unquote(serialized)
        return cls(* serialized.split('/'))

    def _to_string(self):
        # Turns slashes into encoded slashes
        return "%2F".join(self.org, self.course, self.run)

    def org(self):
        return self.org

    def run(self):
        return self.run

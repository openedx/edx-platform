from __future__ import absolute_import


class TeamsService(object):
    def get_team(self, user, course_id):
        from . import api
        return api.get_team_for_user_and_course(user, course_id)

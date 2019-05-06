"""
XBlock for Staff Graded Problem
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import csv
import hashlib
import io
import json
import logging

import markdown
from crum import get_current_request
from django.middleware.csrf import get_token
from web_fragments.fragment import Fragment
from webob import Response
from xblock.core import XBlock
from xblock.fields import Float, Scope, String
from xblock.runtime import NoSuchServiceError
from xblock.scorable import ScorableXBlockMixin, Score
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin


_ = lambda text: text

log = logging.getLogger(__name__)


CSV_FIELDS = '''user_id username full_name email student_uid is_active track
block_id title date_last_graded who_last_graded last_points new_points'''.split()


@XBlock.needs('settings')
@XBlock.needs('grade_utils')
@XBlock.needs('i18n')
@XBlock.needs('user')
class StaffGradedBlock(StudioEditableXBlockMixin, ScorableXBlockMixin, XBlock):
    """
    Staff Graded Problem block
    """
    display_name = String(
        display_name=_("Display Name"),
        help=_("The display name for this component."),
        scope=Scope.settings,
        default=_("Staff Graded Problem"),
    )
    instructions = String(
        display_name=_("Instructions"),
        help=_("The instructions to the learner. Markdown format"),
        scope=Scope.settings,
        multiline_editor=True,
        default=_("Your results will be graded offline"),
        runtime_options={'multiline_editor': 'html'},
    )
    weight = Float(
        display_name="Weight",
        help=_(
            "Enter the number of points possible for this component.  "
            "The default value is 1.0.  "
        ),
        default=1.0,
        scope=Scope.settings,
        values={"min": 0},
    )
    has_score = True

    editable_fields = ('display_name', 'instructions', 'weight')

    def _get_current_username(self):
        return self.runtime.service(self, 'user').get_current_user().opt_attrs.get(
            'edx-platform.username')

    def student_view(self, context):

        fragment = Fragment()
        loader = ResourceLoader(__name__)

        context['id'] = self.location.block_id
        context['instructions'] = markdown.markdown(self.instructions)
        context['display_name'] = self.display_name
        context['is_staff'] = self.runtime.user_is_staff

        if context['is_staff']:
            context['import_url'] = self.runtime.handler_url(self, "csv_import_handler")
            context['export_url'] = self.runtime.handler_url(self, "csv_export_handler")
            context['csrf_token'] = get_token(get_current_request())

        try:
            context['score'] = self.runtime.service(self, "grade_utils").get_score(self.location, self.runtime.user_id) or {}
            if context['score']:
                context['score']['grade_pct'] = format(context['score']['grade'], '.0%')
            context['grades_available'] = True
        except NoSuchServiceError:
            context['grades_available'] = False
        fragment.add_content(loader.render_django_template('/templates/html/sgp.html', context))
        return fragment

    @XBlock.handler
    def csv_import_handler(self, request, suffix=''):  # pylint: disable=unused-argument
        if not self.runtime.user_is_staff:
            return Response('not allowed', status_code=403)
        grade_utils = self.runtime.service(self, 'grade_utils')

        my_location = self.location
        processed = 0
        errors = 0
        data = {}
        try:
            reader = csv.DictReader(request.POST['csv'].file)
        except KeyError:
            errors = 1
            data['message'] = 'missing file'
        else:
            max_points = self.weight
            state = json.dumps({'grader': self._get_current_username()})
            for rownum, row in enumerate(reader):
                if row['new_points']:
                    new_points = float(row['new_points'])
                    if new_points <= max_points:
                        grade_utils.set_score(my_location, row['user_id'], new_points, max_points, state=state)
                        processed += 1
                    else:
                        errors += 1
        data['errors'] = errors
        data['processed'] = processed
        log.info(data)
        return Response(json.dumps(data), content_type='application/json')

    @XBlock.handler
    def csv_export_handler(self, request, suffix=''):  # pylint: disable=unused-argument
        if not self.runtime.user_is_staff:
            return Response('not allowed', status_code=403)

        buf = io.BytesIO()
        writer = csv.DictWriter(buf, CSV_FIELDS)
        writer.writeheader()
        my_location = str(self.location)
        my_name = self.display_name
        grade_utils = self.runtime.service(self, 'grade_utils')
        students = grade_utils.get_scores(self.location)

        user_service = self.runtime.service(self, 'user')
        enrollments = user_service.get_enrollments(self.location.course_key)
        for enrollment in enrollments:
            srow = {
                'block_id': my_location,
                'title': my_name,
                'new_points': None
            }
            srow.update(enrollment)
            score = students.get(enrollment['user_id'], None)

            if score:
                srow['last_points'] = int(score['grade'] * self.weight)
                srow['date_last_graded'] = score['modified']
                state = score['state']
                if state:
                    srow['who_last_graded'] = json.loads(state).get('grader', '')

            writer.writerow(srow)

        resp = Response(buf.getvalue())
        resp.content_type = 'text/csv'
        resp.content_disposition = 'attachment; filename="%s.csv"' % self.location
        return resp

    def max_score(self):
        return self.weight

    def get_score(self):
        """
        Return a raw score already persisted on the XBlock.  Should not
        perform new calculations.

        Returns:
            Score(raw_earned=float, raw_possible=float)
        """
        score = self.runtime.service(self, "grade_utils").get_score(self.runtime.user_id, self.location) or {'grade': 0, 'max_grade': 1}
        return Score(raw_earned=score['grade'], raw_possible=score['max_grade'])

    def set_score(self, score):
        """
        Persist a score to the XBlock.

        The score is a named tuple with a raw_earned attribute and a
        raw_possible attribute, reflecting the raw earned score and the maximum
        raw score the student could have earned respectively.

        Arguments:
            score: Score(raw_earned=float, raw_possible=float)

        Returns:
            None
        """
        state = json.dumps({'grader': self._get_current_username()})
        self.runtime.service(self, "grade_utils").set_score(self.location,
                                                            self.runtime.user_id,
                                                            score.raw_earned,
                                                            score.raw_possible,
                                                            state=state)
        log.info(score)

    def publish_grade(self):
        pass

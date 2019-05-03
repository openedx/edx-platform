from __future__ import absolute_import, division, print_function, unicode_literals

import csv
import io
import json
import logging
from collections import namedtuple

import six

import markdown
from student.models import CourseEnrollment
from web_fragments.fragment import Fragment
from webob import Response
from xblock.core import XBlock
from xblock.fields import Boolean, Float, Integer, List, Scope, String
from xblock.runtime import NoSuchServiceError
from xblock.scorable import ScorableXBlockMixin, Score
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin
from xmodule.fields import ScoreField

_ = lambda text: text

log = logging.getLogger(__name__)

ScoreRow = namedtuple('ScoreRow', 'user_id username full_name email student_uid enrollment_is_active enrollment_track block_id unit_title date_last_graded who_last_graded last_points new_points')


@XBlock.needs('settings')
@XBlock.needs('grade_utils')
@XBlock.needs('i18n')
class StaffGradedBlock(StudioEditableXBlockMixin, ScorableXBlockMixin, XBlock):
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
    score = ScoreField(help=_("Dictionary with the current student score"), scope=Scope.user_state, enforce_type=False)
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

    def student_view(self, context):
        fragment = Fragment()
        loader = ResourceLoader(__name__)

        try:
            score = self.runtime.service(self, "grade_utils").get_score(self.runtime.user_id, self.location)
        except NoSuchServiceError:
            score = None
        context['instructions'] = markdown.markdown(self.instructions)
        context['display_name'] = self.display_name
        context['score'] = score
        context['is_staff'] = self.runtime.user_is_staff
        if context['is_staff']:
            context['import_url'] = self.runtime.handler_url(self, "csv_import_handler")
            context['export_url'] = self.runtime.handler_url(self, "csv_export_handler")
            from django.middleware.csrf import get_token
            from crum import get_current_request
            context['csrf_token'] = get_token(get_current_request())
        fragment.add_content(loader.render_django_template('/templates/html/sgp.html', context))

        return fragment

    @XBlock.handler
    def csv_import_handler(self, request, suffix=''):
        grade_utils = self.runtime.service(self, 'grade_utils')
        log.info(repr(request.POST))
        my_location = self.location
        processed = 0
        errors = 0
        data = {}
        try:
            reader = csv.reader(request.POST['csv'].file)
        except KeyError:
            errors = 1
            data['message'] = 'missing file'
        else:
            for rownum, row in enumerate(reader):
                try:
                    srow = ScoreRow(*row)
                except (ValueError, TypeError):
                    errors += 1
                    continue
                if rownum == 0 and not srow.user_id.isdigit():
                    log.info(row)
                    # header row
                    continue
                if srow.new_points:
                    new_points = float(srow.new_points)
                    grade_utils.set_score(my_location, srow.user_id, new_points)
                    processed += 1
                log.info(row)
        data['errors'] = errors
        data['processed'] = processed
        return Response(json.dumps(data), content_type='application/json')

    @XBlock.handler
    def csv_export_handler(self, request, suffix=''):
        buf = io.BytesIO()
        writer = csv.writer(buf)
        my_location = str(self.location)
        my_name = self.display_name
        grade_utils = self.runtime.service(self, 'grade_utils')
        students = {row.student.id: row for row in grade_utils.get_scores(self.location)}
        writer.writerow(ScoreRow._fields)

        for enrollment in CourseEnrollment.objects.filter(course_id=self.location.course_key):
            score = students.get(enrollment.user.id, None)

            srow = ScoreRow(
                enrollment.user.id,
                enrollment.user.username,
                enrollment.user.profile.name,
                enrollment.user.email,
                '',
                enrollment.is_active,
                enrollment.mode,
                my_location,
                my_name,
                score.modified if score else None,
                'who' if score else None,
                score.score if score else None,
                None
            )
            writer.writerow(srow)

        resp = Response(buf.getvalue())
        resp.content_type = 'text/csv'
        resp.content_disposition = 'attachment; filename="%s.csv"' % self.location
        return resp

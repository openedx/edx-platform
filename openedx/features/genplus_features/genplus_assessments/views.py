from __future__ import absolute_import, print_function, unicode_literals
import io
import os
from os.path import basename, splitext, dirname, join
import tempfile
from itertools import chain
import pdfkit

from collections import defaultdict
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.http import HttpResponse
from django.template import loader
from django.test import override_settings
from django.views.generic import TemplateView
from django.template.loader import render_to_string
from django.contrib.staticfiles import finders

from opaque_keys.edx.keys import CourseKey
from openedx.features.genplus_features.genplus_assessments.models import UserRating, UserResponse
from .utils import (
    build_course_report_for_students,
    get_absolute_url,
    get_student_program_skills_assessment,
    get_user_assessment_result
)
from openedx.features.genplus_features.genplus.models import GenUser, Student, JournalPost, Teacher
from openedx.features.genplus_features.genplus_learning.models import Program, Unit, UnitCompletion
from openedx.features.genplus_features.genplus_badges.models import BoosterBadgeAward
from openedx.features.genplus_features.genplus.constants import JournalTypes
from openedx.features.genplus_features.genplus_assessments.api.v1.serializers import RatingAssessmentSerializer, TextAssessmentSerializer

class AssessmentReportPDFView(TemplateView):
    filename = None
    inline = False
    pdfkit_options = None
    template_path = 'genplus_assessments/assessment-report.html'
    header_template_path = 'genplus_assessments/assessment-header.html'
    stylesheet_path = 'static/genplus_assessments/assets/css/main.css'
    static_images_path = 'static/genplus_assessments/assets/images'

    def get(self, request, *args, **kwargs):
        """
        Return a HTTPResponse either of a PDF file or HTML.
        :rtype: HttpResponse
        """
        context = self.get_context_data(*args, **kwargs)

        if 'html' in request.GET:
            # Output HTML
            content = self.render_html(context, *args, **kwargs)
            return HttpResponse(content)

        else:
            # Output PDF
            content = self.render_pdf(context, *args, **kwargs)

            response = HttpResponse(content, content_type='application/pdf')

            if (not self.inline or 'download' in request.GET) and 'inline' not in request.GET:
                response['Content-Disposition'] = 'attachment; filename=%s' % self.get_filename()

            response['Content-Length'] = len(content)

            return response

    def render_pdf(self, context, *args, **kwargs):
        """
        Render the PDF and returns as bytes.
        :rtype: bytes
        """
        script_dir = dirname(__file__)
        html = self.render_html(context, *args, **kwargs)
        options = self.get_pdfkit_options()
        if 'debug' in self.request.GET and settings.DEBUG:
            options['debug-javascript'] = 1

        kwargs = {}
        wkhtmltopdf_bin = os.environ.get('WKHTMLTOPDF_BIN')
        if wkhtmltopdf_bin:
            kwargs['configuration'] = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_bin)

        try:
            if self.stylesheet_path:
                filename = join(script_dir, self.stylesheet_path)
                print("filename", filename)
                with tempfile.NamedTemporaryFile(suffix='.css', delete=False) as stylesheet_file, io.open(filename,'rb') as f:
                    options['user-style-sheet'] = stylesheet_file.name
                    styles = f.read()
                    stylesheet_file.write(styles)
                    stylesheet_file.flush()

            if self.header_template_path:
                absolute_image_dir_path = join(script_dir, self.static_images_path)
                with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as header_html:
                    options['header-html'] = header_html.name
                    context['images_dir'] = absolute_image_dir_path
                    rendered_html = render_to_string(self.header_template_path, context).encode('utf-8')
                    header_html.write(rendered_html)
                    header_html.flush()

            pdf = pdfkit.from_string(html, False, options, **kwargs)
            return pdf
        finally:
            # Ensure temporary file is deleted after finishing work
            if self.header_template_path:
                os.remove(options['header-html'])
            if self.stylesheet_path:
                os.remove(options['user-style-sheet'])

    def get_pdfkit_options(self):
        """
        Returns ``self.pdfkit_options`` if set otherwise a default dict of options to supply to pdfkit.
        :rtype: dict
        """
        if self.pdfkit_options is not None:
            return self.pdfkit_options

        return {
            'page-size': 'A4',
            'encoding': 'UTF-8',
            "enable-local-file-access": "",
            "enable-javascript": "",
            'margin-top': '2.3in',
            'margin-right': '0in',
            'margin-bottom': '1in',
            'margin-left': '0in',
            'no-outline': None,
            'header-spacing': '10',
        }

    def get_filename(self):
        """
        Return ``self.filename`` if set otherwise return the template basename with a ``.pdf`` extension.
        :rtype: str
        """
        if self.filename is None:
            name = splitext(basename(self.template_path))[0]
            return '{}.pdf'.format(name)

        return self.filename

    def render_html(self, context, *args, **kwargs):
        """
        Renders the template.
        :rtype: str
        """
        static_url = '%s://%s%s' % (self.request.scheme, self.request.get_host(), settings.STATIC_URL)
        media_url = '%s://%s%s' % (self.request.scheme, self.request.get_host(), settings.MEDIA_URL)

        with override_settings(STATIC_URL=static_url, MEDIA_URL=media_url):
            template = loader.get_template(self.template_path)
            html = template.render(context)
            return html

    def _get_skill_assessment_data(self, user_id, student, programs):
        skills_assessment = []
        user = User.objects.get(id=user_id)
        for program in programs:
            user_rating_qs  = UserRating.objects.filter(user=user_id, program=program.id)
            user_response_qs  = UserResponse.objects.filter(user=user_id, program=program.id)
            text_assessment_data = TextAssessmentSerializer(user_response_qs, many=True).data
            rating_assessment_data = RatingAssessmentSerializer(user_rating_qs, many=True).data
            raw_data = text_assessment_data + rating_assessment_data
            assessment_result = get_user_assessment_result(user, raw_data, program)
            skills_assessment.append(assessment_result)

        return skills_assessment

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if not self.request.user.is_authenticated:
            raise PermissionDenied()

        gen_user = GenUser.objects.filter(user=self.request.user).first()
        if not gen_user:
            raise PermissionDenied()

        if gen_user.is_student:
            user_id = self.request.user.id
            student = gen_user.student
        elif gen_user.is_teacher:
            user_id = self.request.GET.get('user_id')
            user = GenUser.objects.filter(user__id=user_id).first()
            if not (user and user.is_student):
                raise PermissionDenied()

            student = user.student
        else:
            raise PermissionDenied()

        course_reports = {}

        program_ids = student.program_enrollments.all().values_list('program', flat=True)
        programs = Program.objects.filter(id__in=program_ids)
        units = Unit.objects.filter(program__in=program_ids)
        course_keys = units.values_list('course', flat=True)
        unit_completions = UnitCompletion.objects.filter(course_key__in=course_keys, user=user_id)

        for course_key in course_keys:
            course_reports[str(course_key)] = build_course_report_for_students(
            user_id=self.request.user.id,
            course_key=course_key,
            student_list=[user_id],
        )

        character_image_url = ''
        if student.character and student.character.profile_pic:
            character_image_url = get_absolute_url(self.request, student.character.profile_pic)

        student_name = ''
        school_name = ''
        if student.user:
            student_name = student.user.profile.name
            school_name = student.gen_user.school.name

        student_data = {
            "user_id": user_id,
            "full_name": student_name,
            "school_name": school_name,
            "character_image_url": character_image_url,
            "units": [],
        }

        for unit in units:
            course_key = unit.course.id
            unit_completion = unit_completions.filter(course_key=course_key, user=user_id).first()
            unit_image_url = get_absolute_url(self.request, unit.unit_image) if unit.unit_image else ''

            course_data = {
                'course_key': str(course_key),
                'display_name': unit.display_name,
                'is_complete': unit_completion is not None and unit_completion.is_complete,
                'unit_image_url': unit_image_url,
                'reflections': course_reports[str(course_key)].get(user_id, [])
            }
            student_data['units'].append(course_data)

        booster_badges = BoosterBadgeAward.objects.filter(user__id=user_id).values('image_url', 'created')
        student_data['booster_badges'] = booster_badges
        teacher_feedbacks = {}
        for feedback in JournalPost.objects.filter(student=student, journal_type=JournalTypes.TEACHER_FEEDBACK):
            teacher_id = feedback.teacher.id

            if teacher_id not in teacher_feedbacks.keys():
                teacher_name = ''
                if feedback.teacher.user:
                    teacher_name = feedback.teacher.user.profile.name

                teacher_feedbacks[teacher_id] = {
                    'teacher_name': teacher_name,
                    'comments': [{
                        'description': feedback.description,
                        'datetime': feedback.created
                    }],
                }
            else:
                teacher_feedbacks[teacher_id]['comments'].append({
                    'description': feedback.description,
                    'datetime': feedback.created
                })

        student_data['teacher_feedbacks'] = teacher_feedbacks
        student_data['skills_assessment'] = self._get_skill_assessment_data(user_id, student, programs)
        context['student_data'] = student_data
        return context

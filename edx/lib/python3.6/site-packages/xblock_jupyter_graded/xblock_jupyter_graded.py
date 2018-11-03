"""Jupyter Notebook Graded XBlock"""
import inspect
import json
import logging
import os
import pkg_resources
from urllib import urlencode
from webob import Response

from django.core.urlresolvers import reverse
from django.template import Template, Context
from django.utils import timezone, dateparse
import nbgrader_utils as nbu

from scorable import ScorableXBlockMixin, Score

from xblock.core import XBlock
from xblock.fields import Scope, String, Integer, Float, Boolean, List
from xblock.fragment import Fragment
from xblockutils.studio_editable import StudioEditableXBlockMixin
from xblockutils.resources import ResourceLoader
from xmodule.studio_editable import StudioEditableBlock

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)


@XBlock.needs("user")
class JupyterGradedXBlock(StudioEditableXBlockMixin, ScorableXBlockMixin,
        XBlock, StudioEditableBlock):

    # Makes LMS icon appear as a problem
    icon_class = "problem"

    # ------- External, Editable Fields -------
    display_name = String(
        display_name="Display Name", 
        default="Graded Jupyter Notebook",
        scope=Scope.settings,
        help="Name of this XBlock" 
    )

    instructions = String(
        help="Instructions displayed to Student",
        scope=Scope.content,
        display_name="Student Instructions",
        multiline_editor=True,
    )

    max_attempts = Integer(
        help="Max number of allowed submissions (0 = unlimited)",
        scope=Scope.settings,
        display_name="Allowed Submissions",
        default=0
    )

    cell_timeout = Integer(
        help="Max seconds to wait for each cell to execute",
        scope=Scope.settings,
        display_name="Cell Timeout (s)",
        default=15
    )

    max_file_size = Integer(
        help="Max allowable file size of student uploaded file (Bytes)",
        scope=Scope.settings,
        display_name="Max File Size (B)",
        default=None
    )

    allow_network = Boolean (
        help="If True, allows network access from student notebook",
        scope=Scope.settings,
        display_name="Network Allowed",
        default=False
    )

    allow_graded_dl = Boolean (
        help="If True, allows student to download .html version of their autograded notebook",
        scope=Scope.settings,
        display_name="Allow Graded NB Download",
        default=False
    )

    # ------- Internal Fields -------
    nb_name = String(
        help="filename of the notebook",
        scope=Scope.settings,
        default=""
    )

    nb_upload_datetime = String(
        help="UTC datetime the notebook was uploaded",
        scope=Scope.settings,
        default=""
    )

    raw_possible = Float(
        help="Max possible score attainable",
        scope=Scope.settings,
        default=0.0
    )

    # ------- Internal Student Fields -------
    student_attempts = Integer(
        help="Number of times student has submitted problem",
        scope=Scope.user_state,
        default=0
    )

    student_score = Float(
        help="Student Score",
        scope=Scope.user_state,
        default=0
    )

    student_section_scores = List(
        help="Student Scores per section",
        scope=Scope.user_state,
        default=[]
    )

    student_submitted_dt = String(
        help="UTC datetime student last submitted notebook",
        scope=Scope.user_state,
        default=""
    )

    editable_fields = ('display_name', 'instructions', 'max_attempts', 
        'allow_network', 'cell_timeout', 'allow_graded_dl', 'max_file_size')

    # ----------- ScorableXBlockMixin Methods -----------
    def has_submitted_answer(self):
        return self.student_attempts > 0

    def get_score(self):
        return Score(raw_earned=self.student_score, 
            raw_possible=self.raw_possible)

    def set_score(self, score):
        self.student_score = score.raw_earned

    def calculate_score(self):
        return Score(raw_earned=self.student_score, 
            raw_possible=self.raw_possible)

    # ----------- Views -----------
    def student_view(self, context=None):
        """View shown to the students in the LMS"""
        # Setup student submitted datetime
        submitted_dt = "Not Yet Submitted"
        if self.student_submitted_dt:
            dt = dateparse.parse_datetime(self.student_submitted_dt)
            submitted_dt = dt.strftime("%Y-%m-%d %H:%M:%S") + " UTC"

        # Disable uploading inputs
        disabled_str = ''
        if self._is_past_due() or (self.max_attempts > 0 and self.student_attempts >= self.max_attempts):
            disabled_str = 'disabled'

        # HTML Template and Context
        ctx_data = {
            'title': self.display_name,
            'student_disabled': disabled_str,
            'nb_name': self.nb_name,
            'instructions': self.instructions,
            'max_attempts': self.max_attempts,
            'student_attempts': self.student_attempts,
            'student_score': self.student_score,
            'section_scores': self.student_section_scores,
            'max_score': "{:0.2f}".format(self.raw_possible),
            'submitted_dt': submitted_dt,
            'student_download_url': self._get_nb_url('student'),
            'xblock_id': self._get_xblock_loc(),
        }
        if self.allow_graded_dl and self.student_attempts > 0:
            ctx_data['autograded_url'] = self._get_nb_url('autograded')

        html = loader.render_django_template(
            'templates/xblock_jupyter_graded/student_view.html',
            ctx_data
        )

        frag = Fragment(html)
        frag.add_javascript(loader.load_unicode('/static/js/student.js'))
	frag.add_css(loader.load_unicode('static/css/styles.css'))
        frag.initialize_js('JupyterGradedXBlock', {'xblock_id': self._get_xblock_loc()})

        return frag
    
    def author_view(self, context=None):
        """View shown in the CMS XBlock preview"""
        # Setup last uploaded datetime
        upload_dt = ''
        if self.nb_upload_datetime:
            dt = dateparse.parse_datetime(self.nb_upload_datetime)
            upload_dt = dt.strftime("%Y-%m-%d %H:%M:%S") + " UTC"
        req = nbu.get_requirements(str(self.course_id))

        # HTML Template and Context
        ctx_data = {
            'title': self.display_name,
            'instructions': self.instructions,
            'requirements': req,
            'max_attempts': self.max_attempts,
            'student_attempts': self.student_attempts,
            'student_score': self.student_score,
            'max_score': "{:0.2f}".format(self.raw_possible),
            'nb_name': self.nb_name,
            'inst_disabled': 'disabled' if self.nb_name else '',
            'student_disabled': 'disabled',
            'nb_upload_date': upload_dt,
            'student_download_url': self._get_nb_url('student'),
            'instructor_download_url': self._get_nb_url('instructor'),
            'xblock_id': self._get_xblock_loc(),
        }
        html = loader.render_django_template('templates/xblock_jupyter_graded/author_view.html', ctx_data)

        frag = Fragment(html)
        frag.add_javascript(loader.load_unicode("/static/js/author.js"))
	frag.add_css(loader.load_unicode('static/css/styles.css'))
        frag.initialize_js('JupyterGradedXBlock', {'xblock_id': self._get_xblock_loc()})

        return frag

    # ----------- Handlers -----------
    @XBlock.handler
    def handle_instructor_nb_upload(self, request, suffix=u''):
        """Handles uploading an instructor notebook"""
        log.info("Handling instructor nb upload for course: {}, xblock: {}"\
            .format(str(self.course_id), str(self.location)))
        f = request.params['file']

        # Validate file upload
        error = self.validate_instructor_nb_upload(request)
        if error:
            return Response(body=json.dumps(error), 
                content_type="application/json", status=200);

	try:
            # Run Container to get max possible score and generate student 
            # version
            max_score = nbu.generate_student_nb(
                str(self.course_id), str(self.location), f) 
            self.raw_possible = max_score
            self.nb_name = f.filename
            submitted_dt = timezone.now()
            self.nb_upload_datetime = str(submitted_dt)

            # Set reasonable default max file size if one not set
            if self.max_file_size is None:
                self.max_file_size = self._get_default_max_file_size(request)

            response = {
                'success': True, 
                'max_score': "{:0.2f}".format(self.raw_possible),
                'nb_upload_date': submitted_dt.strftime("%Y-%m-%d %H:%M:%S") + " UTC",
                'nb_name': self.nb_name,
                'instructor_download_url': self._get_nb_url('instructor'),
                'student_download_url': self._get_nb_url('student')
                }

	except Exception as e:
            log.exception(e)
            response = {'success': False, 'error': str(e)}
    
        return Response(body=json.dumps(response), content_type="application/json", status=200);

    @XBlock.handler
    def handle_student_nb_upload(self, request, suffix=u''):
        """Handles uploading a student notebook"""
        log.info("Handling student nb upload for course: {}, xblock: {}"\
            .format(str(self.course_id), str(self.location)))
        # Handle empty file, wrong file type
        f = request.params['file']

        # Validate file upload
        error = self.validate_student_nb_upload(request)
        if error:
            return Response(body=json.dumps(error), 
                content_type="application/json", status=200);

        # Get User Info
        user_service = self.runtime.service(self, 'user')
        user = user_service.get_current_user()
        username = user.opt_attrs.get('edx-platform.username')

        # Score notebook and record grade
        try:
            
            scores = nbu.autograde_notebook(
                username, str(self.course_id), str(self.location), f,
                self.cell_timeout, self.allow_network) 
            self.student_attempts += 1
            edx_score = Score(raw_earned=scores['total'], raw_possible=self.raw_possible)
            self.set_score(edx_score)
            self._save_section_scores(scores['section_scores'])
            submitted_dt = timezone.now()
            self.student_submitted_dt = str(submitted_dt)
            self._publish_grade(edx_score)

            # Disable uploading inputs
            disable_uploads = False
            if self.max_attempts > 0 and self.student_attempts >= self.max_attempts:
                disable_uploads = True

            response = {
                'success': True,
                'score': "{:0.2f}".format(self.student_score),
                'attempts': self.student_attempts,
                'disable_uploads': disable_uploads,
                'section_scores': self._get_section_scores_html(),
                'autograded_err': scores.get('autograded_err'),
                'submitted_dt': submitted_dt.strftime("%Y-%m-%d %H:%M:%S") + " UTC",
            }

            # Add autograded_url if it should be shown
            if self.allow_graded_dl and self.student_attempts > 0:
                response['autograded_url'] = self._get_nb_url('autograded')

        except Exception as e:
            log.exception(e)
            response = {
                'success': False,
                'error': str(e)
            }

        return Response(body=json.dumps(response), 
                content_type="application/json", status=200);

    @XBlock.handler
    def handle_requirements_upload(self, request, suffix=u''):
        """Handles uploading of requirements.txt"""
        log.info("Handling requirements.txt upload for course: {}, xblock: {}"\
            .format(str(self.course_id), str(self.location)))
        try:
            f = request.params['file']
            nbu.update_requirements(str(self.course_id), f)
            req = nbu.get_requirements(str(self.course_id))
            response = {'success': True, 'requirements': "<br>".join(req)}

        except Exception as e:
            response = {'success': False, 'error': str(e)}

        return Response(body=json.dumps(response), 
                content_type="application/json", status=200);

    def validate_student_nb_upload(self, request):
        """Validate student notebook uploaded file"""
        f = request.params['file']
        response = {'success': False}


        # Check if file attached
        if not hasattr(f, 'filename'):
            response['error'] = "No File Attached"
        # Max file size
        elif f.file.size > self.max_file_size:
            response['error'] = "File ({:,} B) exceeds max allowed file size of {:,} B"\
                .format(f.file.size, self.max_file_size)
        # Check number of attempts
        elif self.max_attempts > 0 and self.student_attempts >= self.max_attempts:
            response['error'] = "Maximum allowed attempts reached"
        # Must end in .ipynb
        elif os.path.splitext(f.filename)[1] != '.ipynb':
            response['error'] = 'File extension must be .ipynb, not {}'\
                .format(os.path.splitext(f.filename)[1])
        # Notebook name must match
        elif not self.nb_name == f.filename:
            response['error'] = "Uploaded notebook ({}) must be named: {}"\
                .format(f.filename, self.nb_name)
        # Make sure it's not past due
        elif self._is_past_due():
            response['error'] = "Unable to submit past due date: {}".format(self.due)
        else:
            response = None

        return response

    def validate_instructor_nb_upload(self, request):
        """Validate instructor notebook uploaded file"""
        f = request.params['file']
        response = {'success': False}

        # Check if file attached
        if not hasattr(f, 'filename'):
            response['error'] = "No File Attached"
        # Check for proper extension
        elif os.path.splitext(f.filename)[1] != '.ipynb':
            response['error'] = 'File extension must be .ipynb, not {}'\
                .format(os.path.splitext(f.filename)[1])
        # Only allow nb to be uploaded once
        elif self.nb_name:
            response['error'] = "Notebook cannot be modified once it has "\
             "been uploaded".format(f.filename, self.nb_name)
        else:
            response = None

        return response

    def _get_nb_url(self, nb_type):
        """Return the URL to the appropriate nb download page"""
        url = None 

        if nb_type == 'student':
            name = 'jupyter_student_dl'
        elif nb_type == 'autograded':
            name = 'jupyter_autograded_dl'
        elif nb_type == 'instructor':
            name = 'jupyter_instructor_dl'
        else:
            # Will raise reverse error
            name = None

        # Only get link if notebook has been uploaded
        if self.nb_name:
            url = reverse(name, 
                kwargs={
                    'course_id': str(self.course_id), 
                    'unit_id': str(self.location),
                    'filename': os.path.splitext(self.nb_name)[0]
                }
            )

        return url


    def _get_xblock_loc(self):
        """Returns trailing number portion of self.location"""
        return str(self.location).split('@')[-1]

    def _get_default_max_file_size(self, request, default_addition=10000):
        """Returns file size `default_addition` B greater than instructor nb size"""
        f = request.params['file']
        return f.file.size + default_addition

    def _save_section_scores(self, section_scores):
        """Formats and saves section scores"""
        l = []
        for section in section_scores:
            d = {
                'name': section['name'],
                'score': section['auto_score'],
                'max_score': section['max_score'],
		'failed_tests': section['failed_tests']
            }
            l.append(d)
        self.student_section_scores = l

    def _get_section_scores_html(self):
        """Returns HTML string for section scores"""
        ctx_data = {'section_scores': self.student_section_scores}

        html = loader.render_django_template(
            'templates/xblock_jupyter_graded/section_scores.html',
            ctx_data
        )

        return html

    def _is_past_due(self):
        """Returns True if unit is past due"""
        if self.due is None:
            return False

        if timezone.now() > self.due:
            return True

    def max_score(self):
        """Return current max possible score"""
        return self.raw_possible


    # TO-DO: change this to create the scenarios you'd like to see in the
    # workbench while developing your XBlock.
    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("MyXBlock",
             """<myxblock/>
             """),
            ("Multiple MyXBlock",
             """<vertical_demo>
                <myxblock/>
                <myxblock/>
                <myxblock/>
                </vertical_demo>
             """),
        ]


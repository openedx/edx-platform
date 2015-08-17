import json
import logging
import re
import bleach
from html5lib.tokenizer import HTMLTokenizer
from xmodule.progress import Progress
import capa.xqueue_interface as xqueue_interface
from capa.util import *
from .peer_grading_service import PeerGradingService, MockPeerGradingService
import controller_query_service

from datetime import datetime
from pytz import UTC
from boto.s3.connection import S3Connection
from boto.s3.key import Key

log = logging.getLogger("edx.courseware")

# Set the default number of max attempts.  Should be 1 for production
# Set higher for debugging/testing
# attempts specified in xml definition overrides this.
MAX_ATTEMPTS = 1

# Set maximum available number of points.
# Overriden by max_score specified in xml.
MAX_SCORE = 1


def upload_to_s3(file_to_upload, keyname, s3_interface):
    '''
    Upload file to S3 using provided keyname.

    Returns:
        public_url: URL to access uploaded file
    '''

    conn = S3Connection(s3_interface['access_key'], s3_interface['secret_access_key'])
    bucketname = str(s3_interface['storage_bucket_name'])
    bucket = conn.lookup(bucketname.lower())
    if not bucket:
        bucket = conn.create_bucket(bucketname.lower())

    k = Key(bucket)
    k.key = keyname
    k.set_metadata('filename', file_to_upload.name)
    k.set_contents_from_file(file_to_upload)

    k.set_acl("public-read")
    public_url = k.generate_url(60 * 60 * 24 * 365)   # URL timeout in seconds.

    return public_url

# Used by sanitize_html
ALLOWED_HTML_ATTRS = {
    '*': ['id', 'class', 'height', 'width', 'alt'],
    'a': ['href', 'title', 'rel', 'target'],
    'embed': ['src'],
    'iframe': ['src'],
    'img': ['src'],
}


class OpenEndedChild(object):
    """
    States:

    initial (prompt, textbox shown)
         |
    assessing (read-only textbox, rubric + assessment input shown for self assessment, response queued for open ended)
         |
    post_assessment (read-only textbox, read-only rubric and assessment, hint input box shown)
         |
    done (submitted msg, green checkmark, everything else read-only.  If attempts < max, shows
         a reset button that goes back to initial state.  Saves previous
         submissions too.)
    """

    DEFAULT_QUEUE = 'open-ended'
    DEFAULT_MESSAGE_QUEUE = 'open-ended-message'
    max_inputfields = 1

    STATE_VERSION = 1

    # states
    INITIAL = 'initial'
    ASSESSING = 'assessing'
    POST_ASSESSMENT = 'post_assessment'
    DONE = 'done'

    # This is used to tell students where they are at in the module
    _ = lambda text: text
    HUMAN_NAMES = {
        # Translators: "Not started" communicates to a student that their response
        # has not yet been graded
        'initial': _('Not started'),
        # Translators: "In progress" communicates to a student that their response
        # is currently in the grading process
        'assessing': _('In progress'),
        # Translators: "Done" communicates to a student that their response
        # has been fully graded
        'post_assessment': _('Done'),
        'done': _('Done'),
    }

    # included to make this act enough like an xblock to get i18n
    _services_requested = {"i18n": "need"}
    _combined_services = _services_requested

    def __init__(self, system, location, definition, descriptor, static_data,
                 instance_state=None, shared_state=None, **kwargs):
        # Load instance state

        if instance_state is not None:
            try:
                instance_state = json.loads(instance_state)
            except:
                log.error(
                    "Could not load instance state for open ended.  Setting it to nothing.: {0}".format(instance_state))
                instance_state = {}
        else:
            instance_state = {}

        # History is a list of tuples of (answer, score, hint), where hint may be
        # None for any element, and score and hint can be None for the last (current)
        # element.
        # Scores are on scale from 0 to max_score

        self.child_history = instance_state.get('child_history', [])
        self.child_state = instance_state.get('child_state', self.INITIAL)
        self.child_created = instance_state.get('child_created', False)
        self.child_attempts = instance_state.get('child_attempts', 0)
        self.stored_answer = instance_state.get('stored_answer', None)

        self.max_attempts = static_data['max_attempts']
        self.child_prompt = static_data['prompt']
        self.child_rubric = static_data['rubric']
        self.display_name = static_data['display_name']
        self.accept_file_upload = static_data['accept_file_upload']
        self.close_date = static_data['close_date']
        self.s3_interface = static_data['s3_interface']
        self.skip_basic_checks = static_data['skip_basic_checks']
        self._max_score = static_data['max_score']
        self.control = static_data['control']

        # Used for progress / grading.  Currently get credit just for
        # completion (doesn't matter if you self-assessed correct/incorrect).
        if system.open_ended_grading_interface:
            self.peer_gs = PeerGradingService(system.open_ended_grading_interface, system.render_template)
            self.controller_qs = controller_query_service.ControllerQueryService(
                system.open_ended_grading_interface, system.render_template
            )
        else:
            self.peer_gs = MockPeerGradingService()
            self.controller_qs = None

        self.system = system

        self.location_string = location
        try:
            self.location_string = self.location_string.to_deprecated_string()
        except:
            pass

        self.setup_response(system, location, definition, descriptor)

    def setup_response(self, system, location, definition, descriptor):
        """
        Needs to be implemented by the inheritors of this module.  Sets up additional fields used by the child modules.
        @param system: Modulesystem
        @param location: Module location
        @param definition: XML definition
        @param descriptor: Descriptor of the module
        @return: None
        """
        pass

    def closed(self):
        if self.close_date is not None and datetime.now(UTC) > self.close_date:
            return True
        return False

    def check_if_closed(self):
        if self.closed():
            return True, {
                'success': False,
                # This is a student_facing_error
                'error': 'The problem close date has passed, and this problem is now closed.'
            }
        elif self.child_attempts > self.max_attempts:
            return True, {
                'success': False,
                # This is a student_facing_error
                'error': 'You have attempted this problem {0} times.  You are allowed {1} attempts.'.format(
                    self.child_attempts, self.max_attempts
                )
            }
        else:
            return False, {}

    def latest_answer(self):
        """Empty string if not available"""
        if not self.child_history:
            return ""
        return self.child_history[-1].get('answer', "")

    def latest_score(self):
        """None if not available"""
        if not self.child_history:
            return None
        return self.child_history[-1].get('score')

    def all_scores(self):
        """None if not available"""
        if not self.child_history:
            return None
        return [child_hist.get('score') for child_hist in self.child_history]

    def latest_post_assessment(self, system):
        """Empty string if not available"""
        if not self.child_history:
            return ""
        return self.child_history[-1].get('post_assessment', "")

    @staticmethod
    def sanitize_html(answer):
        """
        Take a student response and sanitize the HTML to prevent malicious script injection
        or other unwanted content.
        answer - any string
        return - a cleaned version of the string
        """
        clean_html = bleach.clean(answer,
                                  tags=['embed', 'iframe', 'a', 'img', 'br'],
                                  attributes=ALLOWED_HTML_ATTRS,
                                  strip=True)
        autolinked = bleach.linkify(clean_html,
                                    callbacks=[bleach.callbacks.target_blank],
                                    skip_pre=True,
                                    tokenizer=HTMLTokenizer)
        return OpenEndedChild.replace_newlines(autolinked)

    @staticmethod
    def replace_newlines(html):
        """
        Replaces "\n" newlines with <br/>
        """
        retv = re.sub(r'</p>$', '', re.sub(r'^<p>', '', html))
        return re.sub("\n", "<br/>", retv)

    def new_history_entry(self, answer):
        """
        Adds a new entry to the history dictionary
        @param answer: The student supplied answer
        @return: None
        """
        answer = OpenEndedChild.sanitize_html(answer)
        self.child_history.append({'answer': answer})
        self.stored_answer = None

    def record_latest_score(self, score):
        """Assumes that state is right, so we're adding a score to the latest
        history element"""
        self.child_history[-1]['score'] = score

    def record_latest_post_assessment(self, post_assessment):
        """Assumes that state is right, so we're adding a score to the latest
        history element"""
        self.child_history[-1]['post_assessment'] = post_assessment

    def change_state(self, new_state):
        """
        A centralized place for state changes--allows for hooks.  If the
        current state matches the old state, don't run any hooks.
        """
        if self.child_state == new_state:
            return

        self.child_state = new_state

        if self.child_state == self.DONE:
            self.child_attempts += 1

    def get_instance_state(self):
        """
        Get the current score and state
        """

        state = {
            'version': self.STATE_VERSION,
            'child_history': self.child_history,
            'child_state': self.child_state,
            'max_score': self._max_score,
            'child_attempts': self.child_attempts,
            'child_created': self.child_created,
            'stored_answer': self.stored_answer,
        }
        return json.dumps(state)

    def _allow_reset(self):
        """Can the module be reset?"""
        return (self.child_state == self.DONE and self.child_attempts < self.max_attempts)

    def max_score(self):
        """
        Return max_score
        """
        return self._max_score

    def get_score(self):
        """
        Returns the last score in the list
        """
        score = self.latest_score()
        return {'score': score if score is not None else 0,
                'total': self._max_score}

    def reset(self, system):
        """
        If resetting is allowed, reset the state.

        Returns {'success': bool, 'error': msg}
        (error only present if not success)
        """
        self.change_state(self.INITIAL)
        return {'success': True}

    def get_display_answer(self):
        latest = self.latest_answer()
        if self.child_state == self.INITIAL:
            if self.stored_answer is not None:
                previous_answer = self.stored_answer
            elif latest is not None and len(latest) > 0:
                previous_answer = latest
            else:
                previous_answer = ""
            previous_answer = previous_answer.replace("<br/>", "\n").replace("<br>", "\n")
        else:
            if latest is not None and len(latest) > 0:
                previous_answer = latest
            else:
                previous_answer = ""
            previous_answer = previous_answer.replace("\n", "<br/>")

        return previous_answer

    def store_answer(self, data, system):
        if self.child_state != self.INITIAL:
            # We can only store an answer if the problem has not moved into the assessment phase.
            return self.out_of_sync_error(data)

        self.stored_answer = data['student_answer']
        return {'success': True}

    def get_progress(self):
        '''
        For now, just return last score / max_score
        '''
        if self._max_score > 0:
            try:
                return Progress(int(self.get_score()['score']), int(self._max_score))
            except Exception as err:
                # This is a dev_facing_error
                log.exception("Got bad progress from open ended child module. Max Score: {0}".format(self._max_score))
                return None
        return None

    def out_of_sync_error(self, data, msg=''):
        """
        return dict out-of-sync error message, and also log.
        """
        # This is a dev_facing_error
        log.warning("Open ended child state out sync. state: %r, data: %r. %s",
                    self.child_state, data, msg)
        # This is a student_facing_error
        return {'success': False,
                'error': 'The problem state got out-of-sync.  Please try reloading the page.'}

    def get_html(self):
        """
         Needs to be implemented by inheritors.  Renders the HTML that students see.
        @return:
        """
        pass

    def handle_ajax(self):
        """
        Needs to be implemented by child modules.  Handles AJAX events.
        @return:
        """
        pass

    def is_submission_correct(self, score):
        """
        Checks to see if a given score makes the answer correct.  Very naive right now (>66% is correct)
        @param score: Numeric score.
        @return: Boolean correct.
        """
        correct = False
        if (isinstance(score, (int, long, float, complex))):
            score_ratio = int(score) / float(self.max_score())
            correct = (score_ratio >= 0.66)
        return correct

    def is_last_response_correct(self):
        """
        Checks to see if the last response in the module is correct.
        @return: 'correct' if correct, otherwise 'incorrect'
        """
        score = self.get_score()['score']
        correctness = 'correct' if self.is_submission_correct(score) else 'incorrect'
        return correctness

    def upload_file_to_s3(self, file_data):
        """
        Uploads a file to S3.
        file_data: InMemoryUploadedFileObject that responds to read() and seek().
        @return: A URL corresponding to the uploaded object.
        """

        file_key = file_data.name + datetime.now(UTC).strftime(
            xqueue_interface.dateformat
        )

        file_data.seek(0)
        s3_public_url = upload_to_s3(
            file_data, file_key, self.s3_interface
        )

        return s3_public_url

    def check_for_file_and_upload(self, data):
        """
        Checks to see if a file was passed back by the student.  If so, it will be uploaded to S3.
        @param data: AJAX post dictionary containing keys student_file and valid_files_attached.
        @return: has_file_to_upload, whether or not a file was in the data dictionary,
        and image_tag, the html needed to create a link to the uploaded file.
        """
        has_file_to_upload = False
        image_tag = ""

        # Ensure that a valid file was uploaded.
        if 'valid_files_attached' in data and \
           data['valid_files_attached'] in ['true', '1', True] and \
           data['student_file'] is not None and \
           len(data['student_file']) > 0:
            has_file_to_upload = True
            student_file = data['student_file'][0]

            # Upload the file to S3 and generate html to embed a link.
            s3_public_url = self.upload_file_to_s3(student_file)
            image_tag = self.generate_file_link_html_from_url(s3_public_url, student_file.name)

        return has_file_to_upload, image_tag

    def generate_file_link_html_from_url(self, s3_public_url, file_name):
        """
        Create an html link to a given URL.
        @param s3_public_url: URL of the file.
        @param file_name: Name of the file.
        @return: Boolean success, updated AJAX data.
        """
        image_link = """
                        <a href="{0}" target="_blank">{1}</a>
                         """.format(s3_public_url, file_name)
        return image_link

    def append_file_link_to_student_answer(self, data):
        """
        Adds a file to a student answer after uploading it to S3.
        @param data: AJAX data containing keys student_answer, valid_files_attached, and student_file.
        @return: Boolean success, and updated AJAX data dictionary.
        """

        _ = self.system.service(self, "i18n").ugettext

        error_message = ""

        if not self.accept_file_upload:
            # If the question does not accept file uploads, do not do anything
            return True, error_message, data

        try:
            # Try to upload the file to S3.
            has_file_to_upload, image_tag = self.check_for_file_and_upload(data)
            data['student_answer'] += image_tag
            success = True
            if not has_file_to_upload:
                # If there is no file to upload, probably the student has embedded the link in the answer text
                success, data['student_answer'] = self.check_for_url_in_text(data['student_answer'])

                # If success is False, we have not found a link, and no file was attached.
                # Show error to student.
                if success is False:
                    error_message = _(
                        "We could not find a file in your submission. "
                        "Please try choosing a file or pasting a URL to your "
                        "file into the answer box."
                    )

        except Exception:
            # In this case, an image was submitted by the student, but the image could not be uploaded to S3.  Likely
            # a config issue (development vs deployment).
            log.exception("Student AJAX post to combined open ended xmodule indicated that it contained a file, "
                          "but the image was not able to be uploaded to S3.  This could indicate a configuration "
                          "issue with this deployment and the S3_INTERFACE setting.")
            success = False
            error_message = _(
                "We are having trouble saving your file. Please try another "
                "file or paste a URL to your file into the answer box."
            )

        return success, error_message, data

    def check_for_url_in_text(self, string):
        """
        Checks for urls in a string.
        @param string: Arbitrary string.
        @return: Boolean success, and the edited string.
        """
        has_link = False

        # Find all links in the string.
        links = re.findall(r'(https?://\S+)', string)
        if len(links) > 0:
            has_link = True

        # Autolink by wrapping links in anchor tags.
        for link in links:
            string = re.sub(link, self.generate_file_link_html_from_url(link, link), string)

        return has_link, string

    def get_eta(self):
        if self.controller_qs:
            response = self.controller_qs.check_for_eta(self.location_string)
        else:
            return ""

        success = response['success']
        if isinstance(success, basestring):
            success = (success.lower() == "true")

        if success:
            eta = controller_query_service.convert_seconds_to_human_readable(response['eta'])
            eta_string = "Please check back for your response in at most {0}.".format(eta)
        else:
            eta_string = ""

        return eta_string

    @classmethod
    def service_declaration(cls, service_name):
        """
        This classmethod is copied from XBlock's service_declaration.
        It is included to make this class act enough like an XBlock
        to get i18n working on it.

        This is currently only used for i18n, and will return "need"
        in that case.

        Arguments:
            service_name (string): the name of the service requested.

        Returns:
            One of "need", "want", or None.

        """
        declaration = cls._combined_services.get(service_name)
        return declaration

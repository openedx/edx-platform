import json
import logging
from lxml.html.clean import Cleaner, autolink_html
import re

import open_ended_image_submission
from xmodule.progress import Progress
import capa.xqueue_interface as xqueue_interface
from capa.util import *
from .peer_grading_service import PeerGradingService, MockPeerGradingService
import controller_query_service

from datetime import datetime
from django.utils.timezone import UTC

log = logging.getLogger("mitx.courseware")

# Set the default number of max attempts.  Should be 1 for production
# Set higher for debugging/testing
# attempts specified in xml definition overrides this.
MAX_ATTEMPTS = 1

# Set maximum available number of points.
# Overriden by max_score specified in xml.
MAX_SCORE = 1


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
    HUMAN_NAMES = {
        'initial': 'Not started',
        'assessing': 'In progress',
        'post_assessment': 'Done',
        'done': 'Done',
    }

    def __init__(self, system, location, definition, descriptor, static_data,
                 instance_state=None, shared_state=None, **kwargs):
        # Load instance state

        if instance_state is not None:
            try:
                instance_state = json.loads(instance_state)
            except:
                log.error(
                    "Could not load instance state for open ended.  Setting it to nothing.: {0}".format(instance_state))
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

        self.max_attempts = static_data['max_attempts']
        self.child_prompt = static_data['prompt']
        self.child_rubric = static_data['rubric']
        self.display_name = static_data['display_name']
        self.accept_file_upload = static_data['accept_file_upload']
        self.close_date = static_data['close_date']
        self.s3_interface = static_data['s3_interface']
        self.skip_basic_checks = static_data['skip_basic_checks']
        self._max_score = static_data['max_score']

        # Used for progress / grading.  Currently get credit just for
        # completion (doesn't matter if you self-assessed correct/incorrect).
        if system.open_ended_grading_interface:
            self.peer_gs = PeerGradingService(system.open_ended_grading_interface, system)
            self.controller_qs = controller_query_service.ControllerQueryService(
                system.open_ended_grading_interface, system
            )
        else:
            self.peer_gs = MockPeerGradingService()
            self.controller_qs = None

        self.system = system

        self.location_string = location
        try:
            self.location_string = self.location_string.url()
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
        if self.close_date is not None and datetime.now(UTC()) > self.close_date:
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
        return [self.child_history[i].get('score') for i in xrange(0, len(self.child_history))]

    def latest_post_assessment(self, system):
        """Empty string if not available"""
        if not self.child_history:
            return ""
        return self.child_history[-1].get('post_assessment', "")

    @staticmethod
    def sanitize_html(answer):
        try:
            answer = autolink_html(answer)
            cleaner = Cleaner(style=True, links=True, add_nofollow=False, page_structure=True, safe_attrs_only=True,
                              host_whitelist=open_ended_image_submission.TRUSTED_IMAGE_DOMAINS,
                              whitelist_tags=set(['embed', 'iframe', 'a', 'img']))
            clean_html = cleaner.clean_html(answer)
            clean_html = re.sub(r'</p>$', '', re.sub(r'^<p>', '', clean_html))
        except:
            clean_html = answer
        return clean_html

    def new_history_entry(self, answer):
        """
        Adds a new entry to the history dictionary
        @param answer: The student supplied answer
        @return: None
        """
        answer = OpenEndedChild.sanitize_html(answer)
        self.child_history.append({'answer': answer})

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
            'child_created': False,
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

    def upload_image_to_s3(self, image_data):
        """
        Uploads an image to S3
        Image_data: InMemoryUploadedFileObject that responds to read() and seek()
        @return:Success and a URL corresponding to the uploaded object
        """
        success = False
        s3_public_url = ""
        image_ok = False
        try:
            image_data.seek(0)
            image_ok = open_ended_image_submission.run_image_tests(image_data)
        except:
            log.exception("Could not create image and check it.")

        if image_ok:
            image_key = image_data.name + datetime.now(UTC).strftime(
                xqueue_interface.dateformat
            )

            try:
                image_data.seek(0)
                success, s3_public_url = open_ended_image_submission.upload_to_s3(
                    image_data, image_key, self.s3_interface
                )
            except:
                log.exception("Could not upload image to S3.")

        return success, image_ok, s3_public_url

    def check_for_image_and_upload(self, data):
        """
        Checks to see if an image was passed back in the AJAX query.  If so, it will upload it to S3
        @param data: AJAX data
        @return: Success, whether or not a file was in the data dictionary,
        and the html corresponding to the uploaded image
        """
        has_file_to_upload = False
        uploaded_to_s3 = False
        image_tag = ""
        image_ok = False
        if 'can_upload_files' in data:
            if data['can_upload_files'] in ['true', '1']:
                has_file_to_upload = True
                student_file = data['student_file'][0]
                uploaded_to_s3, image_ok, s3_public_url = self.upload_image_to_s3(student_file)
                if uploaded_to_s3:
                    image_tag = self.generate_image_tag_from_url(s3_public_url, student_file.name)

        return has_file_to_upload, uploaded_to_s3, image_ok, image_tag

    def generate_image_tag_from_url(self, s3_public_url, image_name):
        """
        Makes an image tag from a given URL
        @param s3_public_url: URL of the image
        @param image_name: Name of the image
        @return: Boolean success, updated AJAX data
        """
        image_template = """
                        <a href="{0}" target="_blank">{1}</a>
                         """.format(s3_public_url, image_name)
        return image_template

    def append_image_to_student_answer(self, data):
        """
        Adds an image to a student answer after uploading it to S3
        @param data: AJAx data
        @return: Boolean success, updated AJAX data
        """
        overall_success = False
        if not self.accept_file_upload:
            # If the question does not accept file uploads, do not do anything
            return True, data

        has_file_to_upload, uploaded_to_s3, image_ok, image_tag = self.check_for_image_and_upload(data)
        if uploaded_to_s3 and has_file_to_upload and image_ok:
            data['student_answer'] += image_tag
            overall_success = True
        elif has_file_to_upload and not uploaded_to_s3 and image_ok:
            # In this case, an image was submitted by the student, but the image could not be uploaded to S3.  Likely
            # a config issue (development vs deployment).  For now, just treat this as a "success"
            log.exception("Student AJAX post to combined open ended xmodule indicated that it contained an image, "
                          "but the image was not able to be uploaded to S3.  This could indicate a config"
                          "issue with this deployment, but it could also indicate a problem with S3 or with the"
                          "student image itself.")
            overall_success = True
        elif not has_file_to_upload:
            # If there is no file to upload, probably the student has embedded the link in the answer text
            success, data['student_answer'] = self.check_for_url_in_text(data['student_answer'])
            overall_success = success

        # log.debug("Has file: {0} Uploaded: {1} Image Ok: {2}".format(has_file_to_upload, uploaded_to_s3, image_ok))

        return overall_success, data

    def check_for_url_in_text(self, string):
        """
        Checks for urls in a string
        @param string: Arbitrary string
        @return: Boolean success, the edited string
        """
        success = False
        links = re.findall(r'(https?://\S+)', string)
        if len(links) > 0:
            for link in links:
                success = open_ended_image_submission.run_url_tests(link)
                if not success:
                    string = re.sub(link, '', string)
                else:
                    string = re.sub(link, self.generate_image_tag_from_url(link, link), string)
                    success = True

        return success, string

    def check_if_student_can_submit(self):
        location = self.location_string

        student_id = self.system.anonymous_student_id
        success = False
        allowed_to_submit = True
        response = {}
        # This is a student_facing_error
        error_string = ("You need to peer grade {0} more in order to make another submission.  "
                        "You have graded {1}, and {2} are required.  You have made {3} successful peer grading submissions.")
        try:
            response = self.peer_gs.get_data_for_location(self.location_string, student_id)
            count_graded = response['count_graded']
            count_required = response['count_required']
            student_sub_count = response['student_sub_count']
            success = True
        except:
            # This is a dev_facing_error
            log.error("Could not contact external open ended graders for location {0} and student {1}".format(
                self.location_string, student_id))
            # This is a student_facing_error
            error_message = "Could not contact the graders.  Please notify course staff."
            return success, allowed_to_submit, error_message
        if count_graded >= count_required:
            return success, allowed_to_submit, ""
        else:
            allowed_to_submit = False
            # This is a student_facing_error
            error_message = error_string.format(count_required - count_graded, count_graded, count_required,
                                                student_sub_count)
            return success, allowed_to_submit, error_message

    def get_eta(self):
        if self.controller_qs:
            response = self.controller_qs.check_for_eta(self.location_string)
            try:
                response = json.loads(response)
            except:
                pass
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

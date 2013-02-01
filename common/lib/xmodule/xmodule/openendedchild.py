import copy
from fs.errors import ResourceNotFoundError
import itertools
import json
import logging
from lxml import etree
from lxml.html import rewrite_links
from lxml.html.clean import Cleaner, autolink_html
from path import path
import os
import sys
import hashlib
import capa.xqueue_interface as xqueue_interface
import re

from pkg_resources import resource_string

from .capa_module import only_one, ComplexEncoder
from .editing_module import EditingDescriptor
from .html_checker import check_html
from progress import Progress
from .stringify import stringify_children
from .xml_module import XmlDescriptor
from xmodule.modulestore import Location
from capa.util import *
import open_ended_image_submission

from datetime import datetime

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

    #This is used to tell students where they are at in the module
    HUMAN_NAMES = {
        'initial': 'Started',
        'assessing': 'Being scored',
        'post_assessment': 'Scoring finished',
        'done': 'Problem complete',
    }

    def __init__(self, system, location, definition, descriptor, static_data,
                 instance_state=None, shared_state=None, **kwargs):
        # Load instance state
        if instance_state is not None:
            instance_state = json.loads(instance_state)
        else:
            instance_state = {}

        # History is a list of tuples of (answer, score, hint), where hint may be
        # None for any element, and score and hint can be None for the last (current)
        # element.
        # Scores are on scale from 0 to max_score
        self.history = instance_state.get('history', [])

        self.state = instance_state.get('state', self.INITIAL)

        self.created = instance_state.get('created', False)

        self.attempts = instance_state.get('attempts', 0)
        self.max_attempts = static_data['max_attempts']

        self.prompt = static_data['prompt']
        self.rubric = static_data['rubric']
        self.display_name = static_data['display_name']
        self.accept_file_upload = static_data['accept_file_upload']

        # Used for progress / grading.  Currently get credit just for
        # completion (doesn't matter if you self-assessed correct/incorrect).
        self._max_score = static_data['max_score']

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

    def latest_answer(self):
        """Empty string if not available"""
        if not self.history:
            return ""
        return self.history[-1].get('answer', "")

    def latest_score(self):
        """None if not available"""
        if not self.history:
            return None
        return self.history[-1].get('score')

    def latest_post_assessment(self, system):
        """Empty string if not available"""
        if not self.history:
            return ""
        return self.history[-1].get('post_assessment', "")

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
        self.history.append({'answer': answer})

    def record_latest_score(self, score):
        """Assumes that state is right, so we're adding a score to the latest
        history element"""
        self.history[-1]['score'] = score

    def record_latest_post_assessment(self, post_assessment):
        """Assumes that state is right, so we're adding a score to the latest
        history element"""
        self.history[-1]['post_assessment'] = post_assessment

    def change_state(self, new_state):
        """
        A centralized place for state changes--allows for hooks.  If the
        current state matches the old state, don't run any hooks.
        """
        if self.state == new_state:
            return

        self.state = new_state

        if self.state == self.DONE:
            self.attempts += 1

    def get_instance_state(self):
        """
        Get the current score and state
        """

        state = {
            'version': self.STATE_VERSION,
            'history': self.history,
            'state': self.state,
            'max_score': self._max_score,
            'attempts': self.attempts,
            'created': False,
        }
        return json.dumps(state)

    def _allow_reset(self):
        """Can the module be reset?"""
        return (self.state == self.DONE and self.attempts < self.max_attempts)

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
                return Progress(self.get_score()['score'], self._max_score)
            except Exception as err:
                log.exception("Got bad progress")
                return None
        return None

    def out_of_sync_error(self, get, msg=''):
        """
        return dict out-of-sync error message, and also log.
        """
        log.warning("Assessment module state out sync. state: %r, get: %r. %s",
            self.state, get, msg)
        return {'success': False,
                'error': 'The problem state got out-of-sync'}

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
        if(isinstance(score, (int, long, float, complex))):
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
            image_key = image_data.name + datetime.now().strftime("%Y%m%d%H%M%S")

            try:
                image_data.seek(0)
                success, s3_public_url = open_ended_image_submission.upload_to_s3(image_data, image_key)
            except:
                log.exception("Could not upload image to S3.")

        return success, image_ok, s3_public_url

    def check_for_image_and_upload(self, get_data):
        """
        Checks to see if an image was passed back in the AJAX query.  If so, it will upload it to S3
        @param get_data: AJAX get data
        @return: Success, whether or not a file was in the get dictionary,
        and the html corresponding to the uploaded image
        """
        has_file_to_upload = False
        uploaded_to_s3 = False
        image_tag = ""
        image_ok = False
        if 'can_upload_files' in get_data:
            if get_data['can_upload_files'] == 'true':
                has_file_to_upload = True
                file = get_data['student_file'][0]
                uploaded_to_s3, image_ok, s3_public_url = self.upload_image_to_s3(file)
                if uploaded_to_s3:
                    image_tag = self.generate_image_tag_from_url(s3_public_url, file.name)

        return has_file_to_upload, uploaded_to_s3, image_ok, image_tag

    def generate_image_tag_from_url(self, s3_public_url, image_name):
        """
        Makes an image tag from a given URL
        @param s3_public_url: URL of the image
        @param image_name: Name of the image
        @return: Boolean success, updated AJAX get data
        """
        image_template = """
                        <a href="{0}" target="_blank">{1}</a>
                         """.format(s3_public_url, image_name)
        return image_template

    def append_image_to_student_answer(self, get_data):
        """
        Adds an image to a student answer after uploading it to S3
        @param get_data: AJAx get data
        @return: Boolean success, updated AJAX get data
        """
        overall_success = False
        if not self.accept_file_upload:
            #If the question does not accept file uploads, do not do anything
            return True, get_data

        has_file_to_upload, uploaded_to_s3, image_ok, image_tag = self.check_for_image_and_upload(get_data)
        if uploaded_to_s3 and has_file_to_upload and image_ok:
            get_data['student_answer'] += image_tag
            overall_success = True
        elif has_file_to_upload and not uploaded_to_s3 and image_ok:
            #In this case, an image was submitted by the student, but the image could not be uploaded to S3.  Likely
            #a config issue (development vs deployment).  For now, just treat this as a "success"
            log.warning("Student AJAX post to combined open ended xmodule indicated that it contained an image, "
                        "but the image was not able to be uploaded to S3.  This could indicate a config"
                        "issue with this deployment, but it could also indicate a problem with S3 or with the"
                        "student image itself.")
            overall_success = True
        elif not has_file_to_upload:
            #If there is no file to upload, probably the student has embedded the link in the answer text
            success, get_data['student_answer'] = self.check_for_url_in_text(get_data['student_answer'])
            overall_success = success

        return overall_success, get_data

    def check_for_url_in_text(self, string):
        """
        Checks for urls in a string
        @param string: Arbitrary string
        @return: Boolean success, the edited string
        """
        success = False
        links = re.findall(r'(https?://\S+)', string)
        if len(links)>0:
            for link in links:
                success = open_ended_image_submission.run_url_tests(link)
                if not success:
                    string = re.sub(link, '', string)
                else:
                    string = re.sub(link, self.generate_image_tag_from_url(link,link), string)
                    success = True

        return success, string






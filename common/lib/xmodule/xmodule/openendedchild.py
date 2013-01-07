"""
A Self Assessment module that allows students to write open-ended responses,
submit, then see a rubric and rate themselves.  Persists student supplied
hints, answers, and assessment judgment (currently only correct/incorrect).
Parses xml definition file--see below for exact format.
"""

import copy
from fs.errors import ResourceNotFoundError
import itertools
import json
import logging
from lxml import etree
from lxml.html import rewrite_links
from path import path
import os
import sys
import hashlib
import capa.xqueue_interface as xqueue_interface

from pkg_resources import resource_string

from .capa_module import only_one, ComplexEncoder
from .editing_module import EditingDescriptor
from .html_checker import check_html
from progress import Progress
from .stringify import stringify_children
from .xml_module import XmlDescriptor
from xmodule.modulestore import Location
from capa.util import *

from datetime import datetime

log = logging.getLogger("mitx.courseware")

# Set the default number of max attempts.  Should be 1 for production
# Set higher for debugging/testing
# attempts specified in xml definition overrides this.
MAX_ATTEMPTS = 1

# Set maximum available number of points.
# Overriden by max_score specified in xml.
MAX_SCORE = 1

class OpenEndedChild():
    """
    States:

    initial (prompt, textbox shown)
         |
    assessing (read-only textbox, rubric + assessment input shown)
         |
    request_hint (read-only textbox, read-only rubric and assessment, hint input box shown)
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

    def __init__(self, system, location, definition, descriptor,
                 instance_state=None, shared_state=None, **kwargs):
        """
        Definition file should have 4 blocks -- prompt, rubric, submitmessage, hintprompt,
        and two optional attributes:
        attempts, which should be an integer that defaults to 1.
        If it's > 1, the student will be able to re-submit after they see
        the rubric.
        max_score, which should be an integer that defaults to 1.
        It defines the maximum number of points a student can get.  Assumed to be integer scale
        from 0 to max_score, with an interval of 1.

        Note: all the submissions are stored.

        Sample file:

        <selfassessment attempts="1" max_score="1">
            <prompt>
                Insert prompt text here.  (arbitrary html)
            </prompt>
            <rubric>
                Insert grading rubric here.  (arbitrary html)
            </rubric>
            <hintprompt>
                Please enter a hint below: (arbitrary html)
            </hintprompt>
            <submitmessage>
                Thanks for submitting!  (arbitrary html)
            </submitmessage>
        </selfassessment>
        """

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

        self.state = instance_state.get('state', 'initial')

        self.created = instance_state.get('created', "False")

        self.attempts = instance_state.get('attempts', 0)
        self.max_attempts = int(instance_state.get('attempts', MAX_ATTEMPTS))

        # Used for progress / grading.  Currently get credit just for
        # completion (doesn't matter if you self-assessed correct/incorrect).
        self._max_score = int(instance_state.get('max_score', MAX_SCORE))

        self.setup_response(system, location, definition, descriptor)

    def setup_response(self, system, location, definition, descriptor):
        pass

    def latest_answer(self):
        """None if not available"""
        if not self.history:
            return ""
        return self.history[-1].get('answer', "")

    def latest_score(self):
        """None if not available"""
        if not self.history:
            return None
        return self.history[-1].get('score')

    def latest_post_assessment(self):
        """None if not available"""
        if not self.history:
            return ""
        return self.history[-1].get('post_assessment', "")

    def new_history_entry(self, answer):
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
            'created' : "False",
            }
        return json.dumps(state)

    def _allow_reset(self):
        """Can the module be reset?"""
        return self.state == self.DONE and self.attempts < self.max_attempts

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




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

from pkg_resources import resource_string

from .capa_module import only_one, ComplexEncoder
from .editing_module import EditingDescriptor
from .html_checker import check_html
from progress import Progress
from .stringify import stringify_children
from .x_module import XModule
from .xml_module import XmlDescriptor
from xmodule.modulestore import Location

log = logging.getLogger("mitx.courseware")

# Set the default number of max attempts.  Should be 1 for production
# Set higher for debugging/testing
# attempts specified in xml definition overrides this.
MAX_ATTEMPTS = 1

# Set maximum available number of points.
# Overriden by max_score specified in xml.
MAX_SCORE = 1

class OpenEndedModule():
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
    response_tag = 'openendedresponse'
    allowed_inputfields = ['openendedinput']
    max_inputfields = 1

    STATE_VERSION = 1

    # states
    INITIAL = 'initial'
    ASSESSING = 'assessing'
    REQUEST_HINT = 'post_assessment'
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

        instance_state = self.convert_state_to_current_format(instance_state)

        # History is a list of tuples of (answer, score, hint), where hint may be
        # None for any element, and score and hint can be None for the last (current)
        # element.
        # Scores are on scale from 0 to max_score
        self.history = instance_state.get('history', [])

        self.state = instance_state.get('state', 'initial')

        self.attempts = instance_state.get('attempts', 0)
        self.max_attempts = int(instance_state.get('attempts', MAX_ATTEMPTS))

        # Used for progress / grading.  Currently get credit just for
        # completion (doesn't matter if you self-assessed correct/incorrect).
        self._max_score = int(instance_state.get('max_score', MAX_SCORE))

        self.rubric = definition['rubric']
        self.prompt = definition['prompt']
        self.submit_message = definition['submitmessage']
        self.hint_prompt = definition['hintprompt']
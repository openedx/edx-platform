"""
Deals with auto-reporting of discussion posts that contain
profanity or otherwise naughty words or phrases.
"""

from collections import Counter
import json
import logging
import os
import re

from django.contrib.auth.models import User
from opaque_keys.edx.keys import CourseKey

import lms.lib.comment_client as cc


log = logging.getLogger(__name__)


def load_words():
    """
    Returns a dictionary loaded from the `badwords-en.json` file of the form:

    {
        'crud': {
            'score': 1,
            'auto_flag': False,
        },
        'fiddlesticks': {
            'score': 3,
            'auto_flag': True
        },
        ...
    }

    where the 'score' key represents how bad of a word the word is, and 'auto_flag'
    indicates that the inclusion of this word in a string will result in the immediate
    reporting of the post for moderation.
    """
    filename = '/edx/src/badwords-en.json'
    with open(filename) as f:
        return json.load(f)

BADWORDS = load_words()

BADWORDS_REGEX = {w: re.compile(r'\b{}\b'.format(w), re.IGNORECASE) for w in BADWORDS}

REPORTING_THRESHOLD = 4


def check_for_profanity_and_report(**kwargs):
    """
    Given a post_id, post_title, and post_body, checks if the post should
    be flagged, and if so, reports the post using the post_id.
    """
    post_id = kwargs['post_id']
    post_title = kwargs['post_title']
    post_body = kwargs['post_body']
    post_type = kwargs['post_type']

    score = 0
    auto_flag = False
    violations = Counter()
    for content in (post_title, post_body):
        content_score, content_flag, content_violations = check_string(content)
        score += content_score
        auto_flag = max(auto_flag, content_flag)
        violations.update(content_violations)

    if auto_flag or (score >= REPORTING_THRESHOLD):
        report_post(post_id, post_type, violations)


def report_post(post_id, post_type, violations):
    """
    Use the discussion API to report this post.
    """
    profanity_bot = User.objects.get(username='staff')
    if post_type == 'thread':
        thread = cc.Thread.find(post_id)
        thread.flagAbuse(profanity_bot, thread)
    else:
        comment = cc.Comment.find(post_id)
        comment.flagAbuse(profanity_bot, comment)
    log.info('Post {} has been flagged for profanity violations {}'.format(post_id, violations))


def check_string(string):
    """
    Checks the given string against each regular expression in `BADWORDS_REGEX`
    and returns a tuple of (score, auto_flag), where score is an integer representing
    the total "profanity score" of the string and auto_flag is a boolean indicating
    if the string should automatically be reported, regardless of score.
    """
    score = 0
    auto_flag = False
    violations = Counter()
    for word in BADWORDS_REGEX:
        pattern = BADWORDS_REGEX[word]
        for _ in pattern.findall(string):
            violations[word] += 1
            score += BADWORDS[word]['score']
            auto_flag = max(auto_flag, BADWORDS[word]['auto_flag'])
    return score, auto_flag, violations

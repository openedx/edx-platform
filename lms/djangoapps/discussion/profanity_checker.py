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

from django_comment_common.models import CourseForumsProfanityCheckerConfig
import lms.lib.comment_client as cc


log = logging.getLogger(__name__)


def load_base_words():
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


BASE_BADWORDS = load_base_words()

REPORTING_THRESHOLD = 4


def load_regex(bad_words):
    return {w: re.compile(r'\b{}\b'.format(w), re.IGNORECASE) for w in bad_words}


def bad_words_for_course(course_key):
    checker_config = CourseForumsProfanityCheckerConfig.current(course_key)
    bad_words = BASE_BADWORDS.copy()
    bad_words.update(checker_config.extra_bad_words or {})
    for pattern in (checker_config.bad_word_patterns_to_ignore or []):
        if pattern in bad_words:
            bad_words.pop(pattern)
    return bad_words


def check_for_profanity_and_report(**kwargs):
    """
    Given a post_id, post_title, and post_body, checks if the post should
    be flagged, and if so, reports the post using the post_id.
    """
    post_id = kwargs['post_id']
    post_title = kwargs['post_title']
    post_body = kwargs['post_body']
    post_type = kwargs['post_type']
    course_key = CourseKey.from_string(kwargs['course_id'])

    score = 0
    auto_flag = False
    violations = Counter()
    bad_words = bad_words_for_course(course_key)
    regex = load_regex(bad_words)

    for content in (post_title, post_body):
        content_score, content_flag, content_violations = check_string(content, bad_words, regex)
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


def check_string(string, bad_words, regex):
    """
    Checks the given string against each regular expression in `regex`
    and returns a tuple of (score, auto_flag, violations), where score is an integer representing
    the total "profanity score" of the string and auto_flag is a boolean indicating
    if the string should automatically be reported, regardless of score.  violations is
    a Counter of the offending words and their cumulative score in the string.
    """
    score = 0
    auto_flag = False
    violations = Counter()
    for word in regex:
        pattern = regex[word]
        for _ in pattern.findall(string):
            word_score = bad_words[word].get('score', 0)
            violations[word] += word_score
            score += word_score
            auto_flag = max(auto_flag, bad_words[word].get('auto_flag', False))
    return score, auto_flag, violations

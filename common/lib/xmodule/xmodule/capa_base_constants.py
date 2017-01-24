# -*- coding: utf-8 -*-
"""
Constants for capa_base problems
"""


class SHOWANSWER(object):
    """
    Constants for when to show answer
    """
    ALWAYS = "always"
    ANSWERED = "answered"
    ATTEMPTED = "attempted"
    CLOSED = "closed"
    FINISHED = "finished"
    CORRECT_OR_PAST_DUE = "correct_or_past_due"
    PAST_DUE = "past_due"
    NEVER = "never"


class RANDOMIZATION(object):
    """
    Constants for problem randomization
    """
    ALWAYS = "always"
    ONRESET = "onreset"
    NEVER = "never"
    PER_STUDENT = "per_student"

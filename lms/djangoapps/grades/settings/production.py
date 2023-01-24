"""Common environment variables unique to the grades plugin."""


def plugin_settings(settings):
    """Common settings for Grades"""
    # Queue to use for updating persistent grades
    settings.RECALCULATE_GRADES_ROUTING_KEY = settings.ENV_TOKENS.get(
        'RECALCULATE_GRADES_ROUTING_KEY', settings.DEFAULT_PRIORITY_QUEUE,
    )

    # Queue to use for updating grades due to grading policy change
    settings.POLICY_CHANGE_GRADES_ROUTING_KEY = settings.ENV_TOKENS.get(
        'POLICY_CHANGE_GRADES_ROUTING_KEY', settings.DEFAULT_PRIORITY_QUEUE,
    )

    # Queue to use for individual learner course regrades
    settings.SINGLE_LEARNER_COURSE_REGRADE_ROUTING_KEY = settings.ENV_TOKENS.get(
        'SINGLE_LEARNER_COURSE_REGRADE_ROUTING_KEY', settings.DEFAULT_PRIORITY_QUEUE,
    )

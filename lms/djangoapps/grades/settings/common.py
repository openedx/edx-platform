def plugin_settings(settings):
    # Queue to use for updating persistent grades
    settings.RECALCULATE_GRADES_ROUTING_KEY = settings.DEFAULT_PRIORITY_QUEUE

    # Queue to use for updating grades due to grading policy change
    settings.POLICY_CHANGE_GRADES_ROUTING_KEY = settings.DEFAULT_PRIORITY_QUEUE

def plugin_settings(settings):
    settings.FEATURES['PERSISTENT_GRADES_ENABLED_FOR_ALL_TESTS'] = True
    settings.FEATURES['ASSUME_ZERO_GRADE_IF_ABSENT_FOR_ALL_TESTS'] = True

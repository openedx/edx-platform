"""
Profile Distributions
"""

from django.db.models import Count
from student.models import CourseEnrollment, UserProfile

AVAILABLE_PROFILE_FEATURES = ['gender', 'level_of_education', 'year_of_birth']


def profile_distribution(course_id, feature):
    """
    Retrieve distribution of students over a given feature.
    feature is one of AVAILABLE_PROFILE_FEATURES.

    Return a dictionary {
        'type': 'SOME_TYPE',
        'data': {'key': 'val'},
        'display_names': {'key': 'displaynameval'}
    }

    display_names is only return for EASY_CHOICE type eatuers
    note no_data instead of None to be compatible with the json spec.
    data types e.g.
        EASY_CHOICE - choices with a restricted domain, e.g. level_of_education
        OPEN_CHOICE - choices with a larger domain e.g. year_of_birth
    """

    EASY_CHOICE_FEATURES = ['gender', 'level_of_education']
    OPEN_CHOICE_FEATURES = ['year_of_birth']

    def raise_not_implemented():
        raise NotImplementedError("feature requested not implemented but is advertised in AVAILABLE_PROFILE_FEATURES {}" .format(feature))

    feature_results = {}

    if not feature in AVAILABLE_PROFILE_FEATURES:
        raise ValueError("unsupported feature requested for distribution '{}'".format(feature))

    if feature in EASY_CHOICE_FEATURES:
        if feature == 'gender':
            raw_choices = UserProfile.GENDER_CHOICES
        elif feature == 'level_of_education':
            raw_choices = UserProfile.LEVEL_OF_EDUCATION_CHOICES
        else:
            raise raise_not_implemented()

        choices = [(short, full) for (short, full) in raw_choices] + [('no_data', 'No Data')]

        data = {}
        for (short, full) in choices:
            if feature == 'gender':
                count = CourseEnrollment.objects.filter(course_id=course_id, user__profile__gender=short).count()
            elif feature == 'level_of_education':
                count = CourseEnrollment.objects.filter(course_id=course_id, user__profile__level_of_education=short).count()
            else:
                raise raise_not_implemented()
            data[short] = count

        feature_results['data'] = data
        feature_results['type'] = 'EASY_CHOICE'
        feature_results['display_names'] = dict(choices)
    elif feature in OPEN_CHOICE_FEATURES:
        profiles = UserProfile.objects.filter(user__courseenrollment__course_id=course_id)
        query_distribution = profiles.values(feature).annotate(Count(feature)).order_by()
        # query_distribution is of the form [{'featureval': 'value1', 'featureval__count': 4}, {'featureval': 'value2', 'featureval__count': 2}, ...]

        distribution = dict((vald[feature], vald[feature + '__count']) for vald in query_distribution)
        # distribution is of the form {'value1': 4, 'value2': 2, ...}

        # change none to no_data for valid json key
        if None in distribution:
            distribution['no_data'] = distribution.pop(None)
            # django does not properly count NULL values, so the above will alwasy be 0.
            # this correctly counts null values
            distribution['no_data'] = profiles.filter(**{feature: None}).count()

        feature_results['data'] = distribution
        feature_results['type'] = 'OPEN_CHOICE'
    else:
        raise raise_not_implemented()

    return feature_results

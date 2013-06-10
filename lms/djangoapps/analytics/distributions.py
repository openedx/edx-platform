"""
Profile Distributions
"""

from django.db.models import Count
from django.contrib.auth.models import User, Group
from student.models import CourseEnrollment, UserProfile

AVAILABLE_PROFILE_FEATURES = ['gender', 'level_of_education', 'year_of_birth']


def profile_distribution(course_id, feature):
    """
    Retrieve distribution of students over a given feature.
    feature is one of AVAILABLE_PROFILE_FEATURES.

    Returna dictionary {'type': 'SOME_TYPE', 'data': {'key': 'val'}}
    data types e.g.
        EASY_CHOICE - choices with a restricted domain, e.g. level_of_education
        OPEN_CHOICE - choices with a larger domain e.g. year_of_birth
    """

    EASY_CHOICE_FEATURES = ['gender', 'level_of_education']
    OPEN_CHOICE_FEATURES = ['year_of_birth']

    feature_results = {}

    if not feature in AVAILABLE_PROFILE_FEATURES:
        raise ValueError("unsupported feature requested for distribution '%s'" % feature)

    if feature in EASY_CHOICE_FEATURES:
        if feature == 'gender':
            choices = [(short, full) for (short, full) in UserProfile.GENDER_CHOICES] + [(None, 'No Data')]
        elif feature == 'level_of_education':
            choices = [(short, full) for (short, full) in UserProfile.LEVEL_OF_EDUCATION_CHOICES] + [(None, 'No Data')]
        else:
            raise ValueError("feature request not implemented for feature %s" % feature)

        data = {}
        for (short, full) in choices:
            if feature == 'gender':
                count = CourseEnrollment.objects.filter(course_id=course_id, user__profile__gender=short).count()
            elif feature == 'level_of_education':
                count = CourseEnrollment.objects.filter(course_id=course_id, user__profile__level_of_education=short).count()
            else:
                raise ValueError("feature request not implemented for feature %s" % feature)
            data[full] = count

        feature_results['data'] = data
        feature_results['type'] = 'EASY_CHOICE'
    elif feature in OPEN_CHOICE_FEATURES:
        profiles = UserProfile.objects.filter(user__courseenrollment__course_id=course_id)
        query_distribution = profiles.values(feature).annotate(Count(feature)).order_by()
        # query_distribution is of the form [{'attribute': 'value1', 'attribute__count': 4}, {'attribute': 'value2', 'attribute__count': 2}, ...]

        distribution = dict((vald[feature], vald[feature + '__count']) for vald in query_distribution)
        # distribution is of the form {'value1': 4, 'value2': 2, ...}
        feature_results['data'] = distribution
        feature_results['type'] = 'OPEN_CHOICE'
    else:
        raise ValueError("feature requested for distribution has not been implemented but is advertised in AVAILABLE_PROFILE_FEATURES! '%s'" % feature)

    return feature_results

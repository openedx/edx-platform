"""
Profile Distributions

Aggregate sums for values of fields in students profiles.

For example:
The distribution in a course for gender might look like:
'gender': {
    'type': 'EASY_CHOICE',
    'data': {
        'no_data': 1234,
        'm': 5678,
        'o': 2134,
        'f': 5678
    },
    'display_names': {
        'no_data': 'No Data',
        'm': 'Male',
        'o': 'Other',
        'f': 'Female'
}
"""

from django.db.models import Count
from student.models import CourseEnrollment, UserProfile

_EASY_CHOICE_FEATURES = ('gender', 'level_of_education')
_OPEN_CHOICE_FEATURES = ('year_of_birth',)
AVAILABLE_PROFILE_FEATURES = _EASY_CHOICE_FEATURES + _OPEN_CHOICE_FEATURES
DISPLAY_NAMES = {
    'gender': 'Gender',
    'level_of_education': 'Level of Education',
    'year_of_birth': 'Year Of Birth',
}


class ProfileDistribution(object):
    """
    Container for profile distribution data

    `feature` is the name of the distribution feature
    `feature_display_name` is the display name of feature
    `data` is a dictionary of the distribution
    `type` is either 'EASY_CHOICE' or 'OPEN_CHOICE'
    `choices_display_names` is a dict if the distribution is an 'EASY_CHOICE'
    """

    class ValidationError(ValueError):
        """ Error thrown if validation fails. """
        pass

    def __init__(self, feature):
        self.feature = feature
        self.feature_display_name = DISPLAY_NAMES[feature]

    def validate(self):
        """
        Validate this profile distribution.

        Throws ProfileDistribution.ValidationError
        """
        def validation_assert(predicate):
            if not predicate:
                raise ProfileDistribution.ValidationError()

        validation_assert(isinstance(self.feature, str))
        validation_assert(isinstance(self.feature_display_name, str))
        validation_assert(self.type in ['EASY_CHOICE', 'OPEN_CHOICE'])
        validation_assert(isinstance(self.data, dict))
        if self.type == 'EASY_CHOICE':
            validation_assert(isinstance(self.choices_display_names, dict))


def profile_distribution(course_id, feature):
    """
    Retrieve distribution of students over a given feature.
    feature is one of AVAILABLE_PROFILE_FEATURES.

    Returns a ProfileDistribution instance.

    NOTE: no_data will appear as a key instead of None to be compatible with the json spec.
    data types are
        EASY_CHOICE - choices with a restricted domain, e.g. level_of_education
        OPEN_CHOICE - choices with a larger domain e.g. year_of_birth
    """

    if not feature in AVAILABLE_PROFILE_FEATURES:
        raise ValueError(
            "unsupported feature requested for distribution '{}'".format(
                feature)
        )

    prd = ProfileDistribution(feature)

    if feature in _EASY_CHOICE_FEATURES:
        prd.type = 'EASY_CHOICE'

        if feature == 'gender':
            raw_choices = UserProfile.GENDER_CHOICES
        elif feature == 'level_of_education':
            raw_choices = UserProfile.LEVEL_OF_EDUCATION_CHOICES

        # short name and display nae (full) of the choices.
        choices = [(short, full)
                   for (short, full) in raw_choices] + [('no_data', 'No Data')]

        distribution = {}
        for (short, full) in choices:
            if feature == 'gender':
                count = CourseEnrollment.objects.filter(
                    course_id=course_id, user__profile__gender=short
                ).count()
            elif feature == 'level_of_education':
                count = CourseEnrollment.objects.filter(
                    course_id=course_id, user__profile__level_of_education=short
                ).count()
            distribution[short] = count

        prd.data = distribution
        prd.choices_display_names = dict(choices)
    elif feature in _OPEN_CHOICE_FEATURES:
        prd.type = 'OPEN_CHOICE'
        profiles = UserProfile.objects.filter(
            user__courseenrollment__course_id=course_id)
        query_distribution = profiles.values(
            feature).annotate(Count(feature)).order_by()
        # query_distribution is of the form [{'featureval': 'value1', 'featureval__count': 4},
        #    {'featureval': 'value2', 'featureval__count': 2}, ...]

        distribution = dict((vald[feature], vald[feature + '__count'])
                            for vald in query_distribution)
        # distribution is of the form {'value1': 4, 'value2': 2, ...}

        # change none to no_data for valid json key
        if None in distribution:
            distribution['no_data'] = distribution.pop(None)
            # django does not properly count NULL values, so the above will alwasy be 0.
            # this correctly counts null values
            distribution['no_data'] = profiles.filter(
                **{feature: None}
            ).count()

        prd.data = distribution

    prd.validate()
    return prd

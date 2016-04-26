from django.contrib.auth.models import User
from django.http import Http404
from rest_framework import serializers

from openedx.core.djangoapps.course_groups.cohorts import is_course_cohorted
from notification_prefs import NOTIFICATION_PREF_KEY
from lang_pref import LANGUAGE_KEY


class NotifierUserSerializer(serializers.ModelSerializer):
    """
    A serializer containing all information about a user needed by the notifier
    (namely the user's name, email address, notification and language
    preferences, and course enrollment and cohort information).

    Because these pieces of information reside in different tables, this is
    designed to work well with prefetch_related and select_related, which
    require the use of all() instead of get() or filter(). The following fields
    should be prefetched on the user objects being serialized:
     * profile
     * preferences
     * courseenrollment_set
     * course_groups
     * roles__permissions
    """
    name = serializers.SerializerMethodField()
    preferences = serializers.SerializerMethodField()
    course_info = serializers.SerializerMethodField()

    def get_name(self, user):
        return user.profile.name

    def get_preferences(self, user):
        return {
            pref.key: pref.value
            for pref
            in user.preferences.all()
            if pref.key in [LANGUAGE_KEY, NOTIFICATION_PREF_KEY]
        }

    def get_course_info(self, user):
        cohort_id_map = {
            cohort.course_id: cohort.id
            for cohort in user.course_groups.all()
        }
        see_all_cohorts_set = {
            role.course_id
            for role in user.roles.all()
            for perm in role.permissions.all() if perm.name == "see_all_cohorts"
        }
        ret = {}
        for enrollment in user.courseenrollment_set.all():
            if enrollment.is_active:
                try:
                    ret[unicode(enrollment.course_id)] = {
                        "cohort_id": cohort_id_map.get(enrollment.course_id),
                        "see_all_cohorts": (
                            enrollment.course_id in see_all_cohorts_set or
                            not is_course_cohorted(enrollment.course_id)
                        ),
                    }
                except Http404:  # is_course_cohorted raises this if course does not exist
                    pass
        return ret

    class Meta(object):
        model = User
        fields = ("id", "email", "name", "preferences", "course_info")
        read_only_fields = ("id", "email")

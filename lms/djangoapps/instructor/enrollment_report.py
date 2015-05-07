"""
Defines abstract class for the Enrollment Reports.
"""
from django.contrib.auth.models import User
import collections
import json
import abc


class AbstractEnrollmentReportProvider(object):
    """
    Abstract interface for Detailed Enrollment Report Provider
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_enrollment_info(self, user, course_id):
        """
        Returns the User Enrollment information.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_user_profile(self, user_id):
        """
        Returns the UserProfile information.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_payment_info(self, user, course_id):
        """
        Returns the User Payment information.
        """
        raise NotImplementedError()


class BaseAbstractEnrollmentReportProvider(AbstractEnrollmentReportProvider):
    """
    The base abstract class for all Enrollment Reports that can support multiple
    backend such as MySQL/Django-ORM.

    # don't allow instantiation of this class, it must be subclassed
    """
    def get_user_profile(self, user_id):
        """
        Returns the UserProfile information.
        """
        user_info = User.objects.select_related('profile').get(id=user_id)
        # extended user profile fields are stored in the user_profile meta column
        meta = {}
        if user_info.profile.meta:
            meta = json.loads(user_info.profile.meta)

        user_data = collections.OrderedDict()
        user_data['User ID'] = user_info.id
        user_data['Username'] = user_info.username
        user_data['Full Name'] = user_info.profile.name
        user_data['First Name'] = user_info.first_name
        user_data['Last Name'] = user_info.last_name
        user_data['Company Name'] = meta.get('company', '')
        user_data['Title'] = meta.get('title', '')
        user_data['Language'] = user_info.profile.language
        user_data['Location'] = user_info.profile.location
        user_data['Year of Birth'] = user_info.profile.year_of_birth
        user_data['Gender'] = user_info.profile.gender
        user_data['Level of Education'] = user_info.profile.level_of_education
        user_data['Mailing Address'] = user_info.profile.mailing_address
        user_data['Goals'] = user_info.profile.goals
        user_data['City'] = user_info.profile.city
        user_data['Country'] = user_info.profile.country
        return user_data

    def get_enrollment_info(self, user, course_id):
        """
        Returns the User Enrollment information.
        """
        raise NotImplementedError()

    def get_payment_info(self, user, course_id):
        """
        Returns the User Payment information.
        """
        raise NotImplementedError()

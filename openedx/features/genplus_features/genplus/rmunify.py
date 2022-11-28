import re
import logging
from hashlib import sha1
from http import HTTPStatus
from django.conf import settings
import requests
import base64
import hmac
from datetime import datetime
from openedx.features.genplus_features.genplus.models import GenUser, Student, School, Class
from openedx.features.genplus_features.genplus.constants import SchoolTypes, ClassTypes, GenUserRoles


logger = logging.getLogger(__name__)


class RmUnifyException(BaseException):
    pass


class RmUnify:
    ORGANISATION = 'organisation/'
    TEACHING_GROUP = '{}{}/teachinggroup/'
    REGISTRATION_GROUP = '{}{}/registrationgroup/'

    def __init__(self):
        self.key = settings.RM_UNIFY_KEY
        self.secret = settings.RM_UNIFY_SECRET
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    def fetch(self, source, source_id=None):
        headers = {"Authorization": "Unify " + self.key + "_" + self.timestamp + ":" + self.hashed}
        url = self.generate_url(source, source_id)
        response = requests.get(url, headers=headers)
        if response.status_code != HTTPStatus.OK.value:
            logger.exception(response.reason)
            return []
        return response.json()

    @property
    def hashed(self):
        hashed = hmac.new(bytes(self.secret, 'utf-8'), bytes(self.timestamp, 'utf-8'), sha1).digest()
        hashed = str(base64.urlsafe_b64encode(hashed), "UTF-8")
        hashed = hashed.replace('-', '+')
        return hashed.replace('_', '/')

    @staticmethod
    def generate_url(source, source_id):
        url = settings.RM_UNIFY_URL
        if source:
            url = url + source
        if source_id:
            url = url + source_id
        return url

    def fetch_schools(self):
        schools = self.fetch(self.ORGANISATION)
        for school in schools:
            obj, created = School.objects.update_or_create(
                name=school['DisplayName'],
                external_id=school['ExternalId'],
                type=SchoolTypes.RM_UNIFY,
                defaults={"guid": school['OrganisationGuid']}
            )
            response = 'created' if created else 'updated'
            logger.info('{} has been {} successfully.'.format(school['DisplayName'], response))

    def fetch_classes(self, class_type, queryset=School.objects.all()):
        for school in queryset:
            fetch_type = re.sub(r'(?<!^)(?=[A-Z])', '_', class_type).upper()
            # get specific url based on class_type
            url = getattr(self, fetch_type)
            classes = self.fetch(url.format(RmUnify.ORGANISATION, school.guid))
            for gen_class in classes:
                Class.objects.update_or_create(
                    type=class_type,
                    school=school,
                    group_id=gen_class['GroupId'],
                    name=gen_class['DisplayName'],
                    defaults={"name": gen_class['DisplayName']}
                )
            logger.info('classes for {} has been successfully fetched.'.format(school.name))

    def fetch_students(self, query=Class.visible_objects.all()):
        for gen_class in query:
            fetch_type = re.sub(r'(?<!^)(?=[A-Z])', '_', gen_class.type).upper()
            # formatting url according to class type
            url = getattr(self, fetch_type).format(RmUnify.ORGANISATION,
                                                   gen_class.school.guid)
            data = self.fetch(f"{url}/{gen_class.group_id}")
            gen_user_ids = []
            for student_data in data['Students']:
                student_email = student_data.get('UnifyEmailAddress')
                gen_user, created = GenUser.objects.get_or_create(
                    email=student_email,
                    role=GenUserRoles.STUDENT,
                    school=gen_class.school,
                )
                gen_user_ids.append(gen_user.pk)

            gen_students = Student.objects.filter(gen_user__in=gen_user_ids)
            gen_class.students.add(*gen_students)

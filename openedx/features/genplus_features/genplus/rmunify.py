import re
import logging
from hashlib import sha1
from http import HTTPStatus
from django.conf import settings
import requests
import base64
import hmac
from datetime import datetime
from openedx.features.genplus_features.genplus.models import GenUser, Student, TempUser, School, Class
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
            print(gen_class.name)
            fetch_type = re.sub(r'(?<!^)(?=[A-Z])', '_', gen_class.type).upper()
            # formatting url according to class type
            url = getattr(self, fetch_type).format(RmUnify.ORGANISATION,
                                                   gen_class.school.guid)
            print(url)
            data = self.fetch(f"{url}/{gen_class.group_id}")
            try:
                for student in data['Students']:
                    student_email = student['UnifyEmailAddress']
                    student_username = student['UserName']
                    try:
                        # check if student already exists in the system
                        gen_student = Student.objects.get(gen_user__user__username=student_username,
                                                          gen_user__user__email=student_email)
                    except Student.DoesNotExist:
                        try:
                            # check if student exist with a temp_user
                            gen_student = Student.objects.get(gen_user__temp_user__username=student_username,
                                                              gen_user__temp_user__email=student_email)
                        except Student.DoesNotExist:
                            # create a gen_user with tempuser
                            temp_user = TempUser.objects.get_or_create(username=student_username,
                                                                       email=student_email)
                            gen_user = GenUser.objects.create(
                                role=GenUserRoles.STUDENT,
                                school=gen_class.school,
                                temp_user=temp_user[0])
                            gen_user.refresh_from_db()
                            gen_student = gen_user.student
                    gen_class.students.add(gen_student)
                    logger.info(f"{student_username} has been added to {gen_class.name}")
            except KeyError:
                logger.exception('An Error occur while getting students')

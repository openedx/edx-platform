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
from .constants import RmUnifyUpdateTypes
from django.db.models import Q
from django.contrib.auth.models import User



logger = logging.getLogger(__name__)


class RmUnifyException(BaseException):
    pass


class BaseRmUnify:
    def __init__(self):
        self.key = settings.RM_UNIFY_KEY
        self.secret = settings.RM_UNIFY_SECRET
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    def fetch(self, url):
        headers = self.get_header()
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


    def get_header(self):
        return {"Authorization": "Unify " + self.key + "_" + self.timestamp + ":" + self.hashed}


class RmUnify(BaseRmUnify):
    ORGANISATION = 'organisation/'
    TEACHING_GROUP = '{}{}/teachinggroup/'
    REGISTRATION_GROUP = '{}{}/registrationgroup/'

    @staticmethod
    def generate_url(source, source_id=None):
        url = settings.RM_UNIFY_URL + '/graph/'
        if source:
            url = url + source
        if source_id:
            url = url + source_id
        return url

    def fetch_schools(self):
        url = self.generate_url(self.ORGANISATION)
        schools = self.fetch(url)
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
            url_path = getattr(self, fetch_type)
            url = self.generate_url(url_path.format(RmUnify.ORGANISATION, school.guid))
            classes = self.fetch(url)
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
            url_path = getattr(self, fetch_type).format(RmUnify.ORGANISATION,
                                                        gen_class.school.guid)
            url = self.generate_url(url_path)
            data = self.fetch(f"{url}/{gen_class.group_id}")
            gen_user_ids = []
            for student_data in data['Students']:
                student_email = student_data.get('UnifyEmailAddress')
                identity_guid = student_data.get('IdentityGuid')
                gen_user, created = GenUser.objects.get_or_create(
                    email=student_email,
                    role=GenUserRoles.STUDENT,
                    school=gen_class.school,
                )
                # update the identity_guid
                gen_user.identity_guid = identity_guid
                gen_user.save()
                gen_user_ids.append(gen_user.pk)

            gen_students = Student.objects.filter(gen_user__in=gen_user_ids)
            gen_class.students.add(*gen_students)


class RmUnifyProvisioning(BaseRmUnify):

    UPDATES = '/appprovisioning/v2/{}/updates/'
    DELETE_BATCH = '/appprovisioning/v2/{}/deletebatch/'

    def get_header(self):
        return {"Authorization": "Unify " + self.timestamp + ":" + self.hashed}

    @staticmethod
    def generate_url(source, source_id=None):
        url = settings.RM_UNIFY_URL
        if source:
            url = url + source
        if source_id:
            url = url + source_id
        return url

    def provision(self):
        url = self.generate_url(self.UPDATES.format(self.key))
        data = self.fetch(url)
        if data:
            updates_batch = []
            # check updates and update/delete user accordingly
            for update in data['Updates']:
                if update['Type'] == RmUnifyUpdateTypes.USER:
                    self.update_user(update['UpdateData'])
                elif update['Type'] == RmUnifyUpdateTypes.DELETE_USER:
                    try:
                        # only deleting if user with unify guid exist in our system
                        identity_guid = update['UpdateData']['IdentityGuid']
                        self.delete_user(identity_guid)
                    except KeyError:
                        pass

                updates_batch.append(
                    {
                        "UpdateId": update['UpdateId'],
                        "ReceiptId": update['ReceiptId']
                    },
                )
            if len(updates_batch):
                self.delete_batch(updates_batch)
        logger.error('No Updates Found')

    def delete_batch(self, batch):
        headers = self.get_header()
        post_data = {'Updates': batch}
        url = self.generate_url(self.DELETE_BATCH.format(self.key))
        response = requests.post(url, json=post_data, headers=headers)
        if response.status_code != HTTPStatus.OK.value:
            logger.exception(response.reason)
        logger.info('Successfully deleted batch {}'.format(str(batch)))

    @staticmethod
    def update_user(data):

        gen_user = GenUser.objects.filter(Q(user__email=data['UnifyEmailAddress']),
                                          Q(identity_guid=data['IdentityGuid']))
        if gen_user.exist():
            gen_user.user.first_name = data['FirstName']
            gen_user.user.last_name = data['LastName']
            gen_user.user.save()
        return

    @staticmethod
    def delete_user(guid):
        try:
            gen_user = GenUser.objects.get(identity_guid=guid)
            if gen_user.user is not None:
                user_pk = gen_user.user.pk
                # first delete gen_user so it can delete the related Enrollments
                gen_user.delete()
                User.objects.filter(pk=user_pk).delete()
            else:
                # case where user is not logged into our system
                gen_user.delete()
            logger.info(
                'User with identity_guid {} has been deleted.'.format(guid)
            )
        except GenUser.DoesNotExist:
            logger.exception(
                'User with identity_guid {} does not exist.'.format(guid)
            )

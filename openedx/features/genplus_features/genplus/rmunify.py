import re
import logging
from hashlib import sha1
from http import HTTPStatus
from django.conf import settings
import requests
import base64
import hmac
from datetime import datetime
from openedx.features.genplus_features.genplus.models import GenUser, Student, School, Class, GenLog
from openedx.features.genplus_features.genplus.constants import SchoolTypes, ClassTypes, GenUserRoles
from .constants import RmUnifyUpdateTypes
from django.db.models import Q
from django.utils.timezone import get_current_timezone
from django.db.utils import IntegrityError
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
                guid= school['OrganisationGuid'],
                type=SchoolTypes.RM_UNIFY,
                defaults={"external_id": school['ExternalId']}
            )
            response = 'created' if created else 'updated'
            logger.info('{} has been {} successfully.'.format(school['DisplayName'], response))

    def fetch_classes(self, class_type, queryset=School.objects.filter(type=SchoolTypes.RM_UNIFY)):
        for school in queryset:
            logger.info('___Fetching classes for {}___'.format(school.name))
            fetch_type = re.sub(r'(?<!^)(?=[A-Z])', '_', class_type).upper()
            # get specific url based on class_type
            url_path = getattr(self, fetch_type)
            url = self.generate_url(url_path.format(RmUnify.ORGANISATION, school.guid))
            classes = self.fetch(url)
            for gen_class in classes:
                gen_class, created = Class.objects.update_or_create(
                    type=class_type,
                    school=school,
                    group_id=gen_class['GroupId'],
                    name=gen_class['DisplayName'],
                    defaults={"name": gen_class['DisplayName']}
                )
                if created:
                    logger.info('{} has been successfully created.'.format(gen_class.name))
            logger.info('___classes for {} has been successfully fetched___'.format(school.name))

    def fetch_students(self, query=Class.visible_objects.filter(school__type=SchoolTypes.RM_UNIFY, type__isnull=False)):
        for gen_class in query:
            logger.info('___Fetching students for {}___'.format(gen_class.name))
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
                try:
                    gen_user, created = GenUser.objects.get_or_create(
                        email=student_email,
                        role=GenUserRoles.STUDENT,
                        school=gen_class.school,
                    )
                    # update the identity_guid
                    gen_user.identity_guid = identity_guid
                    gen_user.save()
                    gen_user_ids.append(gen_user.pk)
                    if created:
                        logger.info('Student with email {} created.'.format(gen_user.email))
                except IntegrityError:
                    logger.error('Error while creating {}.'.format(student_email))
                    # still adding it to the class (for not removing it in the process)
                    gen_user = GenUser.objects.get(email=student_email)
                    gen_user_ids.append(gen_user.pk)
                    # updating the school if user is not longer the member of old school
                    if not self.student_exists_in_rm_unify_old_school(gen_user):
                        gen_user.school = gen_class.school
                        gen_user.save()
                    # creating GenLog for more than one school
                    GenLog.create_more_than_one_school_log(student_email, gen_class.school.name, gen_class.name)
                    continue

            gen_students = Student.objects.filter(gen_user__in=gen_user_ids)
            gen_class.students.add(*gen_students)
            logger.info('_____{} students added to {}_____'.format(str(gen_students.count()), gen_class.name))
            # get the students which are not in the syncing from the RMUnify
            to_be_removed_students = gen_class.students.exclude(gen_user__id__in=gen_user_ids)
            # remove the remaining users from the class
            gen_class.students.remove(*to_be_removed_students)
            # update the last synced timestamp
            gen_class.last_synced = datetime.now(tz=get_current_timezone())
            gen_class.save()

    def student_exists_in_rm_unify_old_school(self, gen_user):
        try:
            resource_url = f'{gen_user.school.guid}/student/{gen_user.identity_guid}'
            url = self.generate_url(self.ORGANISATION, resource_url)
            return self.fetch(url)
        except Exception as e:
            logger.exception(str(e))
            return True


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
                        self.delete_user(identity_guid, update)
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
        else:
            logger.info('No Updates Found')

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
    def delete_user(guid, update):
        try:
            gen_user = GenUser.objects.get(identity_guid=guid)
            log_details = {
                'email': gen_user.email,
                'identity_guid': gen_user.identity_guid,
                'school': gen_user.school.name,
                'provisioning_update_details': update
            }
            if gen_user.user is not None:
                user_pk = gen_user.user.pk
                # first delete gen_user so it can delete the related Enrollments
                gen_user.delete()
                User.objects.filter(pk=user_pk).delete()
            else:
                # case where user is not logged into our system
                gen_user.delete()
            # create gen_log for removing the user from the system
            GenLog.create_remove_user_log(guid, log_details)
            logger.info(
                'User with identity_guid {} has been deleted.'.format(guid)
            )
        except GenUser.DoesNotExist:
            logger.exception(
                'User with identity_guid {} does not exist.'.format(guid)
            )

import logging
import requests
from datetime import datetime
from requests.exceptions import RequestException
from http import HTTPStatus
from django.conf import settings
from django.utils import timezone
from django.utils.timezone import get_current_timezone
from django.db.utils import IntegrityError
from openedx.features.genplus_features.genplus.models import GenUser, Student, School, Class, XporterDetail
from openedx.features.genplus_features.genplus.constants import GenUserRoles


logger = logging.getLogger(__name__)

class Xporter:
    BASE_API_URL = 'https://xporter.groupcall.com/api/'
    BASE_API_URL_V1 = f'{BASE_API_URL}v1/'
    AUTH_TOKEN_URL = f'{BASE_API_URL}oauth/GetToken'

    def __init__(self, school_id):
        self.school = School.objects.get(pk=school_id)

    def get_token(self):
        xporter_detail = self.school.xporter_detail

        try:
            if xporter_detail.token and xporter_detail.token_expiry >= timezone.now():
                return xporter_detail.token
        except TypeError:
            post_obj = {
                "estab": self.school.pk,
                "relyingParty": settings.XPORTER_RELYING_PARTY_ID,
                "password": xporter_detail.secret,
                "thirdpartyid": settings.XPORTER_THIRD_PARTY_ID,
            }

            res = requests.post(self.AUTH_TOKEN_URL, json=post_obj)

            if res.status_code == HTTPStatus.OK:
                res_obj = res.json()
                xporter_detail.token = res_obj['token']
                xporter_detail.token_expiry = res_obj['expires']
                xporter_detail.save()
                return xporter_detail.token

        return None

    def fetch(self, url):
        headers = self.get_header()
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.exception(e)
            return []

    def get_header(self):
        return {"Authorization": "Idaas " + self.get_token()}

    def fetch_classes(self, class_type):
        url = self.BASE_API_URL_V1 + f'School/{self.school.guid}/Groups/?Type={class_type}'
        response = self.fetch(url)

        for res in response.get('Group', []):
            external_id = res.get('ExternalId') or res.get('XID')
            defaults = {"name": res['Name']}

            gen_class, created = Class.objects.update_or_create(
                type=class_type,
                school=self.school,
                group_id=external_id,
                defaults=defaults
            )
            log_info = 'created' if created else 'updated'
            logger.info(f'{gen_class.name} has been successfully {log_info}.')

    def fetch_students(self, class_id):
        gen_class = Class.objects.get(id=class_id)
        url = self.BASE_API_URL_V1 + f'School/{self.school.guid}/Groups/{gen_class.group_id}?options=includeMembersIds'
        response = self.fetch(url)
        gen_class_res = response.get('Group')
        students = gen_class_res[0].get('StudentIds', '').split(',')
        gen_user_ids = []

        for student_id in students:
            student = self.get_student(student_id)

            if not student:
                continue
            scn = student.get('CandidateNo', '')
            student_id = student.get('Id', '')
            first_name = student.get('Forename', '')
            last_name = student.get('Surname', '')
            school_name = self.school.name.replace(" ", "").lower()
            # create a temp email to assign to the gen_user
            student_email = f'{first_name}_{last_name}{scn[:4]}@{school_name}.temp'

            try:
                gen_user = self.create_or_get_gen_user(scn, student_email)
                gen_user.identity_guid = student_id
                gen_user.save()
                gen_user.refresh_from_db()
                gen_user.student.scn = scn
                gen_user.student.save()
                gen_user_ids.append(gen_user.pk)
            except IntegrityError as e:
                logger.error(f'Error while creating {student_email}: {str(e)}')
                continue

        gen_students = self.get_gen_students(gen_user_ids)
        self.update_gen_class_students(gen_class, gen_students, gen_user_ids)

    def get_student(self, student_id):
        print('fetching for student id ****', student_id)
        url = f'{self.BASE_API_URL_V1}School/{self.school.guid}/Students/{student_id}'
        response = self.fetch(url)
        if response:
            students = response.get('Students')
            if students:
                return students[0]
        return None

    def create_or_get_gen_user(self, scn, student_email):
        try:
            # check if student with the same SCN exits in our system
            student = Student.objects.get(scn=scn)
            return student.gen_user
        except Student.DoesNotExist:
                gen_user, created = GenUser.objects.get_or_create(
                    email=student_email,
                    role=GenUserRoles.STUDENT,
                    school=self.school,
                )
                log_info = 'created' if created else 'updated'
                logger.info(f'Student with email {gen_user.email} {log_info}.')
                return gen_user

    @staticmethod
    def get_gen_students(gen_user_ids):
        return Student.objects.filter(gen_user__in=gen_user_ids)

    @staticmethod
    def update_gen_class_students(gen_class, gen_students, gen_user_ids):
        gen_class.students.clear()
        gen_class.students.add(*gen_students)
        logger.info(f'{gen_students.count()} students added to {gen_class.name}')
        to_be_removed_students = gen_class.students.exclude(gen_user__id__in=gen_user_ids)
        gen_class.students.remove(*to_be_removed_students)
        gen_class.last_synced = datetime.now(tz=get_current_timezone())
        gen_class.save()





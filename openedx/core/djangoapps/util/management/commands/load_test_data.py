#!/usr/bin/env python3
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from common.djangoapps.course_modes.models import CourseMode
from django.contrib.auth import get_user_model
import yaml
import codecs

from lms.djangoapps.verify_student.tests.factories import SoftwareSecurePhotoVerificationFactory

class Command(BaseCommand):
    """
    Created to help test how factoryboy works to add data to database
    """

    def add_arguments(self, parser):
        parser.add_argument('--data-file-path', type=str, help="Path to file where your data is specified.")


    def handle(self, *args, **options):
        with open(options["data_file_path"], 'r') as f:
            data_spec = yaml.safe_load(f)
        if 'users' in data_spec:
            self.create_users(data_spec['users'])
        if 'enrollments' in data_spec:
            self.create_enrollment(data_spec['enrollments'])

    def create_users(self, users):
        for user in data_spec['users']:
            UserFactory.create(**user)

    def create_enrollment(self, enrollments):
        User = get_user_model()
        for enrollment_spec in enrollments:
            try:
                user = User.objects.get(username=enrollment_spec['username'])
            except User.DoesNotExist:
                raise exception(f"User:{enrollment_spec['username']} not created before trying to create enrollment")
            if enrollment_spec['mode'] in CourseMode.VERIFIED_MODES:
                verfication = SoftwareSecurePhotoVerificationFactory(user=user)
            enrollment = CourseEnrollmentFactory(user=user, course_id=enrollment_spec['course_id'])
            if enrollment[0].mode != enrollment_spec['mode']:
                enrollment[0].mode = enrollment_spec['mode']
                enrollment[0].save()

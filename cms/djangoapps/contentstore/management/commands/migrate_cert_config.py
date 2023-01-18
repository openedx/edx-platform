"""
Script to transfer course certificate configuration to Credential IDA from modulestore (old mongo (draft) and split).
The script is a one-time action.
The context for this decision can be read here
lms/djangoapps/certificates/docs/decisions/007-transfer-certificate-signatures-from-mongo.rst
"""

import attr
from itertools import chain
from typing import Dict, Iterator, List, Union

from django.core.management.base import BaseCommand, CommandError

from common.djangoapps.course_modes.models import CourseMode
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import CourseLocator
from openedx.core.djangoapps.credentials.utils import send_course_certificate_configuration
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.course_module import CourseBlock
from cms.djangoapps.contentstore.signals.handlers import (
    create_course_certificate_config_data,
    get_certificate_signature_assets,
)
from cms.djangoapps.contentstore.views.certificates import CertificateManager


class FakedUser:
    def __init__(self, id_: int):
        self.id = id_


class FakedRequest:
    def __init__(self, user_id: int):
        self.user = FakedUser(user_id)


class Command(BaseCommand):
    """
    Management command to transfer course certificate configuration from modulestore to Credentials IDA.

    Examples:

        ./manage.py cms migrate_cert_config <course_id_1> <course_id_2> - transfer courses with provided keys
        ./manage.py cms migrate_cert_config --course_storage_type all - transfer all available courses
        ./manage.py cms migrate_cert_config --course_storage_type draft - transfer all mongo(old approach) modulestore
        available courses
        ./manage.py cms migrate_cert_config --course_storage_type split - transfer all split(new approach) modulestore
        available courses
        ./manage.py cms migrate_cert_config --course_storage_type all --delete-after - transfer all available courses
        and delete course certificate configuration, signature assets from modulestore after successfull transfer.
    """

    help = 'Allows manual transfer course certificate configuration from modulestore to Credentials IDA.'

    def add_arguments(self, parser):
        parser.add_argument('course_ids', nargs='*', metavar='course_id')
        parser.add_argument(
            '--course_storage_type',
            type=str.lower,
            default=None,
            choices=['all', 'draft', 'split'],
            help='Course storage types whose certificate configurations are to be migrated.',
        )
        parser.add_argument(
            '--delete-after',
            help='Boolean value to delete course certificate configuration, signature assets from modulestore.',
            action='store_true',
        )

    def _parse_course_key(self, raw_value: str) -> CourseKey:
        """
        Parses course key from string
        """
        try:
            result = CourseKey.from_string(raw_value)
        except InvalidKeyError:
            raise CommandError(f'Invalid course_key: {raw_value}.')
        if not isinstance(result, CourseLocator):
            raise CommandError(f'Argument {raw_value} is not a course key')

        return result

    def get_mongo_courses(self) -> Iterator[CourseKey]:
        """
        Return objects for any mongo(old approach) modulestore backend course that has a certificate configuration.
        """
        # N.B. This code breaks many abstraction barriers. That's ok, because
        # it's a one-time cleanup command.
        mongo_modulestore = modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.mongo)
        old_mongo_courses = mongo_modulestore.collection.find(
            {'_id.category': 'course', 'metadata.certificates': {'$exists': 1}},
            {
                '_id': True,
            },
        )
        for course in old_mongo_courses:
            yield mongo_modulestore.make_course_key(
                course['_id']['org'],
                course['_id']['course'],
                course['_id']['name'],
            )

    def get_split_courses(self) -> Iterator[CourseKey]:
        """
        Return objects for any split modulestore backend course that has a certificate configuration.
        """
        # N.B. This code breaks many abstraction barriers. That's ok, because
        # it's a one-time cleanup command.
        split_modulestore = modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.split)
        active_version_collection = split_modulestore.db_connection.course_index
        structure_collection = split_modulestore.db_connection.structures
        branches = list(
            active_version_collection.aggregate(
                [
                    {
                        '$group': {
                            '_id': 1,
                            'draft': {'$push': '$versions.draft-branch'},
                            'published': {'$push': '$versions.published-branch'},
                        }
                    },
                    {'$project': {'_id': 1, 'branches': {'$setUnion': ['$draft', '$published']}}},
                ]
            )
        )[0]['branches']

        structures = structure_collection.find(
            {
                '_id': {'$in': branches},
                'blocks': {
                    '$elemMatch': {
                        '$and': [
                            {'block_type': 'course'},
                            {'fields.certificates': {'$exists': True}},
                        ]
                    }
                },
            },
            {
                '_id': True,
            },
        )

        structure_ids = [struct['_id'] for struct in structures]
        split_mongo_courses = list(
            active_version_collection.find(
                {
                    '$or': [
                        {'versions.draft-branch': {'$in': structure_ids}},
                        {'versions.published': {'$in': structure_ids}},
                    ]
                },
                {
                    'org': True,
                    'course': True,
                    'run': True,
                    'versions': True,
                },
            )
        )
        for course in split_mongo_courses:
            yield split_modulestore.make_course_key(
                course['org'],
                course['course'],
                course['run'],
            )

    def send_to_credentials(
        self,
        course_key: CourseKey,
        mode: CourseMode,
        certificate_data: Dict[str, Union[str, List[str]]]
    ):
        """
        Sends certificate configuration data to Credential IDA via http request.
        """
        certificate_config = create_course_certificate_config_data(str(course_key), mode.slug, certificate_data)
        files_to_upload = dict(get_certificate_signature_assets(certificate_config))
        certificate_config_data = attr.asdict(certificate_config)
        send_course_certificate_configuration(str(course_key), certificate_config_data, files_to_upload)

    def delete_from_store(self, course: CourseBlock, certificates: List[Dict[str, str]]):
        """
        Deletes certificate configuration from modulestore storage.
        """
        store = modulestore()
        request = FakedRequest(ModuleStoreEnum.UserID.mgmt_command)
        for cert in certificates:
            CertificateManager.remove_certificate(
                request=request, store=store, course=course, certificate_id=cert['id']
            )

    def validate_input(self, options: Dict[str, str]):
        """
        Makes manage-command input validation. Raises CommandError if has conflicts.
        """
        if (not len(options['course_ids']) and not options.get('course_storage_type')) or (
            len(options['course_ids']) and options.get('course_storage_type')
        ):
            raise CommandError(
                'Certificate configurations migration requires one or more <course_id>s '
                'OR the --course_storage_type choice.'
            )

    def get_course_keys_by_option(self, options: Dict[str, str]) -> Iterator[CourseKey]:
        storage_type = options['course_storage_type']
        course_ids = options['course_ids']
        if storage_type:
            if storage_type == 'all':
                return chain(self.get_mongo_courses(), self.get_split_courses())
            elif storage_type == 'draft':
                return self.get_mongo_courses()
            elif storage_type == 'split':
                return self.get_split_courses()
        if course_ids:
            return map(self._parse_course_key, course_ids)

    def migrate(self, course_keys: List[CourseKey], options: Dict[str, str]):
        """
        Main entry point for executiong all migration-related actions.

        Sending to Credential and/or removal from storage.
        If there are problems with some course, i.e. or it does not exist, or the course is not set to mode,
        which allows to have a certificate, or no certificate configuration,
        then an user of this command will be notified by a message.
        """
        for course_key in course_keys:
            if course := modulestore().get_course(course_key):
                if course_modes := CourseMode.objects.filter(
                    course_id=course_key, mode_slug__in=CourseMode.CERTIFICATE_RELEVANT_MODES
                ):
                    if certificates := CertificateManager.get_certificates(course):
                        for certificate_data in certificates:
                            for mode in course_modes:
                                try:
                                    self.send_to_credentials(course_key, mode, certificate_data)
                                except Exception as exc:
                                    self.stderr.write(str(exc))
                                else:
                                    if options.get('delete_after'):
                                        self.delete_from_store(course, certificates)
                    else:
                        self.stderr.write(f'The course {course_key} does not have any configured certificates.')
                else:
                    self.stderr.write(f'The course {course_key} does not have certificate relevant modes.')
            else:
                self.stderr.write(f'The course {course_key} does not exist.')

    def handle(self, *args, **options):
        """
        Executes the command.
        """
        self.validate_input(options)
        course_keys_to_migrate = self.get_course_keys_by_option(options)
        self.migrate(course_keys_to_migrate, options)

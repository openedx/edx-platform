"""
Command to import Blockstore-backed v2 Libraries to Learning Core data models.

This will hopefully be very short-lived code.
"""
from datetime import datetime, timezone
from xml.etree import ElementTree as ET
import logging

from django.db import transaction
from django.core.management import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist

from opaque_keys.edx.locator import LibraryLocatorV2
from openedx.core.djangoapps.content_libraries import api as lib_api
from openedx.core.djangoapps.content_libraries import models as lib_models
from openedx.core.djangoapps.content_libraries import constants as lib_constants
from openedx.core.lib.blockstore_api import (
    get_bundle,
    get_bundle_file_data,
    get_bundle_files_dict,
)
from openedx_learning.core.publishing import api as publishing_api
from openedx_learning.core.components import api as components_api
from openedx_learning.core.contents import api as contents_api
from openedx_learning.core.collections import api as collections_api


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Create a new LearningPackage and initialize with contents from Library.

    If you run this and specify a Library that already has a LearningPackage
    (using -f), this command will delete that LearningPackage and create a new
    one to associate with the Libary. It does not modify the existing one.

    All the work is done in a transaction, so errors partway through the
    process shouldn't cause state inconsistency in the database. A partly-
    imported course *can* cause data to end up in Django Storages.
    """

    def add_arguments(self, parser):
        """
        Add arguments to the argument parser.
        """
        parser.add_argument(
            'library-key',
            type=LibraryLocatorV2.from_string,
            help=('Content Library Key to import content from.'),
        )
        parser.add_argument(
            '-f',
            '--force',
            action='store_true',
            default=False,
        )

    def handle(self, *args, **options):
        """
        Does the work of parsing content from Blockstore and writing it into
        openedx-learning core models (publishing, components, contents).
        """
        # Search for the library.
        try:
            lib_key = options['library-key']
            lib_data = lib_api.get_library(lib_key)
            lib = lib_models.ContentLibrary.objects.get_by_key(lib_key)
        except ObjectDoesNotExist:
            raise CommandError(f"Library not found: {lib_key}")

        COMPONENT_NAMESPACE = 'xblock.v1'

        learning_package_already_exists = (
            hasattr(lib, 'contents') and
            lib.contents.learning_package is not None
        )

        if learning_package_already_exists and not options['force']:
            raise CommandError(
                f"Learning Package already exists for {lib_key} (use -f to overwrite)"
            )

        with transaction.atomic():
            # This is a migration script and we're assuming there's no important
            # state attached to the LearningPackage yet. That makes it safe to
            # just wipe out everything and recreate it.
            if learning_package_already_exists:
                lp = lib.contents.learning_package
                log.info(f"Deleting existing LearningPackage {lp.key} ({lp.uuid})")
                lib.contents.delete()
                lp.delete()

            # Initialize a new LearningPackage
            learning_package = publishing_api.create_learning_package(
                key=lib_key,
                title=lib_data.title,
            )
            log.info(f"Created LearningPackage {learning_package.key} ({learning_package.uuid})")
            lib.learning_package = learning_package
            lib.save()

            # We don't need the full history stored in Blockstore, just the most
            # recently published version and the most recent draft.
            bundle = get_bundle(lib.bundle_uuid)
            published_files = get_bundle_files_dict(lib.bundle_uuid)

            now = datetime.now(timezone.utc)

            # First get the published version into openedx-learning models. On
            # the openedx-learning side, we'll create them as Drafts and then
            # publish at the end.
            published_metadata_dict = {}
            published_component_pks = {}
            published_definition_files = {
                file_path: metadata
                for file_path, metadata in published_files.items()
                if file_path.endswith('/block.xml')  # This is the OLX
            }
            for file_path, metadata in published_definition_files.items():
                block_type, block_id, _def_xml = file_path.split('/')
                published_metadata_dict[file_path] = metadata
                xml_bytes = get_bundle_file_data(bundle.uuid, file_path)
                display_name = extract_display_name(xml_bytes, file_path)

                component, component_version = components_api.create_component_and_version(
                    learning_package.id,
                    namespace=COMPONENT_NAMESPACE,
                    type=block_type,
                    local_key=block_id,
                    title=display_name,
                    created=now,
                    created_by=None,
                )
                published_component_pks[file_path] = component.pk
                text_content, _created = contents_api.get_or_create_text_content_from_bytes(
                    learning_package.id,
                    data_bytes=xml_bytes,
                    mime_type=f"application/vnd.openedx.xblock.v1.{block_type}+xml",
                    created=now,
                )
                components_api.add_content_to_component_version(
                    component_version.pk,
                    raw_content_id=text_content.pk,
                    key="block.xml",
                    learner_downloadable=False
                )
            # Publish all the Draft versions we created.
            publishing_api.publish_all_drafts(
                learning_package.id,
                message="Initial import from Blockstore",
                published_at=now,
            )

            # Now grab the draft version from blockstore, and copy those...
            draft_files = get_bundle_files_dict(lib.bundle_uuid, use_draft=lib_constants.DRAFT_NAME)
            draft_definition_files = {
                file_path: metadata
                for file_path, metadata in draft_files.items()
                if file_path.endswith("block.xml")
            }
            for file_path, draft_metadata in draft_definition_files.items():
                published_metadata = published_metadata_dict.get(file_path)
                if draft_metadata.modified:
                    block_type, block_id, _def_xml = file_path.split('/')
                    xml_bytes = get_bundle_file_data(bundle.uuid, file_path, use_draft=lib_constants.DRAFT_NAME)
                    display_name = extract_display_name(xml_bytes, file_path)

                    # If this is newly created in the draft, we have to create a
                    # whole new Component...
                    if published_metadata is None:
                        component = components_api.create_component(
                            learning_package.id,
                            namespace=COMPONENT_NAMESPACE,
                            type=block_type,
                            local_key=block_id,
                            created=now,
                            created_by=None,
                        )
                        component_pk = component.pk
                        version_num = 1
                    # Otherwise, it's just been modified...
                    else:
                        component_pk = published_component_pks[file_path]
                        version_num = 2

                    component_version = components_api.create_component_version(
                        component_pk,
                        version_num=version_num,
                        title=display_name,
                        created=now,
                        created_by=None,
                    )
                    text_content, _created = contents_api.get_or_create_text_content_from_bytes(
                        learning_package.id,
                        data_bytes=xml_bytes,
                        mime_type=f"application/vnd.openedx.xblock.v1.{block_type}+xml",
                        created=now,
                    )
                    components_api.add_content_to_component_version(
                        component_version.pk,
                        raw_content_id=text_content.pk,
                        key="block.xml",
                        learner_downloadable=False
                    )

            # Now remove stuff that was present in the published set but was
            # deleted in the draft.
            deleted_definition_files = set(published_definition_files) - set(draft_definition_files)
            for deleted_definition_file in deleted_definition_files:
                log.info(f"Deleting {deleted_definition_file} from draft")
                component_pk = published_component_pks[deleted_definition_file]
                publishing_api.soft_delete_draft(component_pk)

            # Now create a container Collection for everything
            collections_api.create_collection(
                learning_package.id,
                key=str(lib_key),
                title="Imported Library Collection",
                pub_entities_qset=learning_package.publishable_entities.all(),
            )

def extract_display_name(xml_bytes, file_path):
    """
    Parse the display_name out of the XML.

    This will return an empty string if no display_name is specified, or if
    there is a parsing error.
    """
    try:
        xml_str = xml_bytes.decode('utf-8')
        block_root = ET.fromstring(xml_str)
        display_name = block_root.attrib.get("display_name", "")
    except ET.ParseError as err:
        log.error(f"Parse error for {file_path}: {err}")
        display_name = ""

    return display_name

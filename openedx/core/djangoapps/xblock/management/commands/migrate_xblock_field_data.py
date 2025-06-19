"""
Management command to migrate existing XBlock OLX content to the field data model.

This command processes Components and uses the XBlock runtime to generate and save field data for both published
and draft versions, ensuring that XBlockVersionFieldData records exist for faster field access.
"""
import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from openedx_learning.api.authoring_models import Component
from xblock.exceptions import NoSuchUsage

from openedx.core.djangoapps.xblock.models import XBlockVersionFieldData
from openedx.core.djangoapps.xblock.api import get_runtime
from openedx.core.djangoapps.xblock.data import AuthoredDataMode, LatestVersion
from opaque_keys.edx.keys import UsageKeyV2


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to populate XBlockVersionFieldData from existing Components.

    This command processes Components, using the XBlock runtime's get_block method
    to generate and save field data for both published and draft versions.
    This is intended to pre-populate the field data cache for performance.
    """

    help = "Migrate existing XBlock content to the field data model using the runtime."

    def add_arguments(self, parser):
        parser.add_argument(
            '--learning-package-id',
            type=int,
            help='Only process Components from this learning package.'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of Components to process in each batch (default: 100).'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually creating records.'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recreate field data even if it already exists.'
        )
        parser.add_argument(
            '--block-type',
            type=str,
            help='Only process Components of this block type (e.g., "problem", "html").'
        )

    def handle(self, *args, **options):
        """Process Components and create field data records."""

        filters = Q()
        if options['learning_package_id']:
            filters &= Q(learning_package_id=options['learning_package_id'])
        if options['block_type']:
            filters &= Q(component_type__name=options['block_type'])

        try:
            components = Component.objects.select_related('learning_package').filter(filters).order_by('pk')
            total_count = components.count()
            self.stdout.write(f"Found {total_count} Components to process")
        except Exception as e:
            raise CommandError(f"Failed to query Components: {e}")

        if options['dry_run']:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("No Components to process."))
            return

        batch_size = options['batch_size']
        processed_components = 0
        processed_versions = 0
        errors = 0

        self.stdout.write(f"Processing in batches of {batch_size}...")

        # We do not need a user instance to generate XBlock's field data from `Scope.content` and `Scope.settings`.
        runtime = get_runtime(None)  # type: ignore
        # Set the mode to Authoring to access draft versions, in case somebody runs this from LMS.
        runtime.authored_data_mode = AuthoredDataMode.DEFAULT_DRAFT

        for batch_start in range(0, total_count, batch_size):
            batch_end = min(batch_start + batch_size, total_count)
            component_batch = components[batch_start:batch_end]

            for component in component_batch:
                processed_components += 1
                key = None
                try:
                    # FIXME: There must be a better way to construct the key.
                    key = UsageKeyV2.from_string(
                        f"lb{component.learning_package.key.lstrip('lib')}{component.key.lstrip('xblock.v1')}"
                    )

                    # If --force is used, delete existing field data first.
                    if options['force']:
                        versions_to_clear = []
                        if component.versioning.draft:
                            versions_to_clear.append(component.versioning.draft.pk)
                        if component.versioning.published:
                            versions_to_clear.append(component.versioning.published.pk)

                        if versions_to_clear:
                            if options['dry_run']:
                                self.stdout.write(
                                    f"DRY RUN: Would delete existing field data for {key}"
                                )
                            else:
                                with transaction.atomic():
                                    deleted_count, _ = XBlockVersionFieldData.objects.filter(
                                        publishable_entity_version_id__in=versions_to_clear
                                    ).delete()
                                    if deleted_count > 0:
                                        log.info("Deleted %d field data records for %s due to --force", deleted_count, key)

                    for version in (LatestVersion.PUBLISHED, LatestVersion.DRAFT):
                        if options['dry_run']:
                            if version == LatestVersion.DRAFT and not component.versioning.draft:
                                continue
                            if version == LatestVersion.PUBLISHED and not component.versioning.published:
                                continue
                            self.stdout.write(f"DRY RUN: Would process {key} version {version.name}")
                            continue

                        try:
                            # This call will parse the OLX and create a new database record if it doesn't exist.
                            runtime.get_block(key, version=version)
                            processed_versions += 1
                        except NoSuchUsage:
                            # This is expected if a component doesn't have a draft or published version.
                            pass
                        except Exception as e:
                            errors += 1
                            log.exception("Error processing %s version %s: %s", key, version.name, e)
                            self.stdout.write(
                                self.style.ERROR(f"Error on {key} v{version.name}: {e}")
                            )

                except Exception as e:
                    errors += 1
                    error_key_str = key or f"Component PK {component.pk}"
                    log.exception("Error processing %s: %s", error_key_str, e)
                    self.stdout.write(
                        self.style.ERROR(f"Error on {error_key_str}: {e}")
                    )

                if processed_components % 100 == 0 and processed_components > 0:
                    self.stdout.write(f"Processed {processed_components}/{total_count} components...")

        self.stdout.write(
            self.style.SUCCESS(
                f"Migration complete: {processed_versions} block versions processed, "
                f"{processed_components} total components processed, {errors} errors"
            )
        )

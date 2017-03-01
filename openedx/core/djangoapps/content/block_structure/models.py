"""
Models used by the block structure framework.
"""

from datetime import datetime
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from logging import getLogger

from model_utils.models import TimeStampedModel
from openedx.core.djangoapps.xmodule_django.models import UsageKeyField
from openedx.core.lib.block_structure.exceptions import BlockStructureNotFound
from openedx.core.storage import get_storage

import openedx.core.djangoapps.content.block_structure.config as config


log = getLogger(__name__)


def _create_path(directory, filename):
    """
    Returns the full path for the given directory and filename.
    """
    return '{}/{}'.format(directory, filename)


def _directory_name(data_usage_key):
    """
    Returns the directory name for the given
    data_usage_key.
    """
    return '{}{}'.format(
        settings.BLOCK_STRUCTURES_SETTINGS.get('DIRECTORY_PREFIX', ''),
        unicode(data_usage_key),
    )


def _path_name(bs_model, filename):  # pylint:disable=unused-argument
    """
    Returns path name to use for the given
    BlockStructureModel instance.
    """
    filename = datetime.utcnow().strftime('%Y-%m-%d-%H:%M:%S-%f')
    return _create_path(
        _directory_name(bs_model.data_usage_key),
        filename,
    )


def _bs_model_storage():
    """
    Get django Storage object for BlockStructureModel.
    """
    return get_storage(
        settings.BLOCK_STRUCTURES_SETTINGS.get('STORAGE_CLASS'),
        **settings.BLOCK_STRUCTURES_SETTINGS.get('STORAGE_KWARGS', {})
    )


class BlockStructureModel(TimeStampedModel):
    """
    Model for storing Block Structure information.
    """
    VERSION_FIELDS = [
        u'data_version',
        u'data_edit_timestamp',
        u'transformers_schema_version',
        u'block_structure_schema_version',
    ]
    UNIQUENESS_FIELDS = [u'data_usage_key'] + VERSION_FIELDS

    class Meta(object):
        db_table = 'block_structure'

    data_usage_key = UsageKeyField(
        u'Identifier of the data being collected.',
        blank=False,
        max_length=255,
        unique=True,
    )
    data_version = models.CharField(
        u'Version of the data at the time of collection.',
        blank=True,
        null=True,
        max_length=255,
    )
    data_edit_timestamp = models.DateTimeField(
        u'Edit timestamp of the data at the time of collection.',
        blank=True,
        null=True,
    )
    transformers_schema_version = models.CharField(
        u'Representation of the schema version of the transformers used during collection.',
        blank=False,
        max_length=255,
    )
    block_structure_schema_version = models.CharField(
        u'Version of the block structure schema at the time of collection.',
        blank=False,
        max_length=255,
    )
    data = models.FileField(
        upload_to=_path_name,
        max_length=500,  # allocate enough for base path + prefix + usage_key + timestamp in filepath
    )

    def get_serialized_data(self):
        """
        Returns the collected data for this instance.
        """
        serialized_data = self.data.read()
        log.info("BlockStructure: Read data from store; %r, size: %d", self, len(serialized_data))
        return serialized_data

    @classmethod
    def get(cls, data_usage_key):
        """
        Returns the entry associated with the given data_usage_key.
        Raises:
             BlockStructureNotFound if an entry for data_usage_key is not found.
        """
        try:
            return cls.objects.get(data_usage_key=data_usage_key)
        except cls.DoesNotExist:
            log.info("BlockStructure: Not found in table; %r.", data_usage_key)
            raise BlockStructureNotFound(data_usage_key)

    @classmethod
    def update_or_create(cls, serialized_data, data_usage_key, **kwargs):
        """
        Updates or creates the BlockStructureModel entry
        for the given data_usage_key in the kwargs,
        uploading serialized_data as the content data.
        """
        bs_model, created = cls.objects.update_or_create(defaults=kwargs, data_usage_key=data_usage_key)
        bs_model.data.save('', ContentFile(serialized_data))
        log.info(
            'BlockStructure: %s in store; %r, size: %d',
            'Created' if created else 'Updated',
            bs_model,
            len(serialized_data),
        )
        if not created:
            cls._prune_files(data_usage_key)

        return bs_model, created

    def __unicode__(self):
        """
        Returns a string representation of this model.
        """
        return u', '.join(
            u'{}: {}'.format(field_name, unicode(getattr(self, field_name)))
            for field_name in self.UNIQUENESS_FIELDS
        )

    @classmethod
    def _prune_files(cls, data_usage_key, num_to_keep=None):
        """
        Deletes previous file versions for data_usage_key.
        """
        if not config.is_enabled(config.PRUNE_OLD_VERSIONS):
            return

        if num_to_keep is None:
            num_to_keep = config.num_versions_to_keep()

        try:
            all_files_by_date = sorted(cls._get_all_files(data_usage_key))
            files_to_delete = all_files_by_date[:-num_to_keep] if num_to_keep > 0 else all_files_by_date
            cls._delete_files(files_to_delete)
            log.info(
                'BlockStructure: Deleted %d out of total %d files in store; data_usage_key: %r, num_to_keep: %d.',
                len(files_to_delete),
                len(all_files_by_date),
                data_usage_key,
                num_to_keep,
            )

        except Exception as error:  # pylint: disable=broad-except
            log.exception(
                'BlockStructure: Exception when deleting old files; data_usage_key: %r, %r',
                data_usage_key,
                error,
            )

    @classmethod
    def _delete_files(cls, files):
        """
        Deletes the given files from storage.
        """
        storage = _bs_model_storage()
        map(storage.delete, files)

    @classmethod
    def _get_all_files(cls, data_usage_key):
        """
        Returns all filenames that exist for the given key.
        """
        directory = _directory_name(data_usage_key)
        _, filenames = _bs_model_storage().listdir(directory)
        return [
            _create_path(directory, filename)
            for filename in filenames
            if filename and not filename.startswith('.')
        ]

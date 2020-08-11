from django.db import IntegrityError
from opaque_keys.edx.keys import LearningContextKey, UsageKey

from .data import ExternalDiscussionData
from ..models import ExternalDiscussionsIdMapping


def create_external_discussion_mapping(
    context_key: LearningContextKey,
    usage_key: UsageKey,
    external_discussion_id: str
) -> ExternalDiscussionData:
    """
    Create an ExternalDiscussionsIdMapping given the context key, usage key, and external discussion id
    """

    try:
        discussion_mapping = ExternalDiscussionsIdMapping.objects.create(
            context_key=context_key,
            usage_key=usage_key,
            external_discussion_id=external_discussion_id
        )
    except IntegrityError:
        raise ValueError(
            "Unable to create External Discussion Mapping. A mapping already exists for "
            "context_key={context_key} and usage_key={usage_key}".format(
                context_key=context_key,
                usage_key=usage_key
            )
        )

    return ExternalDiscussionData(
        context_key=discussion_mapping.context_key,
        external_discussion_id=discussion_mapping.external_discussion_id,
        usage_key=discussion_mapping.usage_key
    )


def remove_external_discussion_mapping(external_discussion_data: ExternalDiscussionData) -> bool:
    """
    Given an ExternalDiscussionData object, attempt to remove the corresponding DB object.
    Returns True on success, and False on failure
    """
    try:
        discussion_mapping = ExternalDiscussionsIdMapping.objects.get(
            context_key=external_discussion_data.context_key,
            external_discussion_id=external_discussion_data.external_discussion_id,
            usage_key=external_discussion_data.usage_key
        )
    except ExternalDiscussionsIdMapping.DoesNotExist:
        return False

    discussion_mapping.delete()

    return True


def get_external_discussion_context(context_key: LearningContextKey, usage_key: UsageKey) -> ExternalDiscussionData:
    """
    Return an ExternalDiscussionData object with the external_discussion_id given the context_key and usage_key
    """
    try:
        discussion_mapping = ExternalDiscussionsIdMapping.objects.get(
            context_key=context_key,
            usage_key=usage_key
        )
    except ExternalDiscussionsIdMapping.DoesNotExist:
        return None

    return ExternalDiscussionData(
        context_key=discussion_mapping.context_key,
        external_discussion_id=discussion_mapping.external_discussion_id,
        usage_key=discussion_mapping.usage_key
    )

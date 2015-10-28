"""
Utilities for django models.
"""
import unicodedata
import re

from eventtracking import tracker

from django.conf import settings
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe

from django_countries.fields import Country

# The setting name used for events when "settings" (account settings, preferences, profile information) change.
USER_SETTINGS_CHANGED_EVENT_NAME = u'edx.user.settings.changed'


def get_changed_fields_dict(instance, model_class):
    """
    Helper method for tracking field changes on a model.

    Given a model instance and class, return a dict whose keys are that
    instance's fields which differ from the last saved ones and whose values
    are the old values of those fields.  Related fields are not considered.

    Args:
        instance (Model instance): the model instance with changes that are
            being tracked
        model_class (Model class): the class of the model instance we are
            tracking

    Returns:
        dict: a mapping of field names to current database values of those
            fields, or an empty dict if the model is new
    """
    try:
        old_model = model_class.objects.get(pk=instance.pk)
    except model_class.DoesNotExist:
        # Object is new, so fields haven't technically changed.  We'll return
        # an empty dict as a default value.
        return {}
    else:
        field_names = [
            field[0].name for field in model_class._meta.get_fields_with_model()
        ]
        changed_fields = {
            field_name: getattr(old_model, field_name) for field_name in field_names
            if getattr(old_model, field_name) != getattr(instance, field_name)
        }

        return changed_fields


def emit_field_changed_events(instance, user, db_table, excluded_fields=None, hidden_fields=None):
    """Emits a settings changed event for each field that has changed.

    Note that this function expects that a `_changed_fields` dict has been set
    as an attribute on `instance` (see `get_changed_fields_dict`.

    Args:
        instance (Model instance): the model instance that is being saved
        user (User): the user that this instance is associated with
        db_table (str): the name of the table that we're modifying
        excluded_fields (list): a list of field names for which events should
            not be emitted
        hidden_fields (list): a list of field names specifying fields whose
            values should not be included in the event (None will be used
            instead)

    Returns:
        None
    """
    def clean_field(field_name, value):
        """
        Prepare a field to be emitted in a JSON serializable format.  If
        `field_name` is a hidden field, return None.
        """
        if field_name in hidden_fields:
            return None
        # Country is not JSON serializable.  Return the country code.
        if isinstance(value, Country):
            if value.code:
                return value.code
            else:
                return None
        return value

    excluded_fields = excluded_fields or []
    hidden_fields = hidden_fields or []
    changed_fields = getattr(instance, '_changed_fields', {})
    for field_name in changed_fields:
        if field_name not in excluded_fields:
            old_value = clean_field(field_name, changed_fields[field_name])
            new_value = clean_field(field_name, getattr(instance, field_name))
            emit_setting_changed_event(user, db_table, field_name, old_value, new_value)
    # Remove the now inaccurate _changed_fields attribute.
    if hasattr(instance, '_changed_fields'):
        del instance._changed_fields


def emit_setting_changed_event(user, db_table, setting_name, old_value, new_value):
    """Emits an event for a change in a setting.

    Args:
        user (User): the user that this setting is associated with.
        db_table (str): the name of the table that we're modifying.
        setting_name (str): the name of the setting being changed.
        old_value (object): the value before the change.
        new_value (object): the new value being saved.

    Returns:
        None
    """
    # Compute the maximum value length so that two copies can fit into the maximum event size
    # in addition to all the other fields recorded.
    max_value_length = settings.TRACK_MAX_EVENT / 4

    serialized_old_value, old_was_truncated = _get_truncated_setting_value(old_value, max_length=max_value_length)
    serialized_new_value, new_was_truncated = _get_truncated_setting_value(new_value, max_length=max_value_length)
    truncated_values = []
    if old_was_truncated:
        truncated_values.append("old")
    if new_was_truncated:
        truncated_values.append("new")
    tracker.emit(
        USER_SETTINGS_CHANGED_EVENT_NAME,
        {
            "setting": setting_name,
            "old": serialized_old_value,
            "new": serialized_new_value,
            "truncated": truncated_values,
            "user_id": user.id,
            "table": db_table,
        }
    )


def _get_truncated_setting_value(value, max_length=None):
    """
    Returns the truncated form of a setting value.

    Returns:
        truncated_value (object): the possibly truncated version of the value.
        was_truncated (bool): returns true if the serialized value was truncated.
    """
    if isinstance(value, basestring) and max_length is not None and len(value) > max_length:
        return value[0:max_length], True
    else:
        return value, False


# Taken from Django 1.8 source code because it's not supported in 1.4
def slugify(value):
    """Converts value into a string suitable for readable URLs.

    Converts to ASCII. Converts spaces to hyphens. Removes characters that
    aren't alphanumerics, underscores, or hyphens. Converts to lowercase.
    Also strips leading and trailing whitespace.

    Args:
        value (string): String to slugify.
    """
    value = force_unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return mark_safe(re.sub(r'[-\s]+', '-', value))


def generate_unique_readable_id(name, queryset, lookup_field):
    """Generates a unique readable id from name by appending a numeric suffix.

    Args:
        name (string): Name to generate the id from. May include spaces.
        queryset (QuerySet): QuerySet to check for uniqueness within.
        lookup_field (string): Field name on the model that corresponds to the
            unique identifier.

    Returns:
        string: generated unique identifier
    """
    candidate = slugify(name)
    conflicts = queryset.filter(**{lookup_field + '__startswith': candidate}).values_list(lookup_field, flat=True)

    if conflicts and candidate in conflicts:
        suffix = 2
        while True:
            new_id = candidate + '-' + str(suffix)
            if new_id not in conflicts:
                candidate = new_id
                break
            suffix += 1

    return candidate

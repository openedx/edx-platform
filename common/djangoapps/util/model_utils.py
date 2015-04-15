"""
Utilities for django models.
"""
from eventtracking import tracker

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields.related import RelatedField

from django_countries.fields import Country


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
            fields, or an empty dicit if the model is new
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


def emit_field_changed_events(instance, user, event_name, db_table, excluded_fields=None, hidden_fields=None):
    """
    For the given model instance, emit a setting changed event the fields that
    have changed since the last save.

    Note that this function expects that a `_changed_fields` dict has been set
    as an attribute on `instance` (see `get_changed_fields_dict`.

    Args:
        instance (Model instance): the model instance that is being saved
        user (User): the user that this instance is associated with
        event_name (str): the name of the event to be emitted
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
            tracker.emit(
                event_name,
                {
                    "setting": field_name,
                    'old': clean_field(field_name, changed_fields[field_name]),
                    'new': clean_field(field_name, getattr(instance, field_name)),
                    "user_id": user.id,
                    "table": db_table
                }
            )
    # Remove the now inaccurate _changed_fields attribute.
    if getattr(instance, '_changed_fields', None):
        del instance._changed_fields

"""
Add receivers for django signals, and feed data into the monitoring system.

If a model has a class attribute 'METRIC_TAGS' that is a list of strings,
those fields will be retrieved from the model instance, and added as tags to
the recorded metrics.
"""


from django.db.models.signals import post_save, post_delete, m2m_changed, post_init
from django.dispatch import receiver

import dogstats_wrapper as dog_stats_api


def _database_tags(action, sender, kwargs):  # pylint: disable=unused-argument
    """
    Return a tags for the sender and database used in django.db.models signals.

    Arguments:
        action (str): What action is being performed on the db model.
        sender (Model): What model class is the action being performed on.
        kwargs (dict): The kwargs passed by the model signal.
    """
    tags = _model_tags(kwargs, 'instance')
    tags.append(u'action:{}'.format(action))

    if 'using' in kwargs:
        tags.append(u'database:{}'.format(kwargs['using']))

    return tags


def _model_tags(kwargs, key):
    """
    Return a list of all tags for all attributes in kwargs[key].MODEL_TAGS,
    plus a tag for the model class.
    """
    if key not in kwargs:
        return []

    instance = kwargs[key]
    tags = [
        u'{}.{}:{}'.format(key, attr, getattr(instance, attr))
        for attr in getattr(instance, 'MODEL_TAGS', [])
    ]
    tags.append(u'model_class:{}'.format(instance.__class__.__name__))
    return tags


# @receiver(post_init, dispatch_uid='edxapp.monitoring.post_init_metrics')
# def post_init_metrics(sender, **kwargs):
#     """
#     Record the number of times that django models are instantiated.
#
#     Args:
#         sender (Model): The model class sending the signals.
#         using (str): The name of the database being used for this initialization (optional).
#         instance (Model instance): The instance being initialized (optional).
#     """
#     tags = _database_tags('initialized', sender, kwargs)
#
#     dog_stats_api.increment('edxapp.db.model', tags=tags)
#
#
# @receiver(post_save, dispatch_uid='edxapp.monitoring.post_save_metrics')
# def post_save_metrics(sender, **kwargs):
#     """
#     Record the number of times that django models are saved (created or updated).
#
#     Args:
#         sender (Model): The model class sending the signals.
#         using (str): The name of the database being used for this update (optional).
#         instance (Model instance): The instance being updated (optional).
#     """
#     action = 'created' if kwargs.pop('created', False) else 'updated'
#
#     tags = _database_tags(action, sender, kwargs)
#     dog_stats_api.increment('edxapp.db.model', tags=tags)
#
#
# @receiver(post_delete, dispatch_uid='edxapp.monitoring.post_delete_metrics')
# def post_delete_metrics(sender, **kwargs):
#     """
#     Record the number of times that django models are deleted.
#
#     Args:
#         sender (Model): The model class sending the signals.
#         using (str): The name of the database being used for this deletion (optional).
#         instance (Model instance): The instance being deleted (optional).
#     """
#     tags = _database_tags('deleted', sender, kwargs)
#
#     dog_stats_api.increment('edxapp.db.model', tags=tags)
#
#
# @receiver(m2m_changed, dispatch_uid='edxapp.monitoring.m2m_changed_metrics')
# def m2m_changed_metrics(sender, **kwargs):
#     """
#     Record the number of times that Many2Many fields are updated. This is separated
#     from post_save and post_delete, because it's signaled by the database model in
#     the middle of the Many2Many relationship, rather than either of the models
#     that are the relationship participants.
#
#     Args:
#         sender (Model): The model class in the middle of the Many2Many relationship.
#         action (str): The action being taken on this Many2Many relationship.
#         using (str): The name of the database being used for this deletion (optional).
#         instance (Model instance): The instance whose many-to-many relation is being modified.
#         model (Model class): The model of the class being added/removed/cleared from the relation.
#     """
#     if 'action' not in kwargs:
#         return
#
#     action = {
#         'post_add': 'm2m.added',
#         'post_remove': 'm2m.removed',
#         'post_clear': 'm2m.cleared',
#     }.get(kwargs['action'])
#
#     if not action:
#         return
#
#     tags = _database_tags(action, sender, kwargs)
#
#     if 'model' in kwargs:
#         tags.append('target_class:{}'.format(kwargs['model'].__name__))
#
#     pk_set = kwargs.get('pk_set', []) or []
#
#     dog_stats_api.increment(
#         'edxapp.db.model',
#         value=len(pk_set),
#         tags=tags
#     )
#
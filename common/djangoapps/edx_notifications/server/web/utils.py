"""
Assortment of helper utility methods
"""

from django.templatetags.static import static
from django.core.urlresolvers import reverse


class RecursiveDictionary(dict):
    """RecursiveDictionary provides the methods rec_update and iter_rec_update
    that can be used to update member dictionaries rather than overwriting
    them."""
    def rec_update(self, other, **third):
        """Recursively update the dictionary with the contents of other and
        third like dict.update() does - but don't overwrite sub-dictionaries.

        Example:
        >>> d = RecursiveDictionary({'foo': {'bar': 42}})
        >>> d.rec_update({'foo': {'baz': 36}})
        >>> d
        {'foo': {'baz': 36, 'bar': 42}}
        """
        try:
            iterator = other.iteritems()
        except AttributeError:
            iterator = other
        self.iter_rec_update(iterator)
        self.iter_rec_update(third.iteritems())

    def iter_rec_update(self, iterator):
        """
        Implements an iterator over the dictionary
        """
        for (key, value) in iterator:
            if key in self and \
               isinstance(self[key], dict) and isinstance(value, dict):
                self[key] = RecursiveDictionary(self[key])
                self[key].rec_update(value)
            else:
                self[key] = value

    def __repr__(self):
        return super(self.__class__, self).__repr__()


def get_template_path(template_name):
    """
    returns a full URL path to our template directory
    """

    return static(
        'edx_notifications/templates/{template_name}'.format(
            template_name=template_name
        )
    )


def get_audio_path(audio_name):
    """
    returns a full URL path to audio directory
    """

    return static(
        'edx_notifications/audio/{audio_name}'.format(
            audio_name=audio_name
        )
    )


def get_notifications_widget_context(override_context=None):
    """
    As a convenience method, this will return all required
    context properties that the notifications_widget.html Django template needs
    """

    context = RecursiveDictionary({
        'endpoints': {
            'unread_notification_count': (
                '{base_url}?read=False&unread=True'
            ). format(base_url=reverse('edx_notifications.consumer.notifications.count')),
            'mark_all_user_notifications_read': (
                '{base_url}'
            ). format(base_url=reverse('edx_notifications.consumer.notifications.mark_notifications_as_read')),
            'user_notifications_unread_only': (
                '{base_url}?read=False&unread=True'
            ). format(base_url=reverse('edx_notifications.consumer.notifications')),
            'user_notifications_all': (
                '{base_url}?read=True&unread=True'
            ). format(base_url=reverse('edx_notifications.consumer.notifications')),
            'user_notification_mark_read': (
                '{base_url}'
            ). format(base_url=reverse('edx_notifications.consumer.notifications.detail.no_param')),
            'user_notification_preferences': (
                '{base_url}'
            ). format(base_url=reverse('edx_notifications.consumer.user_preferences')),
            'user_notification_preferences_detail': (
                '{base_url}'
            ). format(base_url=reverse('edx_notifications.consumer.user_preferences.detail.no_param')),
            'notification_preferences_all': (
                '{base_url}'
            ).format(base_url=reverse('edx_notifications.consumer.notification_preferences')),
            'renderer_templates_urls': reverse('edx_notifications.consumer.renderers.templates'),
        },
        'global_variables': {
            'app_name': 'Your App Name Here',
            'always_show_dates_on_unread': True,
        },
        'refresh_watchers': {
            'name': 'none',
            'args': {},
        },
        'view_audios': {
            'notification_alert': get_audio_path('notification_alert.mp3'),
        },
        # global notifications by default, callers should override this if they want to only
        # display notifications within a namespace
        'namespace': None,
    })

    if override_context:
        context.rec_update(override_context)

    return context

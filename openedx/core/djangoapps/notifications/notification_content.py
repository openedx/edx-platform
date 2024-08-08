"""
Helper functions for overriding notification content for given notification type.
"""


def get_notification_type_content_function(notification_type):
    """
        Returns the content function for the given notification if it exists.
    """
    try:
        return globals()[f"get_{notification_type}_notification_content"]
    except KeyError:
        return None


def get_notification_content_with_author_pronoun(notification_type, context):
    """
        Helper function to get notification content with author's pronoun.
    """
    html_tags_context = {
        'strong': 'strong',
        'p': 'p',
    }
    notification_type_content_template = notification_type.get('content_template', None)
    if 'author_pronoun' in context:
        context['author_name'] = context['author_pronoun']
    if notification_type_content_template:
        return notification_type_content_template.format(**context, **html_tags_context)
    return ''


# Returns notification content for the new_comment notification.
get_new_comment_notification_content = get_notification_content_with_author_pronoun
# Returns notification content for the comment_on_followed_post notification.
get_comment_on_followed_post_notification_content = get_notification_content_with_author_pronoun

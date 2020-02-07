from django.template import Library

register = Library()


@register.inclusion_tag('features/badging/badge_progress.html', takes_context=True)
def badge_progress(context):
    return {
        'community_id': context.get('community_id'),
        'badges': context.get('badges')
    }

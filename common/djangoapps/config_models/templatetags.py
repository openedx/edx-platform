"""
Override the submit_row template tag to remove all save buttons from the
admin dashboard change view if the context has readonly marked in it.
"""

from django.contrib.admin.templatetags.admin_modify import register
from django.contrib.admin.templatetags.admin_modify import submit_row as original_submit_row


@register.inclusion_tag('admin/submit_line.html', takes_context=True)
def submit_row(context):
    """
    Overrides 'django.contrib.admin.templatetags.admin_modify.submit_row'.

    Manipulates the context going into that function by hiding all of the buttons
    in the submit row if the key `readonly` is set in the context.
    """
    ctx = original_submit_row(context)

    if context.get('readonly', False):
        ctx.update({
            'show_delete_link': False,
            'show_save_as_new': False,
            'show_save_and_add_another': False,
            'show_save_and_continue': False,
            'show_save': False,
        })
    else:
        return ctx

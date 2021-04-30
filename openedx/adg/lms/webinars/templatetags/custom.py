"""
Custom template tags for 'webinars' app
"""
from django import template
from django.contrib.admin.templatetags.admin_modify import submit_row
from django.contrib.admin.templatetags.base import InclusionAdminNode

register = template.Library()


@register.tag(name='submit_row')
def submit_row_tag(parser, token):
    return InclusionAdminNode(parser, token, func=submit_row, template_name='submit_line.html')


@register.inclusion_tag('dialogs/confirm.html')
def confirm_dialogue():
    pass

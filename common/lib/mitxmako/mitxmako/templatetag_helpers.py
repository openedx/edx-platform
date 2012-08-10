from django.template import loader
from django.template.base import Template, Context
from django.template.loader import get_template, select_template


def render_inclusion(func, file_name, *args, **kwargs):
    _dict = func(*args, **kwargs)
    if isinstance(file_name, Template):
        t = file_name
    elif not isinstance(file_name, basestring) and is_iterable(file_name):
        t = select_template(file_name)
    else:
        t = get_template(file_name)
        
    nodelist = t.nodelist
    
    new_context = Context(_dict)
    #  **{
    #     'autoescape': context.autoescape,
    #     'current_app': context.current_app,
    #     'use_l10n': context.use_l10n,
    #     'use_tz': context.use_tz,
    # })
    return nodelist.render(new_context)
    
def django_template_include(file_name, mako_context):
    dictionary = dict( mako_context )
    return loader.render_to_string(file_name, dictionary=dictionary)

from django.template import loader
from django.template.base import Template, Context
from django.template.loader import get_template, select_template


def django_template_include(file_name, mako_context):
    """
    This can be used within a mako template to include a django template
    in the way that a django-style {% include %} does. Pass it context
    which can be the mako context ('context') or a dictionary.
    """

    dictionary = dict(mako_context)
    return loader.render_to_string(file_name, dictionary=dictionary)


def render_inclusion(func, file_name, takes_context, django_context, *args, **kwargs):
    """
    This allows a mako template to call a template tag function (written
    for django templates) that is an "inclusion tag". These functions are
    decorated with @register.inclusion_tag.

    -func: This is the function that is registered as an inclusion tag.
    You must import it directly using a python import statement.
    -file_name: This is the filename of the template, passed into the
    @register.inclusion_tag statement.
    -takes_context: This is a parameter of the @register.inclusion_tag.
    -django_context: This is an instance of the django context. If this
    is a mako template rendered through the regular django rendering calls,
    a copy of the django context is available as 'django_context'.
    -*args and **kwargs are the arguments to func.
    """

    if takes_context:
        args = [django_context] + list(args)

    _dict = func(*args, **kwargs)
    if isinstance(file_name, Template):
        t = file_name
    elif not isinstance(file_name, basestring) and is_iterable(file_name):
        t = select_template(file_name)
    else:
        t = get_template(file_name)

    nodelist = t.nodelist

    new_context = Context(_dict)
    csrf_token = django_context.get('csrf_token', None)
    if csrf_token is not None:
        new_context['csrf_token'] = csrf_token

    return nodelist.render(new_context)

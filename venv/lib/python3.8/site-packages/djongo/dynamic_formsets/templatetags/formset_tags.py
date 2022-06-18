from django import template
from djongo.models.fields import ArrayFormField


register = template.Library()

@register.simple_tag
def formset_prefixes(admin_form):
    ret = []
    for bf in admin_form.form.fields.values():
        if isinstance(bf, ArrayFormField):
            ret.append(bf.name)

    return ret

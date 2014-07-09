from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError

def validate_cedula(cedula):
    """
    Validador de cedula de Ecuador
    """
    values = [int(cedula[x])*(2-(x%2)) for x in range(9)]
    total = sum(map(lambda x: x > 9 and x - 9 or x, values))
    check = 10 - (total - (10 * (total  / 10)))
    if not int(cedula[9])==int(str(check)[-1:]):
        raise ValidationError(_('Invalid ID'), code='invalid')

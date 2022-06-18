import re
import functools
import operator


# from jaraco.functools
def compose(*funcs):
    compose_two = lambda f1, f2: lambda *args, **kwargs: f1(f2(*args, **kwargs))  # noqa
    return functools.reduce(compose_two, funcs)


def compound(mode):
    """
    Support multiple, comma-separated Unix chmod symbolic modes.

    >>> oct(compound('a=r,u+w')(0))
    '0o644'
    """
    return compose(*map(simple, reversed(mode.split(','))))


def simple(mode):
    """
    Convert a Unix chmod symbolic mode like ``'ugo+rwx'`` to a function
    suitable for applying to a mask to affect that change.

    >>> mask = simple('ugo+rwx')
    >>> mask(0o554) == 0o777
    True

    >>> simple('go-x')(0o777) == 0o766
    True

    >>> simple('o-x')(0o445) == 0o444
    True

    >>> simple('a+x')(0) == 0o111
    True

    >>> simple('a=rw')(0o057) == 0o666
    True

    >>> simple('u=x')(0o666) == 0o166
    True

    >>> simple('g=')(0o157) == 0o107
    True

    >>> simple('gobbledeegook')
    Traceback (most recent call last):
    ValueError: ('Unrecognized symbolic mode', 'gobbledeegook')
    """
    # parse the symbolic mode
    parsed = re.match('(?P<who>[ugoa]+)(?P<op>[-+=])(?P<what>[rwx]*)$', mode)
    if not parsed:
        raise ValueError("Unrecognized symbolic mode", mode)

    # generate a mask representing the specified permission
    spec_map = dict(r=4, w=2, x=1)
    specs = (spec_map[perm] for perm in parsed.group('what'))
    spec = functools.reduce(operator.or_, specs, 0)

    # now apply spec to each subject in who
    shift_map = dict(u=6, g=3, o=0)
    who = parsed.group('who').replace('a', 'ugo')
    masks = (spec << shift_map[subj] for subj in who)
    mask = functools.reduce(operator.or_, masks)

    op = parsed.group('op')

    # if op is -, invert the mask
    if op == '-':
        mask ^= 0o777

    # if op is =, retain extant values for unreferenced subjects
    if op == '=':
        masks = (0o7 << shift_map[subj] for subj in who)
        retain = functools.reduce(operator.or_, masks) ^ 0o777

    op_map = {
        '+': operator.or_,
        '-': operator.and_,
        '=': lambda mask, target: target & retain ^ mask,
    }
    return functools.partial(op_map[op], mask)

#!/usr/bin/python
#
# File:  mitx/lib/loncapa/loncapa_check.py
#
# Python functions which duplicate the standard comparison functions available to LON-CAPA problems.
# Used in translating LON-CAPA problems to i4x problem specification language.

from __future__ import division
import random
import math


def lc_random(lower, upper, stepsize):
    '''
    like random.randrange but lower and upper can be non-integer
    '''
    nstep = int((upper - lower) / (1.0 * stepsize))
    choices = [lower + x * stepsize for x in range(nstep)]
    return random.choice(choices)


def lc_choose(index, *args):
    '''
    return args[index]
    '''
    try:
        return args[int(index) - 1]
    except Exception, err:
        pass
    if len(args):
        return args[0]
    raise Exception(
        "loncapa_check.lc_choose error, index={index}, args={args}".format(
            index=index,
            args=args,
        )
    )

deg2rad = math.pi / 180.0
rad2deg = 180.0 / math.pi

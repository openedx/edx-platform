#!/usr/bin/python
#
# File:  mitx/lib/loncapa/loncapa_check.py
#
# Python functions which duplicate the standard comparison functions available to LON-CAPA problems.
# Used in translating LON-CAPA problems to i4x problem specification language.

import random

def lc_random(lower,upper,stepsize):
    '''
    like random.randrange but lower and upper can be non-integer
    '''
    nstep = int((upper-lower)/(1.0*stepsize))
    choices = [lower+x*stepsize for x in range(nstep)]
    return random.choice(choices)


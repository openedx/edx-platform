"""
Provide the mathematical functions that numpy doesn't.

Specifically, the secant/cosecant/cotangents and their inverses and
hyperbolic counterparts
"""
import numpy


# Normal Trig
def sec(arg):
    """
    Secant
    """
    return 1 / numpy.cos(arg)


def csc(arg):
    """
    Cosecant
    """
    return 1 / numpy.sin(arg)


def cot(arg):
    """
    Cotangent
    """
    return 1 / numpy.tan(arg)


# Inverse Trig
# http://en.wikipedia.org/wiki/Inverse_trigonometric_functions#Relationships_among_the_inverse_trigonometric_functions
def arcsec(val):
    """
    Inverse secant
    """
    return numpy.arccos(1. / val)


def arccsc(val):
    """
    Inverse cosecant
    """
    return numpy.arcsin(1. / val)


def arccot(val):
    """
    Inverse cotangent
    """
    if numpy.real(val) < 0:
        return -numpy.pi / 2 - numpy.arctan(val)
    else:
        return numpy.pi / 2 - numpy.arctan(val)


# Hyperbolic Trig
def sech(arg):
    """
    Hyperbolic secant
    """
    return 1 / numpy.cosh(arg)


def csch(arg):
    """
    Hyperbolic cosecant
    """
    return 1 / numpy.sinh(arg)


def coth(arg):
    """
    Hyperbolic cotangent
    """
    return 1 / numpy.tanh(arg)


# And their inverses
def arcsech(val):
    """
    Inverse hyperbolic secant
    """
    return numpy.arccosh(1. / val)


def arccsch(val):
    """
    Inverse hyperbolic cosecant
    """
    return numpy.arcsinh(1. / val)


def arccoth(val):
    """
    Inverse hyperbolic cotangent
    """
    return numpy.arctanh(1. / val)

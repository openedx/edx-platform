"""
Tests of our testing tools.

"The only code you have to test is the code you want to work."
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from abc import ABCMeta, abstractmethod
import unittest

import six


from xblock.test.tools import unabc


class Abstract(six.with_metaclass(ABCMeta, object)):
    """Our test subject: an abstract class with two abstract methods."""

    def concrete(self, arg):
        """This is available as-is on all subclasses."""
        return arg * arg + 3

    @abstractmethod
    def absmeth1(self):
        """Subclasses 'must' implement this."""
        raise NotImplementedError

    @abstractmethod
    def absmeth2(self):
        """Everyone 'should' provide an implementation of this."""
        raise NotImplementedError


@unabc                      # pylint: disable=abstract-method
class ForceConcrete(Abstract):
    """Ha-ha! Can't make me implement what I don't want to!"""
    pass


@unabc("Sorry, no {}")      # pylint: disable=abstract-method
class ForceConcreteMessage(Abstract):
    """I'll implement what I want to implement."""
    pass


class TestUnAbc(unittest.TestCase):
    """Test the @unabc decorator."""

    def test_cant_abstract(self):
        with six.assertRaisesRegex(self, TypeError, r"Can't instantiate .*"):
            Abstract()

    def test_concrete(self):
        conc = ForceConcrete()
        self.assertEqual(conc.concrete(10), 103)

    def test_concrete_absmeth(self):
        conc = ForceConcrete()
        with six.assertRaisesRegex(self, NotImplementedError, r"absmeth1 isn't implemented"):
            conc.absmeth1()
        with six.assertRaisesRegex(self, NotImplementedError, r"absmeth2 isn't implemented"):
            conc.absmeth2()

    def test_concrete_absmeth_message(self):
        conc = ForceConcreteMessage()
        with six.assertRaisesRegex(self, NotImplementedError, r"Sorry, no absmeth1"):
            conc.absmeth1()
        with six.assertRaisesRegex(self, NotImplementedError, r"Sorry, no absmeth2"):
            conc.absmeth2()

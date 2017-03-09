#-*- coding: ISO-8859-1 -*-
# pysqlite2/test/__init__.py: the package containing the test suite
#
# Copyright (C) 2004-2015 Gerhard Häring <gh@ghaering.de>
#
# This file is part of pysqlite.
#
# This software is provided 'as-is', without any express or implied
# warranty.  In no event will the authors be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.

import unittest

from pysqlite2.test import dbapi, types, userfunctions, factory, transactions,\
    hooks, regression, dump

def suite():
    tests = [dbapi.suite(), types.suite(), userfunctions.suite(),
      factory.suite(), transactions.suite(), hooks.suite(), regression.suite(), dump.suite()]

    return unittest.TestSuite(tuple(tests))

def test():
    runner = unittest.TextTestRunner()
    return runner.run(suite())

#!/usr/bin/env python
#
# Cross-compile and build pysqlite installers for win32 on Linux or Mac OS X.
#
# The way this works is very ugly, but hey, it *works*!  And I didn't have to
# reinvent the wheel using NSIS.

import os
import sys
import urllib
import zipfile

from setup import get_amalgamation

# Cross-compiler
if sys.platform == "darwin":
    CC = "/usr/local/i386-mingw32-4.3.0/bin/i386-mingw32-gcc"
    LIBDIR = "lib.macosx-10.6-i386-2.5"
    STRIP = "/usr/local/i386-mingw32-4.3.0/bin/i386-mingw32-gcc --strip-all"
else:
    CC = "/usr/bin/i586-mingw32msvc-gcc"
    LIBDIR = "lib.linux-i686-2.5"
    STRIP = "strip --strip-all"

# Optimization settings
OPT = "-O2"

# pysqlite sources + SQLite amalgamation
SRC = "src/module.c src/connection.c src/cursor.c src/cache.c src/microprotocols.c src/prepare_protocol.c src/statement.c src/util.c src/row.c amalgamation/sqlite3.c"

# You will need to fetch these from
# https://pyext-cross.pysqlite.googlecode.com/hg/
CROSS_TOOLS = "../pysqlite-pyext-cross"

def execute(cmd):
    print cmd
    return os.system(cmd)

def compile_module(pyver):
    VER = pyver.replace(".", "")
    INC = "%s/python%s/include" % (CROSS_TOOLS, VER)
    vars = locals()
    vars.update(globals())
    cmd = '%(CC)s -mno-cygwin %(OPT)s -mdll -DMODULE_NAME=\\"pysqlite2._sqlite\\" -DSQLITE_ENABLE_RTREE=1 -DSQLITE_ENABLE_FTS3=1 -I amalgamation -I %(INC)s -I . %(SRC)s -L %(CROSS_TOOLS)s/python%(VER)s/libs -lpython%(VER)s -o build/%(LIBDIR)s/pysqlite2/_sqlite.pyd' % vars
    execute(cmd)
    execute("%(STRIP)s build/%(LIBDIR)s/pysqlite2/_sqlite.pyd" % vars)

def main():
    vars = locals()
    vars.update(globals())
    get_amalgamation()
    for ver in ["2.5", "2.6", "2.7"]:
        execute("rm -rf build")
        # First, compile the host version. This is just to get the .py files in place.
        execute("python2.5 setup.py build")
        # Yes, now delete the host extension module. What a waste of time.
        os.unlink("build/%(LIBDIR)s/pysqlite2/_sqlite.so" % vars)
        # Cross-compile win32 extension module.
        compile_module(ver)
        # Prepare for target Python version.
        libdir_ver = LIBDIR[:-3] + ver
        os.rename("build/%(LIBDIR)s" % vars, "build/" + libdir_ver)
        # And create the installer!
        os.putenv("PYEXT_CROSS", CROSS_TOOLS)
        execute("python2.5 setup.py cross_bdist_wininst --skip-build --target-version=" + ver)

if __name__ == "__main__":
    main()

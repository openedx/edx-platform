=======================
Vendored library policy
=======================

To simplify Bleach development, we're now vendoring certain libraries that
we use.

Vendored libraries must follow these rules:

1. Vendored libraries must be pure Python--no compiling.
2. Source code for the libary is included in this directory.
3. License must be included in this repo and in the Bleach distribution.
4. Requirements of the library become requirements of Bleach.
5. No modifications to the library may be made.


Adding/Updating a vendored library
==================================

Way to vendor a library or update a version:

1. Update ``vendor.txt`` with the library, version, and hash. You can use 
   `hashin <https://pypi.org/project/hashin/>`_.
2. Remove all old files and directories of the old version.
3. Run ``pip_install_vendor.sh`` and check everything it produced in including
   the ``.dist-info`` directory and contents.


Reviewing a change involving a vendored library
===============================================

Way to verify a vendored library addition/update:

1. Pull down the branch.
2. Delete all the old files and directories of the old version.
3. Run ``pip_install_vendor.sh``.
4. Run ``git diff`` and verify there are no changes.

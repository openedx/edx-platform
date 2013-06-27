*******************************************
Chemistry modules
*******************************************

.. module:: chem

Miller
======

.. automodule:: chem.miller
    :members:
    :show-inheritance:

UI part and inputtypes
----------------------
Miller module is used in the system in crystallography problems.
Crystallography is a class in :mod:`capa` inputtypes module.
It uses *crystallography.html* for rendering and **crystallography.js**
for UI part.

Documentation from **crystallography.js**::

    For a crystallographic problem of the type

     Given a plane definition via miller indexes, specify it by plotting points on the edges
     of a 3D cube. Additionally, select the correct Bravais cubic lattice type depending on the
     physical crystal mentioned in the problem.

    we create a graph which contains a cube, and a 3D Cartesian coordinate system. The interface
    will allow to plot 3 points anywhere along the edges of the cube, and select which type of
    Bravais lattice should be displayed along with the basic cube outline.

    When 3 points are successfully plotted, an intersection of the resulting plane (defined by
    the 3 plotted points), and the cube, will be automatically displayed for clarity.

    After lotting the three points, it is possible to continue plotting additional points. By
    doing so, the point that was plotted first (from the three that already exist), will be
    removed, and the new point will be added. The intersection of the resulting new plane and
    the cube will be redrawn.

    The UI has been designed in such a way, that the user is able to determine which point will
    be removed next (if adding a new point). This is achieved via filling the to-be-removed point
    with a different color.



Chemcalc
========

.. automodule:: chem.chemcalc
    :members:
    :show-inheritance:

Chemtools
=========

.. automodule:: chem.chemtools
    :members:
    :show-inheritance:


Tests
=====

.. automodule:: chem.tests
    :members:
    :show-inheritance:



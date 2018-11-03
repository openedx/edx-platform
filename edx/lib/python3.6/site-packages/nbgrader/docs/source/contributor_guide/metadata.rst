JSON Metadata Format
====================

nbgrader relies on metadata stored in the JSON notebook source. When you create
a notebook using the "Create Assignment" extension, this extension saves
various keys into the metadata that it then relies on during the steps of
``nbgrader assign``. The ``nbgrader assign`` command also adds new metadata to
the notebooks, which is used by ``nbgrader validate`` and ``nbgrader
autograde``.

The metadata is always stored at the cell level, in the cell's ``metadata`` field, under a dictionary called ``nbgrader``. This makes the notebook source look like::

    {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {
                    "nbgrader": {
                        ...
                    }
                },
                "source": ["an example cell\n"]
            },
            ... more cells ...
        ],
        ... other notebook information ...
    }

Details about the metadata are given below.

Version 1
---------

The metadata may contain the following keys:

.. data:: schema_version

    The version of the metadata schema. Defaults to 1.

.. data:: grade

    Added by the "Create Assignment" extension.

    Whether the cell should be graded (which essentially means whether it
    gets a point value). This should be true for manually graded answer
    cells and for autograder test cells.

.. data:: solution

    Added by the "Create Assignment" extension.

    Whether the cell is a solution cell (which essentially means whether
    students should put their answers in it or not). This should be true
    for manually graded answer cells and autograded answer cells.

.. data:: locked

    Added by the "Create Assignment" extension.

    Whether nbgrader should prevent the cell from being edited. This should
    be true for autograder test cells and any other cells that are marked
    as locked/read-only in the create assignment interface.

.. data:: grade_id

    Added by the "Create Assignment" extension.

    This is the nbgrader cell id so that nbgrader can track its contents,
    outputs, etc.

.. data:: points

    Added by the "Create Assignment" extension.

    This is the number of points that a cell is worth. It should only be
    set if ``grade`` is also set to true. The number of points must be greater
    than or equal to zero.

.. data:: checksum

    Added by ``nbgrader assign``.

    This is the checksum of the cell's contents that can then be used by
    ``nbgrader validate`` and ``nbgrader autograde`` to determine whether
    the student has edited the cell.

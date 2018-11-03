Documentation
=============

The source for the documentation can be found in the ``docs/source``
directory of this repository. These source files are a combination of
ReStructured Text (rst) and Jupyter notebooks.

Editing source files
--------------------

* ReStructured Text: The rst files should be fairly straightforward to edit. Here is
  `a quick reference of rst syntax <http://docutils.sourceforge.net/docs/user/rst/quickref.html>`_.
  Some of the rst files also use `Sphinx autodoc <http://sphinx-doc.org/ext/autodoc.html>`_.

* Jupyter Notebooks: The Jupyter notebooks are written in Python and should be written so that
  they are compatible with both Python 2 and Python 3. If you need
  to reference another part of the documentation from a notebook, you will need
  to put that reference in a **raw** cell in the notebook, **not** a markdown
  cell.

Adding a new file to documentation
----------------------------------
If you add a new file (either rst or ipynb) make sure to link to it from the
relevant ``index.rst``.

Additionally, if you are adding a new notebook in the user guide, please add
the rst version of it to ``.gitignore``.


Building documentation locally
------------------------------

.. warning::

  Building the docs is not currently well-supported on Windows. This is because one of
  the dependencies (enchant) does not install easily in Windows.

If you have made changes to the user guide or other notebooks that need to be
executed, please make sure you re-run all the documentation before committing.
While the documentation gets built automatically on Read The Docs, the notebooks do **not** get execute by Read The Docs -- they must be executed manually.
However, executing the notebooks is easy to do!

Our docs are built with `nbconvert <https://nbconvert.readthedocs.io/en/latest/>`_,
`Pandoc <http://pandoc.org/>`_, and `Sphinx <http://sphinx-doc.org/>`_.
To build the docs locally, run the following command::

    invoke docs

This will perform a few different steps:

1. The notebooks are executed and converted to rst or html (the actual
   documentation notebooks will be converted to rst, and example notebooks will
   be converted to html) using the ``build_docs.py`` script.
2. The command line documentation is automatically generated using the
   ``autogen_command_line.py`` and ``autogen_config.py`` scripts.
3. The rst files are converted to html using Sphinx.

After running ``invoke docs``, the resultant HTML files will be in
``docs/build/html``. You can open these files in your browser to preview what
the documentation will look like (note, however, that the theme used by Read
The Docs is different from the default Sphinx theme, so the styling will look
different).

Automatic builds
----------------
When a commit is made on the ``master`` branch, documentation is automatically
built by Read The Docs and rendered at
`nbgrader.readthedocs.org <https://nbgrader.readthedocs.io>`_.

**********************************************
Xml format of conditional module [xmodule]
**********************************************

.. module:: conditional_module

Format description
==================

The main tag of Conditional module input is::

    <conditional> ... </conditional>

``conditional`` can include any number of any xmodule tags (``html``, ``video``, ``poll``, etc.) or ``show`` tags.

conditional tag
---------------

The main container for a single instance of Conditional module. The following attributes can
be specified for this tag::

    sources - location id of required modules, separated by ';'
    message - message for case, where one of conditions  not passed.

    completed - map to `is_completed` module method
    attempted - map to `is_attempted` module method
    poll_answer - map to `poll_answer` module attribute
    voted - map to `voted` module attribute

show tag
--------

Like unix symlink to some set of xmodules. The following attributes can
be specified for this tag::

    sources - location id of required modules, separated by ';'

Example
=======

Examples of draggables that can't be reused
-------------------------------------------

.. code-block:: xml
        <conditional sources="i4x://MITx/0.000x/poll_question/first_real_poll_seq_with_reset" poll_answer="man"
        message="{link} must be answered for this to become visible.">
        <html>
            <h2>You see this, cause your vote value for "First question" was "man"</h2>
            <h2>Code example:</h2>
            <pre style="border: 1px solid; padding: 10px;">
            </pre>
        </html>
        </conditional>


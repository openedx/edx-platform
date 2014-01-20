**********************************************
Xml format of poll module [xmodule]
**********************************************

.. module:: poll_module

Format description
==================

The main tag of Poll module input is:

.. code-block:: xml

    <poll_question> ... </poll_question>

``poll_question`` can include any number of the following tags:
any xml and ``answer`` tag. All inner xml, except for ``answer`` tags, we call "question".

poll_question tag
-----------------

Xmodule for creating poll functionality - voting system. The following attributes can
be specified for this tag::

    name - Name of xmodule.
    [display_name| AUTOGENERATE] - Display name of xmodule. When this attribute is not defined - display name autogenerate with some hash.
    [reset | False] - Can reset/revote many time (value = True/False)


answer tag
----------

Define one of the possible answer for poll module. The following attributes can
be specified for this tag::

    id - unique identifier (using to identify the different answers)

Inner text - Display text for answer choice.

Example
=======

Examples of poll
----------------

.. code-block:: xml

    <poll_question name="second_question" display_name="Second question">
        <h3>Age</h3>
        <p>How old are you?</p>
        <answer id="less18">&lt; 18</answer>
        <answer id="10_25">from 10 to 25</answer>
        <answer id="more25">&gt; 25</answer>
    </poll_question>

Examples of poll with unable reset functionality
------------------------------------------------

.. code-block:: xml

    <poll_question name="first_question_with_reset" display_name="First question with reset"
        reset="True">
        <h3>Your gender</h3>
        <p>You are man or woman?</p>
        <answer id="man">Man</answer>
        <answer id="woman">Woman</answer>
    </poll_question>
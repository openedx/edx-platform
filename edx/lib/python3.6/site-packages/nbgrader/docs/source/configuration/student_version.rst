Customizing how the student version of an assignment looks
==========================================================

.. seealso::

    :doc:`/user_guide/creating_and_grading_assignments`
        Documentation for ``nbgrader assign``, ``nbgrader autograde``, and ``nbgrader feedback``.

    :doc:`/command_line_tools/nbgrader-assign`
        Command line options for ``nbgrader assign``

    :doc:`config_options`
        Details on ``nbgrader_config.py``

"Autograded answer" cells
-------------------------

Default behavior
^^^^^^^^^^^^^^^^

By default, ``nbgrader assign`` will replace regions beginning with
``BEGIN SOLUTION`` and ``END SOLUTION`` comment delimeters with:

.. code:: python

    # YOUR CODE HERE
    raise NotImplementedError

Note that the code stubs will be properly indented based on the indentation of
the solution delimeters. For example, if your original code is:

.. code:: python

    def foo(bar):
        """Prints `bar`."""
        ### BEGIN SOLUTION
        print(bar)
        ### END SOLUTION

then the solution region will become:

.. code:: python

    def foo(bar):
        """Prints `bar`."""
        # YOUR CODE HERE
        raise NotImplementedError

These solution comment delimeters are independent of the programming language
used and the number of comment characters used in the source notebook. For
example, this default will work for both ``Python``:

.. code:: python

    def foo(bar):
        """Prints `bar`."""
        ### BEGIN SOLUTION
        print(bar)
        ### END SOLUTION

and ``JavaScript``:

.. code-block:: javascript

    function foo (bar){
        // BEGIN SOLUTION
        console.log(bar);
        // END SOLUTION
    }

If the solution delimeters aren't present, nbgrader will replace the
entire contents of all :ref:`manually graded cells <manually-graded-cells>` and
:ref:`autograded cells <autograded-answer-cells>` with the above code stub (if
it is a code cell) or a text stub (if it is a Markdown cell), the default of
which is ``YOUR ANSWER HERE``.


Changing the defaults
^^^^^^^^^^^^^^^^^^^^^

If you need to change these defaults (e.g., if your class doesn't use Python,
or isn't taught in English), the values can be configured in the
:doc:`nbgrader_config.py <config_options>` file. Most relevant is the
``code_stub`` option to the ``ClearSolutions`` preprocessor, which is the part
of nbgrader that actually clears the solutions when producing the student
version of the notebook.

The solution delimeters are independent of the programming language used,
however the code stub depends on the language of the notebook,
the default of which is Python. You can specify solution delimeters for any
languages you want by setting the ``ClearSolutions.begin_solution_delimeter``,
``ClearSolutions.end_solution_delimeter``, and ``ClearSolutions.code_stub``
config options, thus allowing you to include notebooks of different languages
within the same assignment:

.. code:: python

    c = get_config()
    c.ClearSolutions.begin_solution_delimeter = "BEGIN MY SOLUTION"
    c.ClearSolutions.end_solution_delimeter = "END MY SOLUTION"
    c.ClearSolutions.code_stub = {
        "python": "# your code here\nraise NotImplementedError",
        "javascript": "// your code here\nthrow new Error();"
    }

.. note::

    Note that the code stub itself doesn't *have* to cause an error (though
    that is the easiest thing to do, in my opinion) -- it all depends on how
    you write your test cases. The only constraint is that when autograding
    happens, the behavior is such that:

    1. If the tests pass, the student gets full credit.
    2. If the tests fail, the student gets no credit.

    So if the student hasn't given an answer, the tests should ideally fail by
    default. How they fail is totally up to how you write your test cases.

Similarly, the text stub that the contents of Markdown cells get replaced with
can be configured through the ``ClearSolutions.text_stub`` option:

.. code:: python

    c.ClearSolutions.text_stub = "Please replace this text with your response."


"Autograder tests" cells with hidden tests
------------------------------------------

.. versionadded:: 0.5.0

Default behavior
^^^^^^^^^^^^^^^^

By default, ``nbgrader assign`` will remove tests wrapped within the
``BEGIN HIDDEN TESTS`` and ``END HIDDEN TESTS`` comment delimeters, for
example:

.. code:: python

    assert squares(1) = [1]
    ### BEGIN HIDDEN TESTS
    assert squares(2) = [1, 4]
    ### END HIDDEN TESTS

will be released as:

.. code:: python

    assert squares(1) = [1]

These comment delimeters are independent of the programming language used and
the number of comment characters used in the source notebook. For example, this
default will work for both ``Python``:

.. code:: python

    assert squares(1) = [1]
    ### BEGIN HIDDEN TESTS
    assert squares(2) = [1, 4]
    ### END HIDDEN TESTS

and ``JavaScript``:

.. code-block:: javascript

    function assert(answer, expected, msg) {
        correct = ...;  // validate the answer
        if (!correct) {
            throw msg || "Incorrect answer";
        }
    }

    assert(squares(1), [1]);
    // BEGIN HIDDEN TESTS
    assert(squares(2), [1, 4]);
    // END HIDDEN TESTS

.. note::

    Keep in mind that wrapping all tests (for an "Autograder tests" cell) in
    this special syntax will remove all these tests in the release version and
    the students will only see a blank cell. It is recommended to have at least
    one or more visible tests, or a comment in the cell for the students to
    see.

Changing the defaults
^^^^^^^^^^^^^^^^^^^^^

If you need to change these defaults (e.g., if your class isn't taught in
English), the values can be configured in the :doc:`nbgrader_config.py
<config_options>` file. Most relevant are the options to the
``ClearHiddenTests`` preprocessor, which is the part of nbgrader that actually
removes the tests when producing the student version of the notebook.

You can specify hidden test delimeters you want by setting the
``ClearHiddenTests.begin_test_delimeter`` and
``ClearHiddenTests.end_test_delimeter`` config options:

.. code:: python

    c = get_config()
    c.ClearHiddenTests.begin_test_delimeter = "VERBORGE TOESTE BEGIN"
    c.ClearHiddenTests.end_test_delimeter = "VERBORGE TOESTE EINDIG"


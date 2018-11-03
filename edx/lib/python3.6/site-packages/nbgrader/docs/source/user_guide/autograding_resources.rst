.. _autograding-resources:

Autograding resources
=====================

Most coding problems can be autograded. Problems that involve writing fruitful
functions can be graded more easily than others. These types of problems can be
graded by writing test functions that compare output values. Instructors should
make sure that all edge cases are captured when creating test cases. Problems
that require writing void functions are harder to autograde and may involve
checking stdout, depending on the nature of the problem.

Here, we provide some best-practices and tips for writing autograder tests. If
you have additional wisdom to add, please do open a PR (or even just an issue)
on the nbgrader repository!


Tips for writing good test cases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test each function/feature in isolation. If a problem contains many
functions or parts, write cases that test each of these functions
individually. Testing one function at a time makes it easier for you to
track an error.

Organize test cases consistently. It can be helpful to arrange and group
your test cases with comments.

Try to cover all edge cases. If you have a function that can take in a
certain range of inputs, test the boundaries of this range. Test cases
should also check for different lengths, different cases of strings,
integers and floats, or different ranges when applicable.

Example
^^^^^^^

Problem: Write a function ``isAnagram()`` that takes 2 strings, and
returns True if the two given strings are anagrams of each other. Your
function should ignore cases, spaces, and all punctuation. So your
function should identify "HeLLo!" and "hOlle" as anagrams.

Test cases:

.. code:: python

    from nose.tools import assert_equal

    # standard True cases
    assert_equal(isAnagram('hi', 'hi'), True)
    assert_equal(isAnagram('pat', 'tap'), True)
    assert_equal(isAnagram('left', 'felt'), True)

    # ignore punctuation, spaces, and different cases (upper/lower)
    assert_equal(isAnagram('hi', 'hi!'), True)
    assert_equal(isAnagram('HI', 'hi'), True)
    assert_equal(isAnagram('hi', 'HI'), True)
    assert_equal(isAnagram('He llo', '?hello'), True)

    # False cases
    assert_equal(isAnagram('hi', 'h'), False)
    assert_equal(isAnagram('apple', 'aple'), False)
    assert_equal(isAnagram('aaaaaa', 'aaaa'), False)


Partially autograding, partially manually grading
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When test cases are not enough to determine the correctness of a
student's solution, you can autograde them to make sure that there are
no errors in the execution or the solution. You still need to manually
look at the solutions to determine whether they are correct or not. This
might be helpful if you want students to write a function for a problem
using a specific implementation approach.

Example
^^^^^^^

Problem: Write a function ``sortList()`` that takes a list of numbers
and returns a list sorted in descending order without using the built-in
methods.

Test cases (but will still require instructors to check whether any
built-in method is used):

.. code:: python

    from nose.tools import assert_equal
    assert_equal(sortList([2, 3, 1]), [3, 2, 1])
    assert_equal(sortList([3, 2, 1]), [3, 2, 1])
    assert_equal(sortList([1, 2, 1, 2, 3, 1]), [3, 2, 2, 1, 1, 1])
    assert_equal(sortList([-1, 0, 1]), [1, 0, -1])


Checking whether a specific function has been used
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes, you may want to ensure that students are implementing their code in
the way they have been asked to. For example, if you have your students write
a function called ``mse``` (to compute mean-squared-error) in the first part of
the problem, and then want them to plot the MSE, you may ask them to be sure
that they use the ``mse`` function in their code. How can you test for this?

In Python, you can be a bit clever and test for this by removing the ``mse`` function from the global namespace, running their code, and checking whether their code throws the appropriate error. If it doesn't throw an error, that means they aren't calling the ``mse`` function.

A test case that does this might look something like this:

.. code:: python

    # save a reference to the original function, then delete it from the
    # global namespace
    old_mse = mse
    del mse

    # try running the students' code
    try:
        plot_mse()

    # if an NameError is thrown, that means their function calls mse
    except NameError:
        pass

    # if no error is thrown, that means their function does not call mse
    else:
        raise AssertionError("plot_mse does not call mse")

    # restore the original function
    finally:
        mse = old_mse
        del old_mse


Grading plots
~~~~~~~~~~~~~

Programmatically grading plots is a painful experience because there are many
ways that students can create the requested plot. In general, we recommend just
grading plots by hand. However, it is possible to programmatically grade some
simple types of plots (such as a scatter plot or bar plot). One such tool that
facilitates grading matplotlib plot specifically is `plotchecker <https://github.com/jhamrick/plotchecker>`_.


Gotchas
~~~~~~~

In many ways, writing autograder tests is similar to writing unit tests.
However, there are certain types of errors that students may make—especially if
they are new to programming—that are not things you would typically test for
when writing tests for your own code. Here are a list of some things we've come
across that are good to be aware of when writing your own autograder tests.

For loops
^^^^^^^^^

For loops in Python are sometimes confusing to students who are new to programming, especially if they are sometimes using them in the context of indexing into lists/arrays and sometimes not. For example, I have seen students sometimes write a for loop like this:

.. code:: python

    for i in x:
        y[i] = f(x[i])

rather than:

.. code:: python

    for i in range(len(x)):
        y[i] = f(x[i])

In particular, if ``x`` in the above example contains integers, the code may
not throw an error, and in certain cases, may even pass the tests if you are
not looking out for this type of mistake!

Global variables in the notebook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Although the Jupyter notebook is a really excellent format for assignments, it
does have some drawbacks. One drawback is the fact that variables defined
earlier in the document—for example, in a piece of sample code—can be accessed
later. This can pose problems if students accidentally use *those* variable
names rather than the variable names given in the function definition.

As a toy example, let's say that earlier in the notebook we have defined a
variable called ``arr``. Then, students are asked to write a function that
multiplies all the variables in the array by two. You give them a function
signature of ``f(x)``, and they write the following code:

.. code:: python

    def f(x):
        return arr * 2

Notice that their code uses ``arr`` rather than ``x``. This can be a problem
especially if you only test on one input—namely, ``arr``—because that test case
will pass! Thus, it is important to test students' code on a variety of inputs
in order to catch edge cases such as these, *and* that you use different
variable names:

.. code:: python

    # both of these tests will pass no because the student hardcoded the use
    # of the arr variable!
    arr = np.array([1, 2, 3])
    np.assert_array_equal(f(arr), np.array([2, 4, 6]))
    arr = np.array([5, 7])
    np.assert_array_equal(f(arr), np.array([10, 14]))

    # this test will fail because it uses a new input AND a new variable name
    arr2 = np.array([3, 2])
    np.assert_array_equal(f(arr2), np.array([6, 4]))

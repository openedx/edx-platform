##############################################################################
JS Input
##############################################################################
     
This document explains how to write a JSInput input type. JSInput is meant to
allow problem authors to easily turn working standalone HTML files into
problems that can be integrated into the edX platform. Since it's aim is
flexibility, it can be seen as the input and client-side equivalent of
CustomResponse.

A JSInput input creates an iframe into a static HTML page, and passes the
return value of author-specified functions to the enclosing response type
(generally CustomResponse). JSInput can also stored and retrieve state.

******************************************************************************
Format
******************************************************************************

A jsinput problem looks like this:

.. code-block:: xml

    <problem>
        <script type="loncapa/python">
 def all_true(exp, ans): return ans == "hi"
        </script>
        <customresponse cfn="all_true">
            <jsinput gradefn="gradefn" 
                height="500"
                get_statefn="getstate"
                set_statefn="setstate"
                html_file="/static/jsinput.html"/>
        </customresponse>
    </problem>

The accepted attributes are:

==============  ==============  ========= ==========
Attribute Name   Value Type     Required?  Default
==============  ==============  ========= ==========
html_file        Url string     Yes        None
gradefn          Function name  Yes        `gradefn`
set_statefn      Function name  No         None
get_statefn      Function name  No         None
height           Integer        No         `500`
width            Integer        No         `400`
==============  ==============  ========= ==========

******************************************************************************
Required Attributes
******************************************************************************

==============================================================================
html_file
==============================================================================

The `html_file` attribute specifies what html file the iframe will point to. This
should be located in the content directory.

The iframe is created using the sandbox attribute; while popups, scripts, and
pointer locks are allowed, the iframe cannot access its parent's attributes.

The html file should contain an accesible gradefn function. To check whether
the gradefn will be accessible to JSInput, check that, in the console,::
    "`gradefn"
Returns the right thing. When used by JSInput, `gradefn` is called with::
    `gradefn`.call(`obj`)
Where `obj` is the object-part of `gradefn`. For example, if `gradefn` is
`myprog.myfn`, JSInput will call `myprog.myfun.call(myprog)`. (This is to
ensure "`this`" continues to refer to what `gradefn` expects.)

Aside from that, more or less anything goes. Note that currently there is no
support for inheriting css or javascript from the parent (aside from the
Chrome-only `seamless` attribute, which is set to true by default).

==============================================================================
gradefn
==============================================================================

The `gradefn` attribute specifies the name of the function that will be called
when a user clicks on the "Check" button, and which should return the student's
answer. This answer will (unless both the get_statefn and set_statefn
attributes are also used) be passed as a string to the enclosing response type.
In the customresponse example above, this means cfn will be passed this answer
as `ans`.

If the `gradefn` function throws an exception when a student attempts to
submit a problem, the submission is aborted, and the student receives a generic
alert. The alert can be customised by making the exception name `Waitfor
Exception`; in that case, the alert message will be the exception message.

**IMPORTANT** : the `gradefn` function should not be at all asynchronous, since
this could result in the student's latest answer not being passed correctly.
Moreover, the function should also return promptly, since currently the student
has no indication that her answer is being calculated/produced.

******************************************************************************
Option Attributes
******************************************************************************

The `height` and `width` attributes are straightforward: they specify the
height and width of the iframe. Both are limited by the enclosing DOM elements,
so for instance there is an implicit max-width of around 900. 

In the future, JSInput may attempt to make these dimensions match the html
file's dimensions (up to the aforementioned limits), but currently it defaults
to `500` and `400` for `height` and `width`, respectively.

==============================================================================
set_statefn
==============================================================================

Sometimes a problem author will want information about a student's previous
answers ("state") to be saved and reloaded. If the attribute `set_statefn` is
used, the function given as its value will be passed the state as a string
argument whenever there is a state, and the student returns to a problem. It is
the responsibility of the function to then use this state approriately.

The state that is passed is:

1. The previous output of `gradefn` (i.e., the previous answer) if
   `get_statefn` is not defined.
2. The previous output of `get_statefn` (see below) otherwise.

It is the responsibility of the iframe to do proper verification of the
argument that it receives via `set_statefn`.

==============================================================================
get_statefn
==============================================================================

Sometimes the state and the answer are quite different. For instance, a problem
that involves using a javascript program that allows the student to alter a
molecule may grade based on the molecule's hidrophobicity, but from the
hidrophobicity it might be incapable of restoring the state. In that case, a
*separate* state may be stored and loaded by `set_statefn`. Note that if
`get_statefn` is defined, the answer (i.e., what is passed to the enclosing
response type) will be a json string with the following format::
    {
        answer: `[answer string]`
        state: `[state string]`
    }

It is the responsibility of the enclosing response type to then parse this as
json.

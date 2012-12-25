*********************************************
Xml format of graphical slider tool [xmodule]
*********************************************

.. module:: xml_format_gst

Format description
==================

Graphical slider tool (GST) main tag is::

    <graphical_slider_tool> BODY </graphical_slider_tool>

``graphical_slider_tool`` tag must have two children tags: ``render``
and ``configuration``.

Render tag
----------

Render tag can contain usual html tags mixed with some GST specific tags::

    <slider/> - represents jQuery slider
    <textbox/> - represents input
    <plot/> - represents Flot plot

Also GST will track all elements inside ``<render></render>`` where ``id``
attribute is set.

The contents of the <render> section will be shown to the user after
all occurrences of::

    <slider var="{parameter name}" [style="{CSS statements}"]/>
    <input var="parameter name" [style="{CSS statements}"] [readonly="true" | readonly="false"]/>
    <plot [style="{CSS statements}"]/>

have been converted to actual sliders, text inputs, and a plot graph.
Everything in square brackets is optional.

``{parameter name}`` specifies the parameter to which the slider or text
input will be attached to.

There is a one-to-one relationship between a slider and a parameter.
I.e. for one parameter you can put only one ``<slider ...<`` in the
``<render>`` section. However, you don't have to specify a slider - they
are optional.

There is a many-to-one relationship between text inputs and a
parameter. I.e. for one parameter you can put many '<input ...<' in
the ``<render>`` section. However, you don't have to specify a text
input - they are optional.

You can put only one ``<plot ...<`` in the ``<render>`` section. It is not
required.

NOTE: MathJax, independently of this module, will render all TeX code
within the ``<render>`` section into nice mathematical formulas. Just
remember to wrap it in one of::

    \(  and  \)  -  for inline formulas (formulas surrounded by
                  standard text)
    \[  and  \]  -  if you want the formula to be a separate line

Slider tag
..........

Slider tag must have ``var`` attribute and optional ``style`` attribute::

    <slider var='a' style="width:400px;float:left;"/>

After processing slider tags will be replaced by jQuery UI sliders with applied
``style`` attribute.


``Var`` attribute must correspond to parameter in one of ``function`` tags in
``functions`` tag. By moving slider, value of parameter ``a`` will change, and so
result of function, that depends on parameter ``a``, will change.


Textbox tag
...........


Texbox tag must have ``var`` attribute and optional ``style`` and ``readonly``
attributes::

    <textbox var="b" readonly="true" style="width:50px; float:left; margin-left:10px;"/>

After processing tetbox tags will be replaced by html inputs with applied
``style`` attribute. If ``readonly`` is set to ``true`` input will be
not-editable, default is ``false``.

``Var`` attribute must correspond to parameter in one of ``function`` tags in
``functions`` tag. By entering value in input, value of parameter ``b`` will change, and so
result of function, that depends on parameter ``b``, will change.

Plot tag
........

Plot tag may have optional ``style`` attribute::

    <plot style="width:50px; float:left; margin-left:10px;"/>

After processing plot tags will be replaced by Flot plot with applied
``style`` attribute.

HTML tags with id
.................

Any html tag with id, i.e. ``<span id="answer_span_1">`` will be counted as
place where result of function can be rendered. To render function result to
element, element id must be included in ``function`` tag as ``el_id`` attribute
and ``output`` value must be ``"element"``::

    <function output="element" el_id="answer_span_1">
                    function add(a, b, precision) {
                        var x = Math.pow(10, precision || 2);
                        return (Math.round(a * x) + Math.round(b * x)) / x;
                    }

                    return add(a, b, 5);
    </function>



Configuration tag
-----------------

The configuration tag contain sparameter settings, graph
settings, and function definitions which are to be plotted on the
graph and that use specified parameters.

Configuration tag contains two mandatory tag ``functions`` and ``parameters`` and
may contain another ``plot`` tag.

Parameters tag
..............

``Parameters`` tag contains ``parameter`` tags. Each ``parameter`` tag must have
``var``, ``max``, ``min``, ``step`` and ``initial`` attributes::

        <parameters>
                <param var="a" min="-10.0" max="10.0" step="0.1" initial="0" />
                <param var="b" min="-10.0" max="10.0" step="0.1" initial="0" />
        </parameters>

``Var`` attribute links min, max, step and initial values to parameter name.
``Min`` attribute is minimal value that parameter can take. Slider and input
values can not go below it.

``Max`` attribute is maximal value that parameter can take. Slider and input
values can not go over it.

``Step`` attribute is value of slider step. When a slider increase or decreases
the specified parameter, it will do so by the amount specified with 'step'

``Initial`` attribute is the initial value that the specified parameter should be
set to.

The parameter's name is specified by the 'var' property. All occurrences
of sliders and/or text inputs that specify a 'var' property, will be
connected to this parameter - i.e. they will reflect the current
value of the parameter and will be updated when the parameter
changes.


If at lest one of these attributes is not set, then the parameter
will not be used, slider's and/or text input elements that specify
this parameter will not be activated, and the specified functions
which use this parameter will return a non valid value. This means
that neglecting to specify at least one of the attributes for some
parameter will have the result of the whole GST instance not working
properly.


Functions tag
.............


For the GST to do something, you must defined at least one
function, which can use any of the specified parameter values. The
function expects to take the ``x`` value, do some calculations, and
return the ``y`` value. I.e. this is a 2D plot in Cartesian
coordinates.

Each function must be defined inside ``function`` tag in  ``functions`` tag::

    <functions>
        <function output="element" el_id="answer_span_1">
            function add(a, b, precision) {
                var x = Math.pow(10, precision || 2);
                return (Math.round(a * x) + Math.round(b * x)) / x;
            }

            return add(a, b, 5);
        </function>
    </functions>

The parameter names (along with their values, as provided from text
inputs and/or sliders), will be available inside all defined
functions. A defined function body string will be parsed internally
by the browser's JavaScript engine and converted to a true JS
function.

The function's parameter list will automatically be created and
populated, and will include the ``x``, and all of the specified
parameter values (from sliders and text inputs). This means that
each of the defined functions will have access to all of the
parameter values. You don't have to use them, but they will be
there.

Examples::

    <function>
        return x;
    </function>

    <function dot="true" label="\(y_2\)">
        return (x + a) * Math.sin(x * b);
    </function>

    <function color="green">
        function helperFunc(c1) {
            return c1 * c1 - a;
        }
        return helperFunc(x + 10 * a * b) + Math.sin(a - x);
    </function>

Required parameters::

    function body:

    A string composing a normal JavaScript function
    except that there is no function declaration
    (along with parameters), and no closing bracket.

    So if you normally would have written your
    JavaScript function like this:

        function myFunc(x, a, b) {
            return x * a + b;
        }

    here you must specify just the function body
    (everything that goes between '{' and '}'). So,
    you would specify the above function like so (the
    bare-bone minimum):

        <function>
            return x * a + b;
        </function>

Optional parameters::


    color:  Color name (red, green, etc.) or in the form of
            '#FFFF00'. If not specified, a default color (different
            one for each function) will be given by Flot;
    line:   A string - 'true' or 'false'. Should the data points be
            connected by a line on the graph? Default is 'true'.
    dot:    A string - 'true' or 'false'. Should points be shown for
            each data point on the graph? Default is 'false'.
    label:  A string. If provided, will be shown in the legend, along
            with the color that was used to plot the function.
    output: "element" or "plot". If not defined, function will be plotted.
            If defined, function will not be plotted, but rendered to element
            with id set in 'el_id' attribute.
    el_id:  Id of html element, defined in 'render' section. Value of
            function will be rendered to content of this element.

With ``output`` and ``el_id`` set together you can update html elements with
function value, also function will not be plotted.

[note on MathJax and labels]:

It is possible to define a label in standard TeX notation. The JS
library MathJax will work on these labels also because they are
inserted on top of the plot as standard HTML (text within a DIV).

Plot tag
........

``Plot`` tag inside ``configuration`` tag defines settings for plot output.

Required parameters::

    xrange: 2 functions that must return value. Value is constant (3.1415)
            or depend on parameter from parameters section:
                <xrange>
                    <min>return 0;</min>
                    <max>return 30;</max>
                </xrange>
                                        or
                <xrange>
                    <min>return -a;</min>
                    <max>return a;</max>
                </xrange>

            All functions will be calculated over domain between xrange:min
            and xrange:max. Xrange depending on parameter is extremely
            useful when domain(s) of your function(s) depends on parameter
            (like circle, when parameter is radius and you want to allow
            to change it).

Optional parameters::

    num_points: Number of data points to generated for the plot. If
                this is not set, the number of points will be
                calculated as width / 5.
    xticks,
    yticks:    3 floating point numbers separated by commas. This
               specifies how many ticks are created, what number they
               start at, and what number they end at. This is different
               from the 'xrange' setting in that it has nothing to do
               with the data points - it control what area of the
               Cartesian space you will see. The first number is the
               first tick's value, the second number is the step
               between each tick, the third number is the value of the
               last tick. If these configurations are not specified,
               Flot will chose them for you based on the data points
               set that he is currently plotting. Usually, this results
               in a nice graph, however, sometimes you need to fine
               grain the controls. For example, when you want to show
               a fixed area of the Cartesian space, even when the data
               set changes. On it's own, Flot will recalculate the
               ticks, which will result in a different graph each time.
               By specifying the xticks, yticks configurations, only
               the plotted data will change - the axes (ticks) will
               remain as you have defined them.

    xunits,
    yunits:   Units values to be set on axes. Use MathJax. Example:
                <xunits>\(cm\)</xunits>
                <yunits>\(m\)</yunits>

Example
=======

Plotting, sliders and inputs
----------------------------

.. literalinclude:: gst_example_with_documentation.xml

Update of html elements, no plotting
------------------------------------

.. literalinclude:: gst_example_html_element_output.xml


Circle with dynamic radius
--------------------------

.. literalinclude:: gst_example_dynamic_range.xml

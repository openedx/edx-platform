.. _Graphical Slider Tool:

*********************************************
Graphical Slider Tool
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

    <slider/> - represents jQuery slider for changing a parameter's value
    <textbox/> - represents a text input field for changing a parameter's value
    <plot/> - represents Flot JS plot element

Also GST will track all elements inside ``<render></render>`` where ``id``
attribute is set, and a corresponding parameter referencing that ``id`` is present
in the configuration section below. These will be referred to as dynamic elements.

The contents of the <render> section will be shown to the user after
all occurrences of::

    <slider var="{parameter name}" [style="{CSS statements}"] />
    <textbox var="{parameter name}" [style="{CSS statements}"] />
    <plot [style="{CSS statements}"] />

have been converted to actual sliders, text inputs, and a plot graph.
Everything in square brackets is optional. After initialization, all
text input fields, sliders, and dynamic elements will be set to the initial
values of the parameters that they are assigned to.

``{parameter name}`` specifies the parameter to which the slider or text
input will be attached to.

[style="{CSS statements}"] specifies valid CSS styling. It will be passed
directly to the browser without any parsing.

There is a one-to-one relationship between a slider and a parameter.
I.e. for one parameter you can put only one ``<slider>`` in the
``<render>`` section. However, you don't have to specify a slider - they
are optional.

There is a many-to-one relationship between text inputs and a
parameter. I.e. for one parameter you can put many '<textbox>' elements in
the ``<render>`` section. However, you don't have to specify a text
input - they are optional.

You can put only one ``<plot>`` in the ``<render>`` section. It is not
required.


Slider tag
..........

Slider tag must have ``var`` attribute and optional ``style`` attribute::

    <slider var='a' style="width:400px;float:left;" />

After processing, slider tags will be replaced by jQuery UI sliders with applied
``style`` attribute.

``var`` attribute must correspond to a parameter. Parameters can be used in any
of the ``function`` tags in ``functions`` tag. By moving slider, value of
parameter ``a`` will change, and so result of function, that depends on parameter
``a``, will also change.


Textbox tag
...........

Texbox tag must have ``var`` attribute and optional ``style`` attribute::

    <textbox var="b" style="width:50px; float:left; margin-left:10px;" />

After processing, textbox tags will be replaced by html text inputs with applied
``style`` attribute. If you want a readonly text input, then you should use a
dynamic element instead (see section below "HTML tagsd with ID").

``var`` attribute must correspond to a parameter. Parameters can be used in any
of the ``function`` tags in ``functions`` tag. By changing the value on the text input,
value of parameter ``a`` will change, and so result of function, that depends on
parameter ``a``, will also change.


Plot tag
........

Plot tag may have optional ``style`` attribute::

    <plot style="width:50px; float:left; margin-left:10px;" />

After processing plot tags will be replaced by Flot JS plot with applied
``style`` attribute.


HTML tags with ID (dynamic elements)
....................................

Any HTML tag with ID, e.g. ``<span id="answer_span_1">`` can be used as a
place where result of function can be inserted. To insert function result to
an element, element ID must be included in ``function`` tag as ``el_id`` attribute
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

The configuration tag contains parameter settings, graph
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

``var`` attribute links min, max, step and initial values to parameter name.

``min`` attribute is the minimal value that a parameter can take. Slider and input
values can not go below it.

``max`` attribute is the maximal value that a parameter can take. Slider and input
values can not go over it.

``step`` attribute is value of slider step. When a slider increase or decreases
the specified parameter, it will do so by the amount specified with 'step'

``initial`` attribute is the initial value that the specified parameter should be
set to. Sliders and inputs will initially show this value.

The parameter's name is specified by the ``var`` property. All occurrences
of sliders and/or text inputs that specify a ``var`` property, will be
connected to this parameter - i.e. they will reflect the current
value of the parameter, and will be updated when the parameter
changes.

If at lest one of these attributes is not set, then the parameter
will not be used, slider's and/or text input elements that specify
this parameter will not be activated, and the specified functions
which use this parameter will not return a numeric value. This means
that neglecting to specify at least one of the attributes for some
parameter will have the result of the whole GST instance not working
properly.


Functions tag
.............

For the GST to do something, you must defined at least one
function, which can use any of the specified parameter values. The
function expects to take the ``x`` value, do some calculations, and
return the ``y`` value. I.e. this is a 2D plot in Cartesian
coordinates. This is how the default function is meant to be used for
the graph.

There are other special cases of functions. They are used mainly for
outputting to elements, plot labels, or for custom output. Because
the return a single value, and that value is meant for a single element,
these function are invoked only with the set of all of the parameters.
I.e. no ``x`` value is available inside them. They are useful for
showing the current value of a parameter, showing complex static
formulas where some parameter's value must change, and other useful
things.

The different style of function is specified by the ``output`` attribute.

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
populated, and will include the ``x`` (when ``output`` is not specified or
is set to ``"graph"``), and all of the specified parameter values (from sliders
and text inputs). This means that each of the defined functions will have
access to all of the parameter values. You don't have to use them, but
they will be there.

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

        <function>return x * a + b;</function>

    VERY IMPORTANT: Because the function will be passed
    to the browser as a single string, depending on implementation
    specifics, the end-of-line characters can be stripped. This
    means that single line JavaScript comments (starting with "//")
    can lead to the effect that everything after the first such comment
    will be treated as a comment. Therefore, it is absolutely
    necessary that such single line comments are not used when
    defining functions for GST. You can safely use the alternative
    multiple line JavaScript comments (such comments start with "/*"
    and end with "*/).

    VERY IMPORTANT: If you have a large function body, and decide to
    split it into several lines, than you must wrap it in "CDATA" like
    so:

        <function>
        <![CDATA[
            var dNew;

            dNew = 0.3;

            return x * a + b - dNew;
        ]]>
        </function>

Optional parameters::


    color:  Color name ('red', 'green', etc.) or in the form of
            '#FFFF00'. If not specified, a default color (different
            one for each graphed function) will be given by Flot JS.
    line:   A string - 'true' or 'false'. Should the data points be
            connected by a line on the graph? Default is 'true'.
    dot:    A string - 'true' or 'false'. Should points be shown for
            each data point on the graph? Default is 'false'.
    bar:    A string - 'true' or 'false'. When set to 'true', points
            will be plotted as bars.
    label:  A string. If provided, will be shown in the legend, along
            with the color that was used to plot the function.
    output: 'element', 'none', 'plot_label', or 'graph'. If not defined,
            function will be plotted (same as setting 'output' to 'graph').
            If defined, and other than 'graph', function will not be
            plotted, but it's output will be inserted into the element
            with ID specified by 'el_id' attribute.
    el_id:  Id of HTML element, defined in '<render>' section. Value of
            function will be inserted as content of this element.
    disable_auto_return: By default, if JavaScript function string is written
                         without a "return" statement, the "return" will be
                         prepended to it. Set to "true" to disable this
                         functionality. This is done so that simple functions
                         can be defined in an easy fashion (for example, "a",
                         which will be translated into "return a").
    update_on: A string - 'change', or 'slide'. Default (if not set) is
               'slide'. This defines the event on which a given function is
               called, and its result is inserted into an element. This
               setting is relevant only when "output" is other than "graph".

When specifying ``el_id``, it is essential to set "output" to one of
    element - GST will invoke the function, and the return of it will be
              inserted into a HTML element with id specified by ``el_id``.
    none    - GST will simply inoke the function. It is left to the instructor
              who writes the JavaScript function body to update all necesary
              HTML elements inside the function, before it exits. This is done
              so that extra steps can be preformed after an HTML element has
              been updated with a value. Note, that because the return value
              from this function is not actually used, it will be tempting to
              omit the "return" statement. However, in this case, the attribute
              "disable_auto_return" must be set to "true" in order to prevent
              GST from inserting a "return" statement automatically.
    plot_label - GST will process all plot labels (which are strings), and
                 will replace the all instances of substrings specified by
                 ``el_id`` with the returned value of the function. This is
                 necessary if you want a label in the graph to have some changing
                 number. Because of the nature of Flot JS, it is impossible to
                 achieve the same effect by setting the "output" attribute
                 to "element", and including a HTML element in the label.

The above values for "output" will tell GST that the function is meant for an
HTML element (not for graph), and that it should not get an 'x' parameter (along
with some value).


[Note on MathJax and labels]
............................

Independently of this module, will render all TeX code
within the ``<render>`` section into nice mathematical formulas. Just
remember to wrap it in one of::

    \(  and  \)  -  for inline formulas (formulas surrounded by
                  standard text)
    \[  and  \]  -  if you want the formula to be a separate line

It is possible to define a label in standard TeX notation. The JS
library MathJax will work on these labels also because they are
inserted on top of the plot as standard HTML (text within a DIV).

If the label is dynamic, i.e. it will contain some text (numeric, or other)
that has to be updated on a parameter's change, then one can define
a special function to handle this. The "output" of such a function must be
set to "none", and the JavaScript code inside this function must update the
MathJax element by itself. Before exiting, MathJax typeset function should
be called so that the new text will be re-rendered by MathJax. For example::

    <render>
        ...
        <span id="dynamic_mathjax"></span>
    </render>
    ...
    <function output="none" el_id="dynamic_mathjax">
    <![CDATA[
        var out_text;

        out_text = "\\[\\mathrm{Percent \\space of \\space treated \\space with \\space YSS=\\frac{"
          +(treated_men*10)+"\\space men *"
          +(your_m_tx_yss/100)+"\\space prev. +\\space "
          +((100-treated_men)*10)+"\\space women *"
          +(your_f_tx_yss/100)+"\\space prev.}"
          +"{1000\\space total\\space treated\\space patients}"
          +"="+drummond_combined[0][1]+"\\%}\\]";
          mathjax_for_prevalence_calcs+="\\[\\mathrm{Percent \\space of \\space untreated \\space with \\space YSS=\\frac{"
          +(untreated_men*10)+"\\space men *"
          +(your_m_utx_yss/100)+"\\space prev. +\\space "
          +((100-untreated_men)*10)+"\\space women *"
          +(your_f_utx_yss/100)+"\\space prev.}"
          +"{1000\\space total\\space untreated\\space patients}"
          +"="+drummond_combined[1][1]+"\\%}\\]";

        $("#dynamic_mathjax").html(out_text);

        MathJax.Hub.Queue(["Typeset",MathJax.Hub,"dynamic_mathjax"]);
    ]]>
    </function>
    ...


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

    bar_width: If functions are present which are to be plotted as bars,
               then this parameter specifies the width of the bars. A
               numeric value for this parameter is expected.

    bar_align: If functions are present which are to be plotted as bars,
               then this parameter specifies how to align the bars relative
               to the tick. Available values are "left" and "center".

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

    xticks_names, yticks_names:
              A JSON string which represents a mapping of xticks, yticks
              values to some defined strings. If specified, the graph will
              not have any xticks, yticks except those for which a string
              value has been defined in the JSON string. Note that the
              matching will be string-based and not numeric. I.e. if a tick
              value was "3.70" before, then inside the JSON there should be
              a mapping like {..., "3.70": "Some string", ...}. Example:

                  <xticks_names>
                  <![CDATA[
                  {
                      "1": "Treated", "2": "Not Treated",
                      "4": "Treated", "5": "Not Treated",
                      "7": "Treated", "8": "Not Treated"
                  }
                  ]]>
                  </xticks_names>

                  <yticks_names>
                  <![CDATA[
                      {"0": "0%", "10": "10%", "20": "20%", "30": "30%", "40": "40%", "50": "50%"}
                  ]]>
                  </yticks_names>

    xunits,
    yunits:   Units values to be set on axes. Use MathJax. Example:
                <xunits>\(cm\)</xunits>
                <yunits>\(m\)</yunits>

    moving_label:
              A way to specify a label that should be positioned dynamically,
              based on the values of some parameters, or some other factors.
              It is similar to a <function>, but it is only valid for a plot
              because it is drawn relative to the plot coordinate system.

              Multiple "moving_label" configurations can be provided, each one
              with a unique text and a unique set of functions that determine
              it's dynamic positioning.

              Each "moving_label" can have a "color" attribute (CSS color notation),
              and a "weight" attribute. "weight" can be one of "normal" or "bold",
              and determines the styling of moving label's text.

              Each "moving_label" function should return an object with a 'x'
              and 'y properties. Within those functions, all of the parameter
              names along with their value are available.

              Example (note that "return" statement is missing; it will be automatically
              inserted by GST):

                  <moving_label text="Co" weight="bold" color="red>
                  <![CDATA[  {'x': -50, 'y': c0};]]>
                  </moving_label>

    asymptote:
              Add a vertical or horizontal asymptote to the graph which will
              be dynamically repositioned based on the specified function.

              It is similar to the function in that it provides a JavaScript body function
              string. This function will be used to calculate the position of the asymptote
              relative to the axis specified by the "type" parameter.

              Required parameters:
                  type:
                        Which axis should the asymptote be plotted against. Available values
                        are "x" and "y".

              Optional parameters:
                  color:
                        The color of the line. A valid CSS color string is expected.


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


Example of a bar graph
----------------------

.. literalinclude:: gst_example_bars.xml


Example of moving labels of graph
---------------------------------

.. literalinclude:: gst_example_dynamic_labels.xml

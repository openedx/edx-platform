**********************************************
Xml format of drag and drop input [inputtypes]
**********************************************

.. module:: drag_and_drop_input

Format description
==================

The main tag of Drag and Drop (DnD) input is::

    <drag_and_drop_input> ... </drag_and_drop_input>

``drag_and_drop_input`` can include any number of the following 2 tags:
``draggable`` and ``target``.

drag_and_drop_input tag
-----------------------

The main container for a single instance of DnD. The following attributes can
be specified for this tag::

    img - Relative path to an image that will be the base image. All draggables
          can be dragged onto it.
    target_outline - Specify whether an outline (gray dashed line) should be
          drawn around targets (if they are specified). It can be either
          'true' or 'false'. If not specified, the default value is
          'false'.
    one_per_target - Specify whether to allow more than one draggable to be
          placed onto a single target. It can be either 'true' or 'false'. If
          not specified, the default value is 'true'.
    no_labels - default is false, in default behaviour if label is not set, label
          is obtained from id. If no_labels is true, labels are not automatically
          populated from id, and one can not set labels and obtain only icons.

draggable tag
-------------

Draggable tag specifies a single draggable object which has the following
attributes::

    id - Unique identifier of the draggable object.
    label - Human readable label that will be shown to the user.
    icon - Relative path to an image that will be shown to the user.

A draggable is what the user must drag out of the slider and place onto the
base image. After a drag operation, if the center of the draggable ends up
outside the rectangular dimensions of the image, it will be returned back
to the slider.

In order for the grader to work, it is essential that a unique ID
is provided. Otherwise, there will be no way to tell which draggable is at what
coordinate, or over what target. Label and icon attributes are optional. If
they are provided they will be used, otherwise, you can have an empty
draggable. The path is relative to 'course_folder' folder, for example,
/static/images/img1.png.

target tag
----------

Target tag specifies a single target object which has the following required
attributes::

    id - Unique identifier of the target object.
    x - X-coordinate on the base image where the top left corner of the target
        will be positioned.
    y - Y-coordinate on the base image where the top left corner of the target
        will be positioned.
    w - Width of the target.
    h - Height of the target.

A target specifies a place on the base image where a draggable can be
positioned. By design, if the center of a draggable lies within the target
(i.e. in the rectangle defined by [[x, y], [x + w, y + h]], then it is within
the target. Otherwise, it is outside.

If at lest one target is provided, the behavior of the client side logic
changes. If a draggable is not dragged on to a target, it is returned back to
the slider.

If no targets are provided, then a draggable can be dragged and placed anywhere
on the base image.


Example
=======

Various configuration of DnD on one page
----------------------------------------

.. literalinclude:: drag-n-drop-demo.xml

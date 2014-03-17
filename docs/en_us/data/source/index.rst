..
    Public facing docs for non-developers go here. Please do not add any Python
    dependencies for code introspection here (we may temporarily host it some
    place where those dependencies are cumbersome to build).

edX Data Documentation
======================
The following documents are targeted at those who are working with various data formats consumed and produced by the edX platform -- primarily course authors and those who are conducting research on data in our system. 

* If you are a course author working with course XML, see :ref:`Course Data Formats`.

* If you are a researcher working with data, see :ref:`Internal Data Formats`.

Developer-oriented discussion of architecture and strictly internal APIs will be documented elsewhere.

.. _Course Data Formats:

Course Data Formats
-------------------
These are data formats written by people to specify course structure and content. Some of this is abstracted away if you are using the Studio authoring user interface.

.. toctree::
   :maxdepth: 2

   course_data_formats/course_xml.rst
   course_data_formats/grading.rst

Specific Problem Types
^^^^^^^^^^^^^^^^^^^^^^
.. toctree::
   :maxdepth: 1

   course_data_formats/drag_and_drop/drag_and_drop_input.rst
   course_data_formats/graphical_slider_tool/graphical_slider_tool.rst
   course_data_formats/poll_module/poll_module.rst
   course_data_formats/lti_module/lti.rst
   course_data_formats/conditional_module/conditional_module.rst
   course_data_formats/word_cloud/word_cloud.rst
   course_data_formats/custom_response.rst
   course_data_formats/symbolic_response.rst
   course_data_formats/jsinput.rst
   course_data_formats/formula_equation_input.rst

.. _Internal Data Formats:

Internal Data Formats
---------------------
These documents describe how we store course structure, student state/progress, and events internally. Useful for developers or researchers who interact with our raw data exports.

.. toctree::
   :maxdepth: 2

   internal_data_formats/change_log.rst
   internal_data_formats/sql_schema.rst
   internal_data_formats/discussion_data.rst
   internal_data_formats/wiki_data.rst
   internal_data_formats/tracking_logs.rst

Indices and tables
==================

* :ref:`search`


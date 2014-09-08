.. _Grading Policy:

#################################
Grading Policy
#################################

You create a grading policy file to specify how problems are graded in your
course.

*******************************
Create the Grading Policy File
*******************************

You define policies for your course in the ``grading_policy.json`` file. 

Save the ``grading_policy.json`` file in the ``policy/<course-name>``
directory.

The ``<course-name>`` directory  must match the value of the ``url_name``
attribute in the ``course.xml`` file.

************************************
Course Policy JSON Objects
************************************

  .. list-table::
     :widths: 10 80
     :header-rows: 0

     * - ``GRADE_CUTOFFS``
       - The minimal grade for passing the course, and receiving a certificate
         if offered.
     * - ``GRADER``
       - For each assignment type:

         * ``min_count``:???
         * ``weight``: The percentage of the total grade determined by
            assignments of this type. The total value for all assignment types
            must equal 1.0.
         * ``type``: The name of the assignment type.
         * ``short_label``: The label for the assignment type shown on the
           student's Progress page.
         * ``drop_count``: The number of assignments of this type that can be
           dropped when calculating the final grade.

*******************************
Example Grading Policy File
*******************************

.. code-block:: json

    {
        "GRADE_CUTOFFS": {"Pass": 0.6}, 
        "GRADER": [
                    {
                        "min_count": 3, 
                        "weight": 0.75, 
                        "type": "Homework", 
                        "drop_count": 1, 
                        "short_label": "Ex"
                    }, 
                    {
                        "short_label": "", 
                        "min_count": 1, 
                        "type": "Exam", 
                        "drop_count": 0, 
                        "weight": 0.25
                    }
                  ]
    }
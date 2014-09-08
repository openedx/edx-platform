.. _Course Asset Policy:

#################################
Course Asset Policy
#################################

You create an asset policy file to provide details of the assets used in your
course. Assets can include image files, textbooks, handouts, and supporting
JavaScript files.

You must enter policy details for each asset you add the the ``static``
directory. See :ref:`Course Assets` for more information.


*******************************
Create the Asset Policy File
*******************************

You define policies for your assets in the ``assets.json`` file. 

Save the ``assets.json`` file in the ``policy`` directory. You use one
``assets.json`` file for all of the courses you may have in your directory
structure.


************************************
Asset Policy JSON Objects
************************************

  .. list-table::
     :widths: 10 80
     :header-rows: 0

     * - ``contentType``
       - The MIME type of the file.
     * - ``displayname``
       - The file name.
     * - ``locked``
       - ``true`` if users can only access the file from within your course.
         ``false`` if users can access the file from outside of your course.
     * - ``content_son``
       - A collection that contains:
         * ``category``:  Equal to ``asset``
         * ``name``: The file name
         * ``course``: The course number
         * ``tag``: 
         * ``org``: The organization that created the course
         * ``revision``
     * - ``filename``
       - The full path and name of the file in the edX Platform.
     * - ``import_path``
       -
     * - ``thumbnail_location``
       - An array containing:
         * ``c4x``
         * The organization
         * The course number
         * ``thumbnail``
         * The filename for the thumbnail

        

*******************************
Example Asset Policy File
*******************************

The following example shows the JSON policy for one image file.

.. code-block:: json

    {
        "dashboard.png": 
            {
                "contentType": "image/png", 
                "displayname": "dashboard.png", 
                "locked": false, 
                "content_son": 
                    {
                        "category": "asset", 
                        "name": "dashboard.png", 
                        "course": "Course number", 
                        "tag": "c4x", 
                        "org": "Organization", 
                        "revision": null
                    }, 
                    "filename": "/c4x/Organization/Course-number/asset/dashboard.png", 
                    "import_path": null, 
                    "thumbnail_location": 
                        [
                            "c4x", 
                            "Organization", 
                            "Course number", 
                            "thumbnail", 
                            "dashboard.jpg", 
                            null
                        ]
            }
    }
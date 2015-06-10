##################################################
Bookmarks API
##################################################
 
 
This page contains information about using the Bookmarks API to complete
the following actions.
 
* :ref:`Get a List of Bookmarks`
* :ref:`Create a New Bookmark`
* :ref:`Retrieve a Bookmark`
* :ref:`Delete a Bookmark`

   
.. _Get a List of Bookmarks:
 
***********************
Get a List of Bookmarks
***********************
 
.. autoclass:: folder_name.file_name.class_name
 
**Example response**
 
.. code-block:: json
 
	200 OK
	{
	    "count": 18,
	    "next": "/api/bookmarks/v0/bookmarks/?course_id=course-v1:TestX+TestCourse+TestRun?page=2&page_size=10",
	    "previous": null,
	    "num_pages": 2,
	    "results": [
	        {
	            "id": "alikhan,i4x%3A//RiceX/BIOC300.1x/openassessment/cf4c1de230af407fa214905b90aace57",
	            "course_id": "RiceX/BIOC300.1x/3T2014",
	            "usage_id": "i4x://RiceX/BIOC300.1x/openassessment/cf4c1de230af407fa214905b90aace57",
	            "display_name": "A Global History of Architecture: Part 1",
	            "path": [
	                {
	                    usage_id: "i4x://RiceX/BIOC300.1x/chapter/cf4c1de2efmveoirm1490e57",
	                    display_name: "Week 1"
	                },
	                {
	                    usage_id: "i4x://RiceX/BIOC300.1x/sequential/foivmeiormoeriv4905b90aace57",
	                    display_name: "Reflection"
	                }
	            ],
	            "created": "2014-09-23T14:00:00Z"
	        }
	    ]
	} 
 
.. _Create a New Bookmark:
 
**********************
Create a New Bookmark
**********************
 
.. autoclass:: folder_name.file_name.class_name
 
**Example response**
 
.. code-block:: json
 
	// Request
	{
	    "usage_id": "i4x://RiceX/BIOC300.1x/openassessment/cf4c1de230af407fa214905b90aace57",
	}
	 
	// Response
	201 Created
	{  
	    "id": "alikhan,i4x%3A//RiceX/BIOC300.1x/openassessment/cf4c1de230af407fa214905b90aace57",
	    "course_id": "RiceX/BIOC300.1x/3T2014",
	    "usage_id": "i4x://RiceX/BIOC300.1x/openassessment/cf4c1de230af407fa214905b90aace57",
	    "display_name": "A Global History of Architecture: Part 1",
	    "path": [
	        {
	            usage_id: "i4x://RiceX/BIOC300.1x/chapter/cf4c1de2efmveoirm1490e57",
	            display_name: "Week 1"
	        },
	        {
	            usage_id: "i4x://RiceX/BIOC300.1x/sequential/foivmeiormoeriv4905b90aace57",
	            display_name: "Reflection"
	        }
	    ],
	    "created": "2014-09-23T14:00:00Z"
	}


.. _Retrieve a Bookmark:
 
***********************
Retrieve a Bookmark
***********************
 
.. autoclass:: folder_name.file_name.class_name
 
**Example response**
 
.. code-block:: json

	200 OK
	{
	    "id": "alikhan,i4x%3A//RiceX/BIOC300.1x/openassessment/cf4c1de230af407fa214905b90aace57",
	    "course_id": "RiceX/BIOC300.1x/3T2014",
	    "usage_id": "i4x://RiceX/BIOC300.1x/openassessment/cf4c1de230af407fa214905b90aace57",
	    "display_name": "A Global History of Architecture: Part 1",
	    "path": [
	        { 
	            usage_id: "i4x://RiceX/BIOC300.1x/chapter/cf4c1de2efmveoirm1490e57",
	            display_name: "Week 1"
	        },
	        { 
	            usage_id: "i4x://RiceX/BIOC300.1x/sequential/foivmeiormoeriv4905b90aace57",
	            display_name: "Reflection"
	        }
	    ],
	    "created": "2014-09-23T14:00:00Z"
	}



.. _Delete a Bookmark:
 
***********************
Delete a Bookmark
***********************
 
.. autoclass:: folder_name.file_name.class_name
 
**Example response**
 
.. code-block:: json

	204 No Content







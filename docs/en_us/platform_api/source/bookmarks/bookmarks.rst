##################################################
Bookmarks API
##################################################
 
 
This page contains information about using the Bookmarks API to complete
the following actions.
 
* :ref:`Get List or Create Bookmarks`
* :ref:`Retrieve or Delete a Bookmark`

   
.. _Get List or Create Bookmarks:
 
***************************************************
Get a List of Bookmarks or Create a New Bookmark
***************************************************
 
.. autoclass:: bookmarks.views.BookmarksListView

**Example response showing creation of a bookmark**
  
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


.. _Retrieve or Delete a Bookmark:
 
********************************
Retrieve or Delete a Bookmark
********************************
 
.. autoclass:: bookmarks.views.BookmarksDetailView

**Example response showing a user's bookmark**
 
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

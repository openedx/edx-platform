.. _Video Components:

#################################
Video Components
#################################

You can add video components to a vertical, or unit, in your course.

See:

* `Create the XML File for a Video Component`_
* `Video Component XML File Elements`_
* `video Element Attributes`_
* `Example Video Component XML File`_

**********************************************
Create the XML File for a Video Component
**********************************************

You create an XML file in the ``video`` directory for each video component in
your course.

The name of the XML file must match the value of the @url_name attribute of the
``video`` element in the vertical XML file.

For example, if the vertical XML file contains:

.. code-block:: xml
  
   <vertical display_name="Lesson_1_Unit_1">
      <video url_name="Introduction_Lecture"/>
      . . .
  </vertical>

You create the file ``video/Introduction_Lecture.xml`` to define the video
component.

*************************************
Video Component XML File Elements
************************************* 

The root element of the XML file for the HTML component is file is ``video``. 

The ``video`` element contains a single ``source`` element.

==============================
``source`` Element
==============================

The ``source`` element contains one attribute:

.. list-table::
   :widths: 10 70
   :header-rows: 1

   * - Attribute
     - Meaning
   * - ``src``
     - The file path for the video file.


*************************************
``video`` Element Attributes
*************************************

.. list-table::
   :widths: 10 70
   :header-rows: 1

   * - Attribute
     - Meaning
   * - ``display_name``
     - The value that is displayed to students as the name of the video
       component.
   * - ``youtube``
     - The speed and ID pairings for the YouTube video source. The value can
       contain multiple speed:ID pairs, separated by commas.
   * - ``download_track``
     - Whether students can download the video track. ``true`` or ``false``.
   * - ``download_video``
     - Whether students can download the video. ``true`` or ``false``.
   * - ``html5_sources``
     - The file path for the HTML5 version of the video.
   * - ``show_captions``
     - Whether students can view the video captions. ``true`` or ``false``.
   * - ``source``
     - ???
   * - ``sub``
     - ???
   * - ``youtube_id_0_75``
     - The YouTube ID for the video that plays at 75% normal speed.
   * - ``youtube_id_1_0``
     - The YouTube ID for the video that plays at 100% normal speed.
   * - ``youtube_id_1_25``
     - The YouTube ID for the video that plays at 125% normal speed.
   * - ``youtube_id_1_5``
     - The YouTube ID for the video that plays at 150% normal speed.
       

*************************************
Example Video Component XML File
*************************************

The following example shows an XML file for a discussion component:

.. code-block:: xml
  
  <video 
    youtube="0.75:xGKlr7nT_Zw,1.00:o2pLltkrhGM,1.25:XGsB9bA6rGU,1.50:_HuIF16HdTA" 
    url_name="Introduction_Lecture" 
    display_name="Introduction Lecture" 
    download_video="true" 
    html5_sources="[&quot;https://s3.amazonaws.com/edx-course-videos/school/DemoCourseIntroductionVideo.mov&quot;]" 
    source="" 
    youtube_id_0_75="xGKlr7nT_Zw" 
    youtube_id_1_0="o2pLltkrhGM" 
    youtube_id_1_25="XGsB9bA6rGU" 
    youtube_id_1_5="_HuIF16HdTA">
  
    <source src="https://s3.amazonaws.com/edx-course-videos/mit-6002x/6002-Tutorial-00010_100.mov"/>
  </video>

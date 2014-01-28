.. _Working with Video Components:

#############################
Working with Video Components
#############################


**********************
Introduction to Videos
**********************
You can create a video of your lecture and add it to your course with other components—such 
as discussions and problems—to promote active learning. Adding a video to your course has several steps.

#. Create the video.
#. Create or obtain a transcript for the video.
#. Post the video online.
#. In Studio, create a Video component.

.. note:: Review :ref:`Best Practices for Accessible Media` before adding videos to your course.

************************
Step 1. Create the Video
************************

Your video can contain whatever content you want. The `Producing Videos <https://edge.edx.org/courses/edX/edX101/How_to_Create_an_edX_Course/courseware/93451eee15ed47b0a310c19020e8dc64/a1b0835e986b4283b0f8871d97babb9a/>`_ 
section of our `edX101 <https://edge.edx.org/courses/edX/edX101/How_to_Create_an_edX_Course/about>`_ 
course has some helpful pointers for creating good video content.


Compression Specifications
--------------------------

When you create your video, edX recommends the following compression specs. (Note that 
these are recommended but not required.)

.. list-table::
   :widths: 10 20 20 20
   :header-rows: 0
   :stub-columns: 1

   * - Output
     - Edited Files
     - Publish to YouTube
     - Publish downloadable file to AWS S3
   * - Codec
     - H.264 .mp4
     - H.264 "main concept" .mp4
     - H.264 "x264" .mp4
   * - Resolution and Frame Rate
     - 1920x1080, progressive, 29.97 fps
     - 1920x1080, progressive, 29.97 fps 
     - 1280x720, progressive, 29.97 fps
   * - Aspect
     - 1.0
     - 1.0
     - 1.0
   * - Bit Rate
     - VBR, 2 pass 
     - VBR, 2 pass 
     - VBR, 2 pass  
   * - Target VBR
     - 32 mbps
     - 5 mbps
     - 1 mbps
   * - Max VBR
     - 40 mbps
     - 7.5 mbps
     - 1.5 mbps
   * - Audio
     - Linear AAC 48kHz / 256 kbps
     - AAC 44.1 / 192 kbps
     - AAC 44.1 / 192 kbps

.. _Video Formats:

Video Formats
-------------

The edX video player supports videos in .mp4, .mpeg, .ogg, and .webm format.

*********************************************
Step 2. Create or Obtain a Video Transcript
*********************************************

We strongly recommend that you associate a timed transcript with your video. Transcripts can be helpful for students whose first language isn't English, or who can't watch the video or want to review the video's content. The transcript scrolls automatically while your video plays. When a student clicks a word in the transcript, the video opens to that word. You can also allow your students to download the transcript so that they can read it offline. You'll associate the transcript with the video when you create the Video component.

To create or obtain a transcript, you can work with a company that provides captioning services. EdX works with `3Play Media <http://www.3playmedia.com>`_. `YouTube <http://www.youtube.com/>`_ also provides captioning services. 

Transcript Format
-----------------

Your transcript must be an .srt file.

.. note:: Some past courses have used .sjson files for video transcripts. If transcripts in your course uses this format, see :ref:`Steps for sjson files`. We don't recommend that you use .sjson files.


*****************************
Step 3. Post the Video Online
*****************************

All course videos should be posted to YouTube. By default, the edX video player accesses your YouTube videos. 

Because YouTube is not available in all locations, however, we recommend that you also post 
copies of your videos on a third-party site such as `Amazon S3 <http://aws.amazon.com/s3/>`_. When a student views 
a video in your course, if YouTube is not available in that student’s location or if 
the YouTube video doesn’t play, the video on the backup site starts playing automatically. 
The student can also click a link to download the video from the backup site.

After you post your video online, make sure you have the URL for the video. If you host copies of your video in more than one place, make sure you have the URL for each video location.


YouTube
-------

After you've created your video, upload the video to `YouTube <http://www.youtube.com/>`_. 

.. note:: YouTube only hosts videos of up to 15 minutes. If you create a 0.75-speed option, you must make sure that your 1.0-speed video segments are only 11.25 minutes long so that YouTube can host all speeds. YouTube offers paid accounts that relax this restriction.

Other Sites
-----------

You can use any video backup site that you want. However, keep in mind that the site where you 
post the videos may have to handle a lot of traffic.

.. note:: The URL for the video that you post on a third-party site must end in .mp4, .mpeg, .ogg, or .webm. EdX can't support videos that you post on sites such as Vimeo. 



.. _Create a Video Component:

********************************
Step 4. Create a Video Component
********************************

#. Under **Add New Component**, click **Video**.

#. When the new video component appears, click **Edit**. The video editor opens to the **Basic** tab.

   .. image:: Images/VideoComponentEditor.gif

   You'll replace the default values with your own. 
   
#. In the **Display Name** field, enter the name you want students to see when they hover the mouse 
   over the unit in the course accordion. This text also appears as a header for the video.

#. In the **Video URL** field, enter the URL of the video. For example, the URL may resemble one of the following.

   ::
   
      http://youtu.be/OEoXaMPEzfM
      http://www.youtube.com/watch?v=OEoXaMPEzfM
      https://s3.amazonaws.com/edx-course-videos/edx-edx101/EDXSPCPJSP13-G030300.mp4	


#. Next to **Timed Transcript**, select an option.

   - If edX already has a transcript for your video, Studio automatically finds the transcript and associates the transcript with the video. For example, edX may have a transcript for your video if you're using a video from an existing course.
     
     If you want to modify the transcript, click **Download to Edit**. You can then make your changes and upload the new file by clicking **Upload New Timed Transcript**.

   - If your video has a transcript on YouTube, Studio automatically finds the transcript and asks if you want to import it. To use this YouTube transcript, click **Import from YouTube**. (If you want to modify the YouTube transcript, click **Download to Edit**. You can then make your changes and upload the new file by clicking **Upload New Timed Transcript**.)

   - If neither edX nor YouTube has a transcript for your video, and your transcript uses the .srt format, click **Upload New Timed Transcript** to upload the transcript file from your computer. 

     .. note:: If your transcript uses the .sjson format, do not use this setting. For more information, see :ref:`Steps for sjson files`.

#. Optionally, click **Advanced** to set more options for the video. For a description of each option, see the table below.

#. Click **Save.**
  
Advanced Options
----------------

.. list-table::
   :widths: 20 80
   :header-rows: 0

   * - **Display Name**
     - The name that you want your students to see. This is the same as the **Display Name** field on the **Basic** tab.
   * - **End Time**
     - The time, formatted as hours, minutes, and seconds (HH:MM:SS), when you want the video to end.
   * - **HTML5 Transcript**
     - If you uploaded an .srt file on the **Basic** tab, the name of your .srt file appears in this field by default. You don't have to change this setting.
       If your transcript uses an .sjson file, see :ref:`Steps for sjson files`.
   * - **Show Transcript**
     - Specifies whether you want the transcript to show by default. Students can always turn transcripts on or off while they watch the video.
   * - **Start Time**
     - The time, formatted as hours, minutes, and seconds (HH:MM:SS), when you want the video to begin. 
   * - **Transcript Download Allowed**
     - Specifies whether you want to allow your students to download a copy of the transcript. 
   * - **Video Download Allowed**
     - Specifies whether you want to allow your students to download a copy of the video.
   * - **Video Sources**
     - Additional locations where you've posted the video. This field must contain a URL that ends in .mpeg, .mp4, .ogg, or .webm.
   * - **YouTube ID, YouTube ID for .75x speed, YouTube ID for 1.25x speed, YouTube ID for 1.5x speed**
     - If you have uploaded separate videos to YouTube for different speeds of your video, enter the YouTube IDs for these videos in these fields.

.. _Steps for sjson files:

**********************
Steps for .sjson Files
**********************

If your course uses .sjson files, you'll upload the .sjson file for the video to the **Files & Uploads** page, and then specify the name of the .sjson file in the Video component.

.. note:: Only older courses that have used .sjson files in the past should use .sjson files. All new courses should use .srt files. 

#. Obtain the .sjson file from a media company such as 3Play.
#. Change the name of the .sjson file to use the following format:
   
   ``subs_FILENAME.srt.sjson``
   
   For example, if the name of your video is **Lecture1a**, the name of your .sjson file must be **subs_Lecture1a.srt.sjson**.
#. Upload the .sjson file for your video to the **Files & Uploads** page.
#. Create a new video component.
#. On the **Basic** tab, enter the name that you want students to see in the **Display Name** field.
#. In the **Video URL** field, enter the URL of the video. For example, the URL may resemble one of the following.

   ::
   
      http://youtu.be/OEoXaMPEzfM
      http://www.youtube.com/watch?v=OEoXaMPEzfM
      https://s3.amazonaws.com/edx-course-videos/edx-edx101/EDXSPCPJSP13-G030300.mp4

#. Click the **Advanced** tab.
#. In the **HTML5 Transcript** field, enter the file name of your video. Do not include "subs\_" or ".sjson". For the example in step 2, you would only enter **Lecture1a**.
#. Set the other options that you want.
#. Click **Save**.

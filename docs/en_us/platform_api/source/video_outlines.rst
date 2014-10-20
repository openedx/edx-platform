##################################################
Video Outlines API Module
##################################################

.. module:: mobile_api

This page contains docstrings and example responses for:

* `Get the Video List`_
* `Get a Video Transcript`_

.. _Get the Video List:

*******************
Get the Video List
*******************

.. .. autoclass:: video_outlines.views.VideoSummaryList
..    :members:

**Use Case**

Get a list of all videos in the specified course. You can use the video_url
value to access the video file.

**Example request**:

``GET /api/mobile/v0.5/video_outlines/courses/{organization}/{course_number}/{course_run}``

**Response Values**

An array of videos in the course. For each video:

* section_url: The URL to the first page of the section that contains the video
  in the Learning Managent System.

* path: An array containing category and name values specifying the complete
  path the the video in the courseware hierarcy. The following categories
  values are included: "chapter", "sequential", and "vertical". The name value
  is the display name for that object.

* unit_url: The URL to the unit contains the video in the Learning Managent
  System.

* named_path: An array consisting of the display names of the courseware
  objects in the path to the video.

* summary:  An array of data about the video that includes:

    * category:  The type of component, in this case always "video".

    * video_thumbnail_url: The URL to the thumbnail image for the video, if
      available.

    * language: The language code for the video.

    * name:  The display name of the video.

    * video_url: The URL to the video file. Use this value to access the video.

    * duration: The length of the video, if available.

    * transcripts: An array of language codes and URLs to available video
      transcripts. Use the URL value to access a transcript for the video.

    * id: The unique identifier for the video.

    * size: The size of the video file

**Example response**

.. code-block:: json

    HTTP 200 OK  
    Vary: Accept   
    Content-Type: text/html; charset=utf-8   
    Allow: GET, HEAD, OPTIONS 

    [
        {
            "section_url": "http://localhost:8000/courses/edX/Open_DemoX/edx_demo_course/courseware/d8a6192ade314473a78242dfeedfbf5b/edx_introduction/", 
            "path": [
                {
                    "category": "chapter", 
                    "name": "Introduction"
                }, 
                {
                    "category": "sequential", 
                    "name": "Demo Course Overview"
                }, 
                {
                    "category": "vertical", 
                    "name": "Introduction: Video and Sequences"
                }
            ], 
            "unit_url": "http://localhost:8000/courses/edX/Open_DemoX/edx_demo_course/courseware/d8a6192ade314473a78242dfeedfbf5b/edx_introduction/1", 
            "named_path": [
                "Introduction", 
                "Demo Course Overview"
            ], 
            "summary": {
                "category": "video", 
                "video_thumbnail_url": null, 
                "language": "en", 
                "name": "Welcome!", 
                "video_url": "https://s3.amazonaws.com/edx-course-videos/edx-edx101/EDXSPCPJSP13-H010000_100.mp4", 
                "duration": null, 
                "transcripts": {
                    "en": "http://localhost:8000/api/mobile/v0.5/video_outlines/transcripts/edX/Open_DemoX/edx_demo_course/0b9e39477cf34507a7a48f74be381fdd/en"
                }, 
                "id": "i4x://edX/Open_DemoX/video/0b9e39477cf34507a7a48f74be381fdd", 
                "size": 0
            }
        }
    ] 

.. _Get a Video Transcript:

***********************
Get a Video Transcript
***********************

.. .. autoclass:: video_outlines.views.VideoTranscripts
..    :members:

**Use Case**

Use to get a transcript for a specified video and language.

**Example request**:

``/api/mobile/v0.5/video_outlines/transcripts/{organization}/{course_number}/{course_run}/{video ID}/{language code}``
    
**Response Values**

An HttpResponse with an SRT file download.
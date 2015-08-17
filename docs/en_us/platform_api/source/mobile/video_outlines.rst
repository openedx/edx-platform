##################################################
Mobile Video Outlines API
##################################################

This page describes how to use the Mobile Video Outlines API to
complete these actions:

* `Get the Video List`_
* `Get a Video Transcript`_

.. _Get the Video List:

*******************
Get the Video List
*******************

.. autoclass:: mobile_api.video_outlines.views.VideoSummaryList


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

.. autoclass:: mobile_api.video_outlines.views.VideoTranscripts
    
**Response Values**

An HttpResponse with an SRT file download.
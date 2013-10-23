.. module:: transcripts

======================================================
Developer’s workflow for the timed transcripts in CMS.
======================================================

:download:`Multipage pdf version of Timed Transcripts workflow. <transcripts_workflow.pdf>`

:download:`Open office graph version (source for pdf). <transcripts_workflow.odg>`

:download:`List of implemented acceptance tests. <transcripts_acceptance_tests.odt>`


Description
===========

Timed Transcripts functionality is added in separate tab of Video module Editor, that is active by default. This tab is called `Basic`, another tab is called `Advanced` and contains default metadata fields.

`Basic` tab is a simple representation of `Advanced` tab that provides functionality to speed up adding Video module with transcripts to the course.

To make more accurate adjustments `Advanced` tab should be used.

Front-end part of `Basic` tab has 4 editors/views:
    * Display name
    * 3 editors for inserting Video URLs.

Video URL fields might contain 3 kinds of URLs:
    * **YouTube** link. There are supported formats:
        * http://www.youtube.com/watch?v=OEoXaMPEzfM&feature=feedrec_grec_index ;
        * http://www.youtube.com/user/IngridMichaelsonVEVO#p/a/u/1/OEoXaMPEzfM ;
        * http://www.youtube.com/v/OEoXaMPEzfM?fs=1&amp;hl=en_US&amp;rel=0 ;
        * http://www.youtube.com/watch?v=OEoXaMPEzfM#t=0m10s ;
        * http://www.youtube.com/embed/OEoXaMPEzfM?rel=0 ;
        * http://www.youtube.com/watch?v=OEoXaMPEzfM ;
        * http://youtu.be/OEoXaMPEzfM ;

    * **MP4** video source;
    * **WEBM** video source.

Each of these kind of URLs can be specified just **ONCE**. Otherwise, error message occurs on front-end.

After filling editor **transcripts/check** method will be invoked with the parameters described below  (see `API`_). Depending on conditions, that are also described below (see `Commands`_), this method responds with a *command* and front-end renders the appropriate View.
Each View can have specific actions. There is a list of supported actions:
    * Download Timed Transcripts;
    * Upload Timed Transcripts;
    * Import Timed Transcripts from YouTube;
    * Replace edX Timed Transcripts by Timed Transcripts from YouTube;
    * Choose Timed Transcripts;
    * Use existing Timed Transcripts.

All of these actions are handled by 7 API methods described below (see `API`_).

Because rollback functionality isn't implemented now, after invoking some of the actions user cannot revert changes by clicking button `Cancel`.

To remove timed transcripts file from the video just go to `Advanced` tab and clear field `sub` then Save changes.


Commands
========

Command from front-end point of view is just a reference to the needed View with possible actions that user can do depending on conditions described below (See edx-platform/cms/static/js/views/transcripts/message_manager.js:21-29).

So,
   * **IF** YouTube transcripts present locally **AND** on YouTube server **AND** both of these transcripts files are **DIFFERENT**, we respond with `replace` command. Ask user to replace local transcripts file by YouTube's ones.
   * **IF** YouTube transcripts present **ONLY** locally, we respond with `found` command.
   * **IF** YouTube transcripts present **ONLY** on YouTube server, we respond with `import` command. Ask user to import transcripts file from YouTube server.
   * **IF** player is in HTML5 video mode. It means that **ONLY** html5 sources are added:
        * **IF** just 1 html5 source was added or both html5 sources have **EQUAL** transcripts files, then we respond with `found` command.
        * **OTHERWISE**, when 2 html5 sources were added and founded transcripts files are **DIFFERENT**, we respond with `choose` command. In this case, user should choose which one transcripts file he wants to use.
   * **IF** we are working with just 1 field **AND** item.sub field **HAS** a value **AND** user fills editor/view by the new value/video source without transcripts file, we respond with `use_existing` command. In this case, user will have possibility to use transcripts file from previous video.
   * **OTHERWISE**, we will respond with `not_found` command.


Synchronization and Saving workflow
====================================


For now saving mechanism works as follows:

On click `Save` button **ModuleEdit** class (See edx-platform/cms/static/coffee/src/views/module_edit.coffee:83-101) grabs values from all modified metadata fields and sends all this data to the server.

Because of the fact that Timed Transcripts is module specific functionality, ModuleEdit class is not extended. Instead, to apply all changes that user did in the `Basic` tab, we use synchronization mechanism of TabsEditingDescriptor class. That mechanism provides us possibility to do needed actions on Tab switching and on Save (See edx-platform/cms/templates/widgets/video/transcripts.html).

On tab switching and when save action is invoked, JavaScript code synchronize collections (Metadata Collection and Transcripts Collection). You can see synchronization logic in the edx-platform/cms/static/js/views/transcripts/editor.js:72-219. In this case, Metadata fields always have the actual data.


Special cases
=============

1. Status message `Timed Transcript Conflict` (Choose) where one of 2 transcripts files should be chosen **-->** click `Save` button without choosing **-->** open Editor **-->** status message `Timed Transcript Found` will be shown and transcripts file will be chosen in random order.

2. status message `Timed Transcript Conflict` (Choose) where one of 2 transcripts files should be chosen **-->** open `Advanced` tab without choosing **-->** get back to `Basic` tab **-->** status message `Timed Transcript Found` will be shown and transcripts file will be chosen in random order.

3. The same issues with `Timed Transcript Not Updated` (Use existing).

API
===

We provide 7 API methods to work with timed transcripts
(edx-platform/cms/urls.py:23-29):
    * transcripts/upload
    * transcripts/download
    * transcripts/check
    * transcripts/choose
    * transcripts/replace
    * transcripts/rename
    * transcripts/save

**"transcripts/upload"** method is used for uploading SRT transcripts for the
HTML5 and YouTube video modules.

*Method:*
    POST
*Parameters:*
    - id - location ID of the Xmodule
    - video_list - list with information about the links currently passed in the editor/view.
    - file - BLOB file
*Response:*
    HTTP 400
    or
    HTTP 200 + JSON:
    .. code::
        {
            status: 'Success' or 'Error',
            subs: value of uploaded and saved sub field in the video item.
        }


**"transcripts/download"** method is used for downloading SRT transcripts for the
HTML5 and YouTube video modules.

*Method:*
    GET
*Parameters:*
    - id - location ID of the Xmodule
    - subs_id - file name that is used to find transcripts file in the storage.
*Response:*
    HTTP 404
    or
    HTTP 200 + BLOB of SRT file


**"transcripts/check"** method is used for checking availability of timed transcripts
for the video module.

*Method:*
    GET
*Parameters:*
    - id - location ID of the Xmodule
*Response:*
    HTTP 400
    or
    HTTP 200 + JSON:
    .. code::
        {
            command: string with action to front-end what to do and what to show to user,
            subs: file name of transcripts file that was found in the storage,
            html5_local: [] or [True] or [True, True],
            is_youtube_mode: True/False,
            youtube_local: True/False,
            youtube_server: True/False,
            youtube_diff: True/False,
            current_item_subs: string with value of item.sub field,
            status: 'Error' or 'Success'
        }


**"transcripts/choose"** method is used for choosing which transcripts file should be used.

*Method:*
    GET
*Parameters:*
    - id - location ID of the Xmodule
    - video_list - list with information about the links currently passed in the editor/view.
    - html5_id - file name of chosen transcripts file.

*Response:*
    HTTP 200 + JSON:
    .. code::
        {
            status: 'Success' or 'Error',
            subs: value of uploaded and saved sub field in the video item.
        }


**"transcripts/replace"** method is used for handling `import` and `replace` commands.
Invoking this method starts downloading new transcripts file from YouTube server.

*Method:*
    GET
*Parameters:*
    - id - location ID of the Xmodule
    - video_list - list with information about the links currently passed in the editor/view.

*Response:*
    HTTP 400
    or
    HTTP 200 + JSON:
    .. code::
        {
            status: 'Success' or 'Error',
            subs: value of uploaded and saved sub field in the video item.
        }


**"transcripts/rename"** method is used for handling `use_existing` command.
After invoking this method current transcripts file will be copied and renamed to another one with name of current video passed in the editor/view.

*Method:*
    GET
*Parameters:*
    - id - location ID of the Xmodule
    - video_list - list with information about the links currently passed in the editor/view.

*Response:*
    HTTP 400
    or
    HTTP 200 + JSON:
    .. code::
        {
            status: 'Success' or 'Error',
            subs: value of uploaded and saved sub field in the video item.
        }


**"transcripts/save"** method is used for handling `save` command.
After invoking this method all changes will be saved that were done before this moment.

*Method:*
    GET
*Parameters:*
    - id - location ID of the Xmodule
    - metadata - new values for the metadata fields.
    - currents_subs - list with the file names of videos passed in the editor/view.

*Response:*
    HTTP 400
    or
    HTTP 200 + JSON:
    .. code::
        {
            status: 'Success' or 'Error'
        }


Transcripts modules:
====================

.. automodule:: contentstore.views.transcripts_ajax
    :members:
    :show-inheritance:

.. automodule:: contentstore.transcripts_utils
    :members:
    :show-inheritance:


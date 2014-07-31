###################
Course XML Tutorial
###################
EdX uses an XML format to describe the structure and contents of its courses. While much of this is abstracted away by the Studio authoring interface, it is still helpful to understand how the edX platform renders a course.

This guide was written with the assumption that you've dived straight into the edX platform without necessarily having any prior programming/CS knowledge. It will be especially valuable to you if your course is being authored with XML files rather than Studio -- in which case you're likely using functionality that is not yet fully supported in Studio.

*****
Goals
*****
After reading this, you should be able to:

* Organize your course content into the files and folders the edX platform expects.
* Add new content to a course and make sure it shows up in the courseware.

*Prerequisites:* it would be helpful to know a little bit about xml.  Here is a 
`simple example <http://www.ultraslavonic.info/intro-to-xml/>`_ if you've never seen it before. 

************
Introduction
************

A course is organized hierarchically. We start by describing course-wide parameters, then break the course into chapters, and then go deeper and deeper until we reach a specific pset, video, etc. You could make an analogy to finding a green shirt in your house -> bedroom -> closet -> drawer -> shirts -> green shirt.

We'll begin with a sample course structure as a case study of how XML and files in a course are organized. More technical details will follow, including discussion of some special cases.

**********
Case Study
**********
Let's jump right in by looking at the directory structure of a very simple toy course::

  toy/
      course/
      course.xml
      problem/
      policies/
      roots/

The only top level file is `course.xml`, which should contain one line, looking something like this:

.. code-block:: xml

  <course org="edX" course="toy" url_name="2012_Fall"/>

This gives all the information to uniquely identify a particular run of any course -- which organization is producing the course, what the course name is, and what "run" this is, specified via the `url_name` attribute.

Obviously, this doesn't actually specify any of the course content, so we need to find that next.  To know where to look, you need to know the standard organizational structure of our system: course elements are uniquely identified by the combination `(category, url_name)`. In this case, we are looking for a `course` element with the `url_name` "2012_Fall". The definition of this element will be in `course/2012_Fall.xml`. Let's look there next::

  toy/
      course/
             2012_Fall.xml # <-- Where we look for category="course", url_name="2012_Fall"

.. code-block:: xml

  <!-- Contents of course/2012_Fall.xml -->
  <course>
    <chapter url_name="Overview">
      <videosequence url_name="Toy_Videos">
        <problem url_name="warmup"/>
        <video url_name="Video_Resources" youtube="1.0:1bK-WdDi6Qw"/>
      </videosequence>
      <video url_name="Welcome" youtube="1.0:p2Q6BrNhdh8"/>
    </chapter>
  </course>

Aha. Now we've found some content. We can see that the course is organized hierarchically, in this case with only one chapter, with `url_name` "Overview". The chapter contains a `videosequence` and a `video`, with the sequence containing a problem and another video. When viewed in the courseware, chapters are shown at the top level of the navigation accordion on the left, with any elements directly included in the chapter below.

Looking at this file, we can see the course structure, and the youtube urls for the videos, but what about the "warmup" problem?  There is no problem content here! Where should we look? This is a good time to pause and try to answer that question based on our organizational structure above.

As you hopefully guessed, the problem would be in `problem/warmup.xml`.  (Note: This tutorial doesn't discuss the xml format for problems -- there are chapters of edx4edx that describe it.)  This is an instance of a *pointer tag*: any xml tag with only the category and a url_name attribute will point to the file `{category}/{url_name}.xml`.  For example, this means that our toy `course.xml` could have also been written as

.. code-block:: xml

  <!-- Contents of course/2012_Fall.xml -->
  <course>
    <chapter url_name="Overview"/>
  </course>

with `chapter/Overview.xml` containing

.. code-block:: xml

  <chapter>
    <videosequence url_name="Toy_Videos">
      <problem url_name="warmup"/>
      <video url_name="Video_Resources" youtube="1.0:1bK-WdDi6Qw"/>
    </videosequence>
    <video url_name="Welcome" youtube="1.0:p2Q6BrNhdh8"/>
  </chapter>

In fact, this is the recommended structure for real courses -- putting each chapter into its own file makes it easy to have different people work on each without conflicting or having to merge.  Similarly, as sequences get large, it can be handy to split them out as well (in `sequence/{url_name}.xml`, of course).

Note that the `url_name` is only specified once per element -- either the inline definition, or in the pointer tag.

Policy Files
============

We still haven't looked at two of the directories in the top-level listing above: `policies` and `roots`.  Let's look at policies next.  The policy directory contains one file::

  toy/
      policies/
               2012_Fall.json

and that file is named `{course-url_name}.json`.  As you might expect, this file contains a policy for the course. In our example, it looks like this:

.. code-block:: json

    {
        "course/2012_Fall": {
            "graceperiod": "2 days 5 hours 59 minutes 59 seconds",
            "start": "2015-07-17T12:00",
            "display_name": "Toy Course"
        },
        "chapter/Overview": {
            "display_name": "Overview"
        },
        "videosequence/Toy_Videos": {
            "display_name": "Toy Videos",
            "format": "Lecture Sequence"
        },
        "problem/warmup": {
            "display_name": "Getting ready for the semester"
        },
        "video/Video_Resources": {
            "display_name": "Video Resources"
        },
        "video/Welcome": {
            "display_name": "Welcome"
        }
    }

The policy specifies metadata about the content elements -- things which are not inherent to the definition of the content, but which describe how the content is presented to the user and used in the course.  
See below for a full list of metadata attributes; as the example shows, they include `display_name`, which is what is shown when this piece of content is referenced or shown in the courseware, and various dates and times, like `start`, which specifies when the content becomes visible to students, and various problem-specific parameters like the allowed number of attempts.  
One important point is that some metadata is inherited: for example, specifying the start date on the course makes it the default for every element in the course.  
See below for more details.

It is possible to put metadata directly in the XML, as attributes of the appropriate tag, but using a policy file has two benefits: 
it puts all the policy in one place, making it easier to check that things like due dates are set properly, and it allows the content definitions to be easily used in another run of the same course, with the same or similar content, but different policy.

Roots
=====
The last directory in the top level listing is `roots`.  In our toy course, it contains a single file::

  roots/
        2012_Fall.xml

This file is identical to the top-level `course.xml`, containing

.. code-block:: xml

  <course org="edX" course="toy" url_name="2012_Fall"/>

In fact, the top level `course.xml` is a symbolic link to this file.  When there is only one run of a course, the roots directory is not really necessary, and the top-level course.xml file can just specify the `url_name` of the course.  However, if we wanted to make a second run of our toy course, we could add another file called, e.g., `roots/2013_Spring.xml`, containing

.. code-block:: xml

  <course org="edX" course="toy" url_name="2013_Spring"/>

After creating `course/2013_Spring.xml` with the course structure (possibly as a symbolic link or copy of `course/2012_Fall.xml` if no content was changing), and `policies/2013_Spring.json`, we would have two different runs of the toy course in the course repository.  Our build system understands this roots structure, and will build a course package for each root.

.. note::
   If you're using a local development environment, make the top level `course.xml` point to the desired root, and check out the repo multiple times if you need multiple runs simultaneously).

That's basically all there is to the organizational structure.  Read the next section for details on the tags we support, including some special case tags like `customtag` and `html` invariants, and look at the end for some tips that will make the editing process easier.

****
Tags
****

  .. list-table::
     :widths: 10 80
     :header-rows: 0
     
     * - `abtest`
       - Support for A/B testing.  TODO: add details..
     * - `chapter`
       - Top level organization unit of a course. The courseware display code currently expects the top level `course` element to contain only chapters, though there is no philosophical reason why this is required, so we may change it to properly display non-chapters at the top level.
     * - `conditional`
       - Conditional element, which shows one or more modules only if certain conditions are satisfied.
     * - `course`
       - Top level tag.  Contains everything else.
     * - `customtag` 
       - Render an html template, filling in some parameters, and return the resulting html. See below for details.
     * - `discussion`
       - Inline discussion forum.
     * - `html`
       - A reference to an html file.
     * - `error`
       - Don't put these in by hand :) The internal representation of content that has an error, such as malformed XML or some broken invariant.
     * - `problem`
       - See elsewhere in edx4edx for documentation on the format.
     * - `problemset`
       - Logically, a series of related problems. Currently displayed vertically. May contain explanatory html, videos, etc.
     * - `sequential`
       - A sequence of content, currently displayed with a horizontal list of tabs. If possible, use a more semantically meaningful tag (currently, we only have `videosequence`).
     * - `vertical`
       - A sequence of content, displayed vertically. Content will be accessed all at once, on the right part of the page. No navigational bar. May have to use browser scroll bars. Content split with separators. If possible, use a more semantically meaningful tag (currently, we only have `problemset`).
     * - `video`
       - A link to a video, currently expected to be hosted on youtube.
     * - `videosequence`
       - A sequence of videos.  This can contain various non-video content; it just signals to the system that this is logically part of an explanatory sequence of content, as opposed to say an exam sequence.

Container Tags
==============
Container tags include `chapter`, `sequential`, `videosequence`, `vertical`, and `problemset`. They are all specified in the same way in the xml, as shown in the tutorial above.

`course`
========
`course` is also a container, and is similar, with one extra wrinkle: the top level pointer tag *must* have  `org` and `course` attributes specified--the organization name, and course name. Note that `course` is referring to the platonic ideal of this course (e.g. "6.002x"), not to any particular run of this course. The `url_name` should be the particular run of this course.

`conditional`
=============
`conditional` is as special kind of container tag as well.  Here are two examples:

  .. code-block:: xml
  
    <conditional condition="require_completed" required="problem/choiceprob">
      <video url_name="secret_video" />
    </conditional>
  
    <conditional condition="require_attempted" required="problem/choiceprob&problem/sumprob">
      <html url_name="secret_page" />
    </conditional>

The condition can be either `require_completed`, in which case the required modules must be completed, or `require_attempted`, in which case the required modules must have been attempted.

The required modules are specified as a set of `tag`/`url_name`, joined by an ampersand.

`customtag`
===========
When we see:

  .. code-block:: xml

    <customtag impl="special" animal="unicorn" hat="blue"/>

We will:

#. Look for a file called `custom_tags/special`  in your course dir.
#. Render it as a mako template, passing parameters {'animal':'unicorn', 'hat':'blue'}, generating html.  (Google `mako` for template syntax, or look at existing examples).

Since `customtag` is already a pointer, there is generally no need to put it into a separate file--just use it in place:

  .. code-block:: xml

    <customtag url_name="my_custom_tag" impl="blah" attr1="..."/>

`discussion`
============
The discussion tag embeds an inline discussion module. The XML format is:

  .. code-block:: xml

    <discussion for="Course overview" id="6002x_Fall_2012_Overview" discussion_category="Week 1/Overview" />

The meaning of each attribute is as follows:

  .. list-table::
     :widths: 10 80
     :header-rows: 0

     * - `for`
       - A string that describes the discussion. Purely for descriptive purposes (to the student).
     * - `id`
       - The identifier that the discussion forum service uses to refer to this inline discussion module. Since the `id` must be unique and lives in a common namespace with all other courses, the preferred convention is to use `<course_name>_<course_run>_<descriptor>` as in the above example. The `id` should be "machine-friendly", e.g. use alphanumeric characters, underscores. Do **not** use a period (e.g. `6.002x_Fall_2012_Overview`).
     * - `discussion_category`
       - The inline module will be indexed in the main "Discussion" tab of the course. The inline discussions are organized into a directory-like hierarchy. Note that the forward slash indicates depth, as in conventional filesytems. In the above example, this discussion module will show up in the following "directory": `Week 1/Overview/Course overview`

Note that the `for` tag has been appended to the end of the `discussion_category`. This can often lead into deeply nested subforums, which may not be intended. In the above example, if we were to use instead:

  .. code-block:: xml

   <discussion for="Course overview" id="6002x_Fall_2012_Overview" discussion_category="Week 1" />

This discussion module would show up in the main forums as `Week 1 / Course overview`, which is more succinct.

`html`
======
Most of our content is in XML, but some HTML content may not be proper xml (all tags matched, single top-level tag, etc), since browsers are fairly lenient in what they'll display.  So, there are two ways to include HTML content:

* If your HTML content is in a proper XML format, just put it in `html/{url_name}.xml`.
* If your HTML content is not in proper XML format, you can put it in `html/{filename}.html`, and put `<html filename={filename} />` in `html/{filename}.xml`.  This allows another level of indirection, and makes sure that we can read the XML file and then just return the actual HTML content without trying to parse it.

`video`
=======
Videos have an attribute `youtube`, which specifies a series of speeds + youtube video IDs:

  .. code-block:: xml

    <video youtube="0.75:1yk1A8-FPbw,1.0:vNMrbPvwhU4,1.25:gBW_wqe7rDc,1.50:7AE_TKgaBwA" 
           url_name="S15V14_Response_to_impulse_limit_case"/>

This video has been encoded at 4 different speeds: `0.75x`, `1x`, `1.25x`, and `1.5x`.

More on `url_name`
==================
Every content element (within a course) should have a unique id.  This id is formed as `{category}/{url_name}`, or automatically generated from the content if `url_name` is not specified.  Categories are the different tag types ('chapter', 'problem', 'html', 'sequential', etc).  Url_name is a string containing a-z, A-Z, 0-9, dot (.), underscore (_), and ':'.  This is what appears in urls that point to this object.

Colon (':') is special--when looking for the content definition in an xml, ':' will be replaced with '/'.  This allows organizing content into folders.  For example, given the pointer tag

  .. code-block:: xml

    <problem url_name="conceptual:add_apples_and_oranges"/>

we would look for the problem definition in `problem/conceptual/add_apples_and_oranges.xml`. (There is a technical reason why we can't just allow '/' in the url_name directly.)

.. important::
  A student's state for a particular content element is tied to the element ID, so automatic ID generation is only ok for elements that do not need to store any student state (e.g. verticals or customtags).  For problems, sequentials, and videos, and any other element where we keep track of what the student has done and where they are at, you should specify a unique `url_name`. Of course, any content element that is split out into a file will need a `url_name` to specify where to find the definition.


************
Policy Files
************
* A policy file is useful when running different versions of a course e.g. internal, external, fall, spring, etc. as you can change due dates, etc, by creating multiple policy files.
* A policy file provides information on the metadata of the course--things that are not inherent to the definitions of the contents, but that may vary from run to run.
* Note: We will be expanding our understanding and format for metadata in the not-too-distant future, but for now it is simply a set of key-value pairs.

Locations
=========
* The policy for a course run `some_url_name` should live in `policies/some_url_name/policy.json`  (NOTE: the old format of putting it in `policies/some_url_name.json` will also work, but we suggest using the subdirectory to have all the per-course policy files in one place)
* Grading policy files go in `policies/some_url_name/grading_policy.json`   (if there's only one course run, can also put it directly in the course root: `/grading_policy.json`)

Contents
========
* The file format is JSON, and is best shown by example, as in the tutorial above.
* The expected contents are a dictionary mapping from keys to values (syntax `{ key : value, key2 : value2, etc}`)
* Keys are in the form `{category}/{url_name}`, which should uniquely identify a content element. Values are dictionaries of the form `{"metadata-key" : "metadata-value"}`.
* The order in which things appear does not matter, though it may be helpful to organize the file in the same order as things appear in the content.
* NOTE: JSON is picky about commas.  If you have trailing commas before closing braces, it will complain and refuse to parse the file.  This can be irritating at first.

Supported fields at the course level
====================================

  .. list-table::
     :widths: 10 80
     :header-rows: 0

     * - `start`
       - specify the start date for the course.  Format-by-example: `"2012-09-05T12:00"`.
     * - `advertised_start`
       - specify what you want displayed as the start date of the course in the course listing and course about pages. This can be useful if you want to let people in early before the formal start. Format-by-example: `"2012-09-05T12:"00`.
     * - `disable_policy_graph`
       - set to true (or "Yes"), if the policy graph should be disabled (ie not shown).
     * - `enrollment_start`, `enrollment_end`
       - -- when can students enroll?  (if not specified, can enroll anytime). Same format as `start`.
     * - `end`
       - specify the end date for the course.  Format-by-example: `"2012-11-05T12:00"`.
     * - `end_of_course_survey_url`
       - a url for an end of course survey -- shown after course is over, next to certificate download links.
     * - `tabs`
       - have custom tabs in the courseware.  See below for details on config.
     * - `discussion_blackouts`
       - An array of time intervals during which you want to disable a student's ability to create or edit posts in the forum. Moderators, Community TAs, and Admins are unaffected. You might use this during exam periods, but please be aware that the forum is often a very good place to catch mistakes and clarify points to students. The better long term solution would be to have better flagging/moderation mechanisms, but this is the hammer we have today. Format by example: `[[""2012-10-29T04:00", "2012-11-03T04:00"], ["2012-12-30T04:00", "2013-01-02T04:00"]]`
     * - `show_calculator`
       - (value "Yes" if desired)
     * - `days_early_for_beta`
       - number of days (floating point ok) early that students in the beta-testers group get to see course content.  Can also be specified for any other course element, and overrides values set at higher levels.
     * - `cohort_config`
       -
          * `cohorted` : boolean.  Set to true if this course uses student cohorts.  If so, all inline discussions are automatically cohorted, and top-level discussion topics are configurable via the cohorted_discussions list. Default is not cohorted).
          * `cohorted_discussions`: list of discussions that should be cohorted.  Any not specified in this list are not cohorted.
          * `auto_cohort`: Truthy.
          * `auto_cohort_groups`: `["group name 1", "group name 2", ...]` If `cohorted` and `auto_cohort` is true, automatically put each student into a random group from the `auto_cohort_groups` list, creating the group if needed.  
     * - `pdf_textbooks`
       - have pdf-based textbooks on tabs in the courseware.  See below for details on config.
     * - `html_textbooks`
       - have html-based textbooks on tabs in the courseware.  See below for details on config.


Available metadata
==================

Not Inherited
--------------
`display_name`
  Name that will appear when this content is displayed in the courseware.  Useful for all tag types.

`format`
  Subheading under display name -- currently only displayed for chapter sub-sections.  Also used by the the grader to know how to process students assessments that the section contains. New formats can be defined as a 'type' in the GRADER variable in course_settings.json. Optional.  (TODO: double check this--what's the current behavior?)

`hide_from_toc`
  If set to true for a chapter or chapter subsection, will hide that element from the courseware navigation accordion.  This is useful if you'd like to link to the content directly instead (e.g. for tutorials)

`ispublic`
  Specify whether the course is public.  You should be able to use start dates instead (?)

Inherited
---------

`start`
  When this content should be shown to students.  Note that anyone with staff access to the course will always see everything.

`showanswer`
  When to show answer. Values: never, attempted, answered, closed, finished, correct_or_past_due, past_due, always. Default: closed. Optional.
    - `never`: never show answer
    - `attempted`: show answer after first attempt
    - `answered` : this is slightly different from `attempted` -- resetting the problems makes "done" False, but leaves attempts unchanged.
    - `closed` : show answer after problem is closed, ie due date is past, or maximum attempts exceeded.
    - `finished` : show answer after problem closed, or is correctly answered.
    - `past_due` : show answer after problem due date is past.
    - `correct_or_past_due` : like `past_due`, but also allow solution to be seen immediately if the problem is correctly answered.
    - `always` : always allow answer to be shown.

`graded`
  Whether this section will count towards the students grade. "true" or "false". Defaults to "false".

`rerandomize`
  Randomize question on each attempt. Optional. Possible values:
  
  `always` (default)
    Students see a different version of the problem after each attempt to solve it.
  `onreset`
    Randomize question when reset button is pressed by the student.
  `never`
    All students see the same version of the problem.
  `per_student`
    Individual students see the same version of the problem each time the look at it, but that version is different from what other students see.
  `due`
    Due date for assignment. Assignment will be closed after that.  Values: valid date. Default: none. Optional.
  `attempts`
    Number of allowed attempts. Values: integer. Default: infinite. Optional.
  `graceperiod`
    A default length of time that the problem is still accessible after the due date in the format `"2 days 3 hours"` or `"1 day 15 minutes"`.  Note, graceperiods are currently the easiest way to handle time zones. Due dates are all expressed in UTC.
  `xqa_key`
    For integration with Ike's content QA server. -- should typically be specified at the course level.

Inheritance example
-------------------
This is a sketch ("tue" is not a valid start date), that should help illustrate how metadata inheritance works.

  .. code-block:: xml

    <course start="tue">
      <chap1> -- start tue
        <problem>   --- start tue
      </chap1>
      <chap2 start="wed">  -- start wed
       <problem2 start="thu">  -- start thu
       <problem3>      -- start wed
      </chap2>
    </course>


Specifying metadata in the XML file
-----------------------------------
Metadata can also live in the xml files, but anything defined in the policy file overrides anything in the XML.  This is primarily for backwards compatibility, and you should probably  not use both.  If you do leave some metadata tags in the xml, you should be consistent (e.g. if `display_name` stays in XML, they should all stay in XML. Note `display_name` should be specified in the problem xml definition itself, ie, `<problem display_name="Title">Problem Text</problem>`, in file `ProblemFoo.xml`).

.. note::
   Some xml attributes are not metadata.  e.g. in `<video youtube="xyz987293487293847"/>`, the `youtube` attribute specifies what video this is, and is logically part of the content, not the policy, so it should stay in the xml.

Another example policy file::

    {
        "course/2012": {
            "graceperiod": "1 day",
            "start": "2012-10-15T12:00",
            "display_name": "Introduction to Computer Science I",
            "xqa_key": "z1y4vdYcy0izkoPeihtPClDxmbY1ogDK"
        },
        "chapter/Week_0": {
            "display_name": "Week 0"
        },
        "sequential/Pre-Course_Survey": {
            "display_name": "Pre-Course Survey",
            "format": "Survey"
        }
    }



Deprecated Formats
------------------
If you look at some older xml, you may see some tags or metadata attributes that aren't listed above.  They are deprecated, and should not be used in new content.  We include them here so that you can understand how old-format content works.

Obsolete Tags
^^^^^^^^^^^^^
`section`
  This used to be necessary within chapters.  Now, you can just use any standard tag inside a chapter, so use the container tag that makes the most sense for grouping content--e.g. `problemset`, `videosequence`, and just include content directly if it belongs inside a chapter (e.g. `html`, `video`, `problem`)

`videodev, book, slides, image, discuss`
  There used to be special purpose tags that all basically did the same thing, and have been subsumed by `customtag`.  The list is `videodev, book, slides, image, discuss`.  Use `customtag` in new content.  (e.g. instead of `<book page="12"/>`, use `<customtag impl="book" page="12"/>`)

Obsolete Attributes
^^^^^^^^^^^^^^^^^^^
`slug`
  Old term for `url_name`.  Use `url_name`

`name`
  We didn't originally have a distinction between `url_name` and `display_name` -- this made content element ids fragile, so please use `url_name` as a stable unique identifier for the content, and `display_name` as the particular string you'd like to display for it.

************
Static links
************
If your content links (e.g. in an html file)  to `"static/blah/ponies.jpg"`, we will look for this...

* If your course dir has a `static/` subdirectory, we will look in `YOUR_COURSE_DIR/static/blah/ponies.jpg`.   This is the prefered organization, as it does not expose anything except what's in `static/` to the world.
*  If your course dir does not have a `static/` subdirectory, we will look in `YOUR_COURSE_DIR/blah/ponies.jpg`.  This is the old organization, and requires that the web server allow access to everything in the couse dir.  To switch to the new organization, move all your static content into a new `static/` dir  (e.g. if you currently have things in `images/`, `css/`, and `special/`, create a dir called `static/`, and move `images/, css/, and special/` there).

Links that include `/course` will be rewritten to the root of your course in the courseware (e.g. `courses/{org}/{course}/{url_name}/` in the current url structure).  This is useful for linking to the course wiki, for example.

****
Tabs
****

If you want to customize the courseware tabs displayed for your course, specify a "tabs" list in the course-level policy, like the following example:

.. code-block:: json

  "tabs" : [
    {"type": "courseware"},
    {
      "type": "course_info",
      "name": "Course Info"
    },
    {
      "type": "external_link",
      "name": "My Discussion",
      "link": "http://www.mydiscussion.org/blah"
    },
    {"type": "progress", "name": "Progress"},
    {"type": "wiki", "name": "Wonderwiki"},
    {
      "type": "static_tab",
      "url_slug": "news",
      "name": "Exciting news"
    },
    {"type": "textbooks"},
    {"type": "html_textbooks"},
    {"type": "pdf_textbooks"}
  ]

* If you specify any tabs, you must specify all tabs.  They will appear in the order given.
* The first two tabs must have types `"courseware"` and `"course_info"`, in that order, or the course will not load.
* The `courseware` tab never has a name attribute -- it's always rendered as "Courseware" for consistency between courses.
* The `textbooks` tab will actually generate one tab per textbook, using the textbook titles as names.
* The `html_textbooks` tab will actually generate one tab per html_textbook.  The tab name is found in the html textbook definition.
* The `pdf_textbooks` tab will actually generate one tab per pdf_textbook.  The tab name is found in the pdf textbook definition.
* For static tabs, the `url_slug` will be the url that points to the tab.  It can not be one of the existing courseware url types (even if those aren't used in your course).  The static content will come from `tabs/{course_url_name}/{url_slug}.html`, or `tabs/{url_slug}.html` if that doesn't exist.
* An Instructor tab will be automatically added at the end for course staff users.

.. list-table:: Supported Tabs and Parameters
   :widths: 10 80
   :header-rows: 0

   * - `courseware`
     - No other parameters.
   * - `course_info`
     - Parameter `name`.
   * - `wiki`
     - Parameter `name`.
   * - `discussion`
     - Parameter `name`.
   * - `external_link`
     - Parameters `name`, `link`.
   * - `textbooks`
     - No parameters--generates tab names from book titles.
   * - `html_textbooks`
     - No parameters--generates tab names from html book definition.  (See discussion below for configuration.)
   * - `pdf_textbooks`
     - No parameters--generates tab names from pdf book definition.  (See discussion below for configuration.)
   * - `progress`
     - Parameter `name`.
   * - `static_tab`
     - Parameters `name`, `url_slug`--will look for tab contents in 'tabs/{course_url_name}/{tab url_slug}.html'
   * - `staff_grading`
     - No parameters.  If specified, displays the staff grading tab for instructors.

*********
Textbooks
*********
Support is currently provided for image-based, HTML-based and PDF-based textbooks. In addition to enabling the display of textbooks in tabs (see above), specific information about the location of textbook content must be configured.  

Image-based Textbooks
=====================

Configuration
-------------

Image-based textbooks are configured at the course level in the XML markup.  Here is an example:  

.. code-block:: xml

  <course>
    <textbook title="Textbook 1" book_url="https://www.example.com/textbook_1/" />
    <textbook title="Textbook 2" book_url="https://www.example.com/textbook_2/" />
    <chapter url_name="Overview">
    <chapter url_name="First week">
  </course>


Each `textbook` element is displayed on a different tab.  The `title` attribute is used as the tab's name, and the `book_url` attribute points to the remote directory that contains the images of the text.  Note the trailing slash on the end of the `book_url` attribute.

The images must be stored in the same directory as the `book_url`, with filenames matching `pXXX.png`, where `XXX` is a three-digit number representing the page number (with leading zeroes as necessary).  Pages start at `p001.png`.

Each textbook must also have its own table of contents.  This is read from the `book_url` location, by appending `toc.xml`.  This file contains a `table_of_contents` parent element, with `entry` elements nested below it.  Each `entry`  has attributes for `name`, `page_label`, and `page`, as well as an optional `chapter` attribute.  An arbitrary number of levels of nesting of `entry` elements within other `entry` elements is supported, but you're likely to only want two levels.  The `page` represents the actual page to link to, while the `page_label` matches the displayed page number on that page.  Here's an example:

.. code-block:: xml

  <table_of_contents>
    <entry page="1" page_label="i" name="Title" />
    <entry page="2" page_label="ii" name="Preamble">
      <entry page="2" page_label="ii" name="Copyright"/>
      <entry page="3" page_label="iii" name="Brief Contents"/>
      <entry page="5" page_label="v" name="Contents"/>
      <entry page="9" page_label="1" name="About the Authors"/>
      <entry page="10" page_label="2" name="Acknowledgments"/>
      <entry page="11" page_label="3" name="Dedication"/>
      <entry page="12" page_label="4" name="Preface"/>
    </entry>
    <entry page="15" page_label="7" name="Introduction to edX" chapter="1">
      <entry page="15" page_label="7" name="edX in the Modern World"/>
      <entry page="18" page_label="10" name="The edX Method"/>
      <entry page="18" page_label="10" name="A Description of edX"/>
      <entry page="29" page_label="21" name="A Brief History of edX"/>
      <entry page="51" page_label="43" name="Introduction to edX"/>
      <entry page="56" page_label="48" name="Endnotes"/>
    </entry>
    <entry page="73" page_label="65" name="Art and Photo Credits" chapter="30">
      <entry page="73" page_label="65" name="Molecular Models"/>
      <entry page="73" page_label="65" name="Photo Credits"/>
    </entry>
    <entry page="77" page_label="69" name="Index" />
  </table_of_contents>


Linking from Content
--------------------

It is possible to add links to specific pages in a textbook by using a URL that encodes the index of the textbook and the page number.  The URL is of the form `/course/book/${bookindex}/$page}`.  If the page is omitted from the URL, the first page is assumed.

You can use a `customtag` to create a template for such links.  For example, you can create a `book` template in the `customtag` directory, containing:

.. code-block:: xml

  <img src="/static/images/icons/textbook_icon.png"/> More information given in <a href="/course/book/${book}/${page}">the text</a>. 

The course content can then link to page 25 using the `customtag` element:

.. code-block:: xml

  <customtag book="0" page="25" impl="book"/>


HTML-based Textbooks
====================

Configuration
-------------

HTML-based textbooks are configured at the course level in the policy file.  The JSON markup consists of an array of maps, with each map corresponding to a separate textbook.  There are two styles to presenting HTML-based material.  The first way is as a single HTML on a tab, which requires only a tab title and a URL for configuration.  A second way permits the display of multiple HTML files that should be displayed together on a single view. For this view, a side panel of links is available on the left, allowing selection of a particular HTML to view.  

.. code-block:: json

        "html_textbooks": [ 
          {"tab_title": "Textbook 1", 
	   "url": "https://www.example.com/thiscourse/book1/book1.html" },
          {"tab_title": "Textbook 2", 
	   "chapters": [
               { "title": "Chapter 1", "url": "https://www.example.com/thiscourse/book2/Chapter1.html" },
               { "title": "Chapter 2", "url": "https://www.example.com/thiscourse/book2/Chapter2.html" },
               { "title": "Chapter 3", "url": "https://www.example.com/thiscourse/book2/Chapter3.html" },
               { "title": "Chapter 4", "url": "https://www.example.com/thiscourse/book2/Chapter4.html" },
               { "title": "Chapter 5", "url": "https://www.example.com/thiscourse/book2/Chapter5.html" },
               { "title": "Chapter 6", "url": "https://www.example.com/thiscourse/book2/Chapter6.html" },
               { "title": "Chapter 7", "url": "https://www.example.com/thiscourse/book2/Chapter7.html" }
	       ]
	  }
        ]

Some notes:

* It is not a good idea to include a top-level URL and chapter-level URLs in the same textbook configuration.

Linking from Content
--------------------

It is possible to add links to specific pages in a textbook by using a URL that encodes the index of the textbook, the chapter (if chapters are used), and the page number.  For a book with no chapters, the URL is of the form `/course/htmlbook/${bookindex}`.  For a book with chapters, use `/course/htmlbook/${bookindex}/chapter/${chapter}` for a specific chapter, or `/course/htmlbook/${bookindex}` will default to the first chapter.   

For example, for the book with no chapters configured above, the textbook can be reached using the URL `/course/htmlbook/0`.  Reaching the third chapter of the second book is accomplished with `/course/htmlbook/1/chapter/3`.  

You can use a `customtag` to create a template for such links.  For example, you can create a `htmlbook` template in the `customtag` directory, containing:

.. code-block:: xml

  <img src="/static/images/icons/textbook_icon.png"/> More information given in <a href="/course/htmlbook/${book}">the text</a>. 

And a `htmlchapter` template containing:

.. code-block:: xml

  <img src="/static/images/icons/textbook_icon.png"/> More information given in <a href="/course/htmlbook/${book}/chapter/${chapter}">the text</a>. 

The example pages can then be linked using the `customtag` element:

.. code-block:: xml

  <customtag book="0" impl="htmlbook"/>
  <customtag book="1" chapter="3" impl="htmlchapter"/>

PDF-based Textbooks
===================

Configuration
-------------

PDF-based textbooks are configured at the course level in the policy file.  The JSON markup consists of an array of maps, with each map corresponding to a separate textbook.  There are two styles to presenting PDF-based material.  The first way is as a single PDF on a tab, which requires only a tab title and a URL for configuration.  A second way permits the display of multiple PDFs that should be displayed together on a single view. For this view, a side panel of links is available on the left, allowing selection of a particular PDF to view.  

.. code-block:: json

        "pdf_textbooks": [ 
          {"tab_title": "Textbook 1", 
	   "url": "https://www.example.com/thiscourse/book1/book1.pdf" },
          {"tab_title": "Textbook 2", 
	   "chapters": [
               { "title": "Chapter 1", "url": "https://www.example.com/thiscourse/book2/Chapter1.pdf" },
               { "title": "Chapter 2", "url": "https://www.example.com/thiscourse/book2/Chapter2.pdf" },
               { "title": "Chapter 3", "url": "https://www.example.com/thiscourse/book2/Chapter3.pdf" },
               { "title": "Chapter 4", "url": "https://www.example.com/thiscourse/book2/Chapter4.pdf" },
               { "title": "Chapter 5", "url": "https://www.example.com/thiscourse/book2/Chapter5.pdf" },
               { "title": "Chapter 6", "url": "https://www.example.com/thiscourse/book2/Chapter6.pdf" },
               { "title": "Chapter 7", "url": "https://www.example.com/thiscourse/book2/Chapter7.pdf" }
	       ]
	  }
        ]

Some notes:

* It is not a good idea to include a top-level URL and chapter-level URLs in the same textbook configuration.

Linking from Content
--------------------

It is possible to add links to specific pages in a textbook by using a URL that encodes the index of the textbook, the chapter (if chapters are used), and the page number.  For a book with no chapters, the URL is of the form `/course/pdfbook/${bookindex}/$page}`.  For a book with chapters, use `/course/pdfbook/${bookindex}/chapter/${chapter}/${page}`.  If the page is omitted from the URL, the first page is assumed.

For example, for the book with no chapters configured above, page 25 can be reached using the URL `/course/pdfbook/0/25`.  Reaching page 19 in the third chapter of the second book is accomplished with `/course/pdfbook/1/chapter/3/19`.  

You can use a `customtag` to create a template for such links.  For example, you can create a `pdfbook` template in the `customtag` directory, containing:

.. code-block:: xml

  <img src="/static/images/icons/textbook_icon.png"/> More information given in <a href="/course/pdfbook/${book}/${page}">the text</a>. 

And a `pdfchapter` template containing:

.. code-block:: xml

  <img src="/static/images/icons/textbook_icon.png"/> More information given in <a href="/course/pdfbook/${book}/chapter/${chapter}/${page}">the text</a>. 

The example pages can then be linked using the `customtag` element:

.. code-block:: xml

  <customtag book="0" page="25" impl="pdfbook"/>
  <customtag book="1" chapter="3" page="19" impl="pdfchapter"/>


*************************************
Other file locations (info and about)
*************************************
With different course runs, we may want different course info and about materials.  This is now supported by putting files in as follows::

    / 
      about/
           foo.html      -- shared default for all runs
           url_name1/
                foo.html   -- version used for url_name1
                bar.html   -- bar for url_name1
           url_name2/
                bar.html   -- bar for url_name2
                           -- url_name2 will use default foo.html

and the same works for the `info` directory.


***************************
Tips for content developers
***************************

#. We will be making better tools for managing policy files soon.  In the meantime, you can add dummy definitions to make it easier to search and separate the file visually.  For example, you could add `"WEEK 1" : "###################"`, before the week 1 material to make it easy to find in the file.

#. Come up with a consistent pattern for url_names, so that it's easy to know where to look for any piece of content.  It will also help to come up with a standard way of splitting your content files.  As a point of departure, we suggest splitting chapters, sequences, html, and problems into separate files.

#. Prefer the most "semantic" name for containers: e.g., use problemset rather than sequential for a problem set. That way, if we decide to display problem sets differently, we don't have to change the XML.


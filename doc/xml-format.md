# edX xml format tutorial

## Goals of this document

*	This was written assuming the reader has no prior programming/CS knowledge and has jumped cold turkey into the edX platform.
*	To educate the reader on how to build and maintain the back end structure of the course content. This is important for debugging and standardization.
*	After reading this, you should be able to add content to a course and make sure it shows up in the courseware and does not break the code.
* __Prerequisites:__ it would be helpful to know a little bit about xml.  Here is a [simple example](http://www.ultraslavonic.info/intro-to-xml/) if you've never seen it before.

## Outline

*	First, we will show a sample course structure as a case study/model of how xml and files in a course are organized to introductory understanding.

*	More technical details are below, including discussion of some special cases.


## Introduction

*	The course is organized hierarchically.  We start by describing course-wide parameters, then break the course into chapters, and then go deeper and deeper until we reach a specific pset, video, etc.

*	You could make an analogy to finding a green shirt in your house - front door -> bedroom -> closet -> drawer -> shirts -> green shirt


## Case Study

Let's jump right in by looking at the directory structure of a very simple toy course:

    toy/
        course
        course.xml
        problem
        policies
        roots

The only top level file is `course.xml`, which should contain one line, looking something like this:

    <course org="edX" course="toy" url_name="2012_Fall"/>

This gives all the information to uniquely identify a particular run of any course--which organization is producing the course, what the course name is, and what "run" this is, specified via the `url_name` attribute.

Obviously, this doesn't actually specify any of the course content, so we need to find that next.  To know where to look, you need to know the standard organizational structure of our system: _course elements are uniquely identified by the combination `(category, url_name)`_.  In this case, we are looking for a `course` element with the `url_name` "2012_Fall".  The definition of this element will be in `course/2012_Fall.xml`.  Let's look there next:

`course/2012_Fall.xml`

    <course>
      <chapter url_name="Overview">
        <videosequence url_name="Toy_Videos">
          <problem url_name="warmup"/>
          <video url_name="Video_Resources" youtube="1.0:1bK-WdDi6Qw"/>
        </videosequence>
        <video url_name="Welcome" youtube="1.0:p2Q6BrNhdh8"/>
      </chapter>
    </course>

Aha.  Now we found some content.  We can see that the course is organized hierarchically, in this case with only one chapter, with `url_name` "Overview".   The chapter contains a `videosequence` and a `video`, with the sequence containing a problem and another video.  When viewed in the courseware, chapters are shown at the top level of the navigation accordion on the left, with any elements directly included in the chapter below.

Looking at this file, we can see the course structure, and the youtube urls for the videos, but what about the "warmup" problem?  There is no problem content here!    Where should we look?  This is a good time to pause and try to answer that question based on our organizational structure above.

As you hopefully guessed, the problem would be in `problem/warmup.xml`.  (Note: This tutorial doesn't discuss the xml format for problems--there are chapters of edx4edx that describe it.)  This is an instance of a _pointer tag:_ any xml tag with only the category and a url_name attribute will point to the file `{category}/{url_name}.xml`.  For example, this means that our toy `course.xml` could have also been written as

`course/2012_Fall.xml`

    <course>
      <chapter url_name="Overview"/>
    </course>

with `chapter/Overview.xml` containing

    <chapter>
        <videosequence url_name="Toy_Videos">
          <problem url_name="warmup"/>
          <video url_name="Video_Resources" youtube="1.0:1bK-WdDi6Qw"/>
        </videosequence>
        <video url_name="Welcome" youtube="1.0:p2Q6BrNhdh8"/>
    </chapter>

In fact, this is the recommended structure for real courses--putting each chapter into its own file makes it easy to have different people work on each without conflicting or having to merge.  Similarly, as sequences get large, it can be handy to split them out as well (in `sequence/{url_name}.xml`, of course).

Note that the `url_name` is only specified once per element--either the inline definition, or in the pointer tag.

## Policy files

We still haven't looked at two of the directoies in the top-level listing above: `policies` and `roots`.  Let's look at policies next.  The policy directory contains one file:

    policies:
        2012_Fall.json

and that file is named {course-url_name}.json.  As you might expect, this file contains a policy for the course.  In our example, it looks like this:

    2012_Fall.json:
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

The policy specifies metadata about the content elements--things which are not inherent to the definition of the content, but which describe how the content is presented to the user and used in the course.  See below for a full list of metadata attributes; as the example shows, they include `display_name`, which is what is shown when this piece of content is referenced or shown in the courseware, and various dates and times, like `start`, which specifies when the content becomes visible to students, and various problem-specific parameters like the allowed number of attempts.  One important point is that some metadata is inherited: for example, specifying the start date on the course makes it the default for every element in the course.  See below for more details.

It is possible to put metadata directly in the xml, as attributes of the appropriate tag, but using a policy file has two benefits: it puts all the policy in one place, making it easier to check that things like due dates are set properly, and it allows the content definitions to be easily used in another run of the same course, with the same or similar content, but different policy.

## Roots

The last directory in the top level listing is `roots`.  In our toy course, it contains a single file:

    roots/
        2012_Fall.xml

This file is identical to the top-level `course.xml`, containing

    <course org="edX" course="toy" url_name="2012_Fall"/>

In fact, the top level `course.xml` is a symbolic link to this file.  When there is only one run of a course, the roots directory is not really necessary, and the top-level course.xml file can just specify the `url_name` of the course.  However, if we wanted to make a second run of our toy course, we could add another file called, e.g., `roots/2013_Spring.xml`, containing

    <course org="edX" course="toy" url_name="2013_Spring"/>

After creating `course/2013_Spring.xml` with the course structure (possibly as a symbolic link or copy of `course/2012_Fall.xml` if no content was changing), and `policies/2013_Spring.json`, we would have two different runs of the toy course in the course repository.  Our build system understands this roots structure, and will build a course package for each root.  (Dev note: if you're using a local development environment, make the top level `course.xml` point to the desired root, and check out the repo multiple times if you need multiple runs simultaneously).

That's basically all there is to the organizational structure.  Read the next section for details on the tags we support, including some special case tags like `customtag` and `html` invariants, and look at the end for some tips that will make the editing process easier.

----------

# Tag types

* `abtest` -- Support for A/B testing.  TODO: add details..
* `chapter` -- top level organization unit of a course.   The courseware display code currently expects the top level `course` element to contain only chapters, though there is no philosophical reason why this is required, so we may change it to properly display non-chapters at the top level.
* `course` -- top level tag.  Contains everything else.
* `customtag` -- render an html template, filling in some parameters, and return the resulting html.  See below for details.
* `html` -- a reference to an html file.
* `error`  -- don't put these in by hand :)   The internal representation of content that has an error, such as malformed xml or some broken invariant.  You may see this in the xml once the CMS is in use...
* `problem` -- a problem.  See elsewhere in edx4edx for documentation on the format.
* `problemset` -- logically, a series of related problems.  Currently displayed vertically.  May contain explanatory html, videos, etc.
* `sequential` -- a sequence of content, currently displayed with a horizontal list of tabs.  If possible, use a more semantically meaningful tag (currently, we only have `videosequence`).
* `vertical` -- a sequence of content, displayed vertically.  Content will be accessed all at once, on the right part of the page. No navigational bar. May have to use browser scroll bars. Content split with separators.   If possible, use a more semantically meaningful tag (currently, we only have `problemset`).
* `video`  -- a link to a video, currently expected to be hosted on youtube.
* `videosequence` -- a sequence of videos.  This can contain various non-video content; it just signals to the system that this is logically part of an explanatory sequence of content, as opposed to say an exam sequence.

## Tag details

### Container tags

Container tags include `chapter`, `sequential`, `videosequence`, `vertical`, and `problemset`.  They are all specified in the same way in the xml, as shown in the tutorial above.

### `course`

`course` is also a container, and is similar, with one extra wrinkle: the top level pointer tag _must_ have  `org` and `course` attributes specified--the organization name, and course name.  Note that `course` is referring to the platonic ideal of this course (e.g. "6.002x"), not to any particular run of this course.  The `url_name` should be the particular run of this course.

### `customtag`

When we see `<customtag impl="special" animal="unicorn" hat="blue"/>`, we will:

* look for a file called `custom_tags/special`  in your course dir.
* render it as a mako template, passing parameters {'animal':'unicorn', 'hat':'blue'}, generating html.  (Google `mako` for template syntax, or look at existing examples).

Since `customtag` is already a pointer, there is generally no need to put it into a separate file--just use it in place: <customtag url_name="my_custom_tag" impl="blah" attr1="..."/>


### `html`

Most of our content is in xml, but some html content may not be proper xml (all tags matched, single top-level tag, etc), since browsers are fairly lenient in what they'll display.  So, there are two ways to include html content:

* If your html content is in a proper xml format, just put it in `html/{url_name}.xml`.
* If your html content is not in proper xml format, you can put it in `html/{filename}.html`, and put `<html filename={filename} />` in `html/{filename}.xml`.  This allows another level of indirection, and makes sure that we can read the xml file and then just return the actual html content without trying to parse it.

### `video`

Videos have an attribute youtube, which specifies a series of speeds + youtube videos id:

    <video youtube="0.75:1yk1A8-FPbw,1.0:vNMrbPvwhU4,1.25:gBW_wqe7rDc,1.50:7AE_TKgaBwA" url_name="S15V14_Response_to_impulse_limit_case"/>

This video has been encoded at 4 different speeds: 0.75x, 1x, 1.25x, and 1.5x.

## More on `url_name`s

Every content element (within a course) should have a unique id.  This id is formed as `{category}/{url_name}`, or automatically generated from the content if `url_name` is not specified.  Categories are the different tag types ('chapter', 'problem', 'html', 'sequential', etc).  Url_name is a string containing a-z, A-Z, dot (.), underscore (_), and ':'.  This is what appears in urls that point to this object.

Colon (':') is special--when looking for the content definition in an xml, ':' will be replaced with '/'.  This allows organizing content into folders.  For example, given the pointer tag

    <problem url_name="conceptual:add_apples_and_oranges"/>

we would look for the problem definition in `problem/conceptual/add_apples_and_oranges.xml`.   (There is a technical reason why we can't just allow '/' in the url_name directly.)

__IMPORTANT__: A student's state for a particular content element is tied to the element id, so the automatic id generation if only ok for elements that do not need to store any student state (e.g. verticals or customtags).  For problems, sequentials, and videos, and any other element where we keep track of what the student has done and where they are at, you should specify a unique `url_name`.  Of course, any content element that is split out into a file will need a `url_name` to specify where to find the definition.  When the CMS comes online, it will use these ids to enable content reuse, so if there is a logical name for something, please do specify it.

-----

## Policy files

*	A policy file is useful when running different versions of a course e.g. internal, external, fall, spring, etc. as you can change due dates, etc, by creating multiple policy files.
*	A policy file provides information on the metadata of the course--things that are not inherent to the definitions of the contents, but that may vary from run to run.
* Note: We will be expanding our understanding and format for metadata in the not-too-distant future, but for now it is simply a set of key-value pairs.

### Policy file location
* The policy for a course run `some_url_name` should live in `policies/some_url_name/policy.json`  (NOTE: the old format of putting it in `policies/some_url_name.json` will also work, but we suggest using the subdirectory because that's allows you to organize all the per-course policy files)
* Grading policy files go in `policies/some_url_name/grading_policy.json`   (if there's only one course run, can also put it directly in the course root: `/grading_policy.json`)

### Policy file contents
* The file format is "json", and is best shown by example, as in the tutorial above (though also feel free to google :)
* The expected contents are a dictionary mapping from keys to values (syntax "{ key : value, key2 : value2, etc}")
* Keys are in the form "{category}/{url_name}", which should uniquely identify a content element.
Values are dictionaries of the form {"metadata-key" : "metadata-value"}.
* The order in which things appear does not matter, though it may be helpful to organize the file in the same order as things appear in the content.
* NOTE: json is picky about commas.  If you have trailing commas before closing braces, it will complain and refuse to parse the file.  This can be irritating at first.

### Grading policy file contents

TODO: This needs to be improved, but for now here's a sketch of how grading works:


* First we grade on individual problems. Correct and total are methods on CapaProblem.

    `problem_score = (correct ,  total)`

* If a problem weight is in the xml, then re-weight the problem to be worth that many points

    `if problem_weight:`
         `problem_score = (correct * weight / total, weight)`

* Now sum up all of problems in a section to get the percent for that section

    `section_percent = \sum_problems_correct /   \sum_problems_total`

* Now we have all of the percents for all of the graded sections. This is the gradesheet that we pass to to a subclass of CourseGrader.

* A WeightedSubsectionsGrader contains several SingleSectionGraders and AssignmentFormatGraders. Each of those graders is run first before WeightedSubsectionsGrader computes the final grade.

    - SingleSectionGrader (within a WeightedSubsectionsGrader) contains one section

    `grader_percent = section_percent`

    - AssignmentFormatGrader (within a WegithedSubsectionsGrader) contains multiple sections matching a certain format
drop the lowest X sections

    `grader_percent = \sum_section_percent  /  \count_section`

    - WeightedSubsectionsGrader

    `final_grade_percent = \sum_(grader_percent * grader_weight)`

* Round the final grade up to the nearest percentage point

    `final_grade_percent = round(final_grade_percent * 100 + 0.05) / 100`

### Available metadata

__Not inherited:__

* `display_name` - name that will appear when this content is displayed in the courseware.  Useful for all tag types.
*	`format` - subheading under display name -- currently only displayed for chapter sub-sections.  Also used by the the grader to know how to process students assessments that the
    section contains. New formats can be defined as a 'type' in the GRADER variable in course_settings.json. Optional.  (TODO: double check this--what's the current behavior?)
* `hide_from_toc` -- If set to true for a chapter or chapter subsection, will hide that element from the courseware navigation accordion.  This is useful if you'd like to link to the content directly instead (e.g. for tutorials)
* `ispublic` -- specify whether the course is public.  You should be able to use start dates instead (?)

__Inherited:__

* `start` -- when this content should be shown to students.  Note that anyone with staff access to the course will always see everything.
*	`showanswer` - When to show answer. For 'attempted', will show answer after first attempt. Values: never, attempted, answered, closed. Default: closed. Optional.
*	`graded` - Whether this section will count towards the students grade. "true" or "false". Defaults to "false".
*	`rerandomise` - Randomize question on each attempt. Values: 'always' (students see a different version of the problem after each attempt to solve it)
                                                            'never' (all students see the same version of the problem)
                                                            'per_student' (individual students see the same version of the problem each time the look at it, but that version is different from what other students see)
                                                            Default: 'always'. Optional.
*	`due` - Due date for assignment. Assignment will be closed after that.  Values: valid date. Default: none. Optional.
* attempts: Number of allowed attempts. Values: integer. Default: infinite. Optional.
* `graceperiod` - A default length of time that the problem is still accessible after the due date in the format "2 days 3 hours" or "1 day 15 minutes".  Note, graceperiods are currently the easiest way to handle time zones. Due dates are all expressed in UCT.
* `xqa_key` -- for integration with Ike's content QA server. -- should typically be specified at the course level.

__Inheritance example:__

This is a sketch ("tue" is not a valid start date), that should help illustrate how metadata inheritance works.

    <course start="tue">
      <chap1> -- start tue
        <problem>   --- start tue
      </chap1>
      <chap2 start="wed">  -- start wed
       <problem2 start="thu">  -- start thu
       <problem3>      -- start wed
      </chap2>
    </course>


## Specifying metadata in the xml file

Metadata can also live in the xml files, but anything defined in the policy file overrides anything in the xml.  This is primarily for backwards compatibility, and you should probably  not use both.  If you do leave some metadata tags in the xml, you should be consistent (e.g. if `display_name`s stay in xml, they should all stay in xml).
   - note, some xml attributes are not metadata.  e.g. in `<video youtube="xyz987293487293847"/>`, the `youtube` attribute specifies what video this is, and is logically part of the content, not the policy, so it should stay in the xml.

Another example policy file:

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



## Deprecated formats

If you look at some older xml, you may see some tags or metadata attributes that aren't listed above.  They are deprecated, and should not be used in new content.  We include them here so that you can understand how old-format content works.

### Obsolete tags:

* `section` : this used to be necessary within chapters.  Now, you can just use any standard tag inside a chapter, so use the container tag that makes the most sense for grouping content--e.g. `problemset`, `videosequence`, and just include content directly if it belongs inside a chapter (e.g. `html`, `video`, `problem`)

* There used to be special purpose tags that all basically did the same thing, and have been subsumed by `customtag`.  The list is `videodev, book, slides, image, discuss`.  Use `customtag` in new content.  (e.g. instead of `<book page="12"/>`, use `<customtag impl="book" page="12"/>`)

### Obsolete attributes

* `slug` -- old term for `url_name`.  Use `url_name`
* `name` -- we didn't originally have a distinction between `url_name` and `display_name` -- this made content element ids fragile, so please use `url_name` as a stable unique identifier for the content, and `display_name` as the particular string you'd like to display for it.


# Static links

if your content links (e.g. in an html file)  to `"static/blah/ponies.jpg"`, we will look for this in `YOUR_COURSE_DIR/blah/ponies.jpg`.  Note that this is not looking in a `static/` subfolder in your course dir.  This may (should?) change at some point.   Links that include `/course` will be rewritten to the root of your course in the courseware (e.g. `courses/{org}/{course}/{url_name}/` in the current url structure).  This is useful for linking to the course wiki, for example.

# Tips for content developers

* We will be making better tools for managing policy files soon.  In the meantime, you can add dummy definitions to make it easier to search and separate the file visually.  For example, you could add:

    "WEEK 1" : "##################################################",

before the week 1 material to make it easy to find in the file.

* Come up with a consistent pattern for url_names, so that it's easy to know where to look for any piece of content.  It will also help to come up with a standard way of splitting your content files.  As a point of departure, we suggest splitting chapters, sequences, html, and problems into separate files.

* A heads up: our content management system will allow you to develop content through a web browser, but will be backed by this same xml at first.  Once that happens, every element will be in its own file to make access and updates faster.

* Prefer the most "semantic" name for containers: e.g., use problemset rather than vertical for a problem set.  That way, if we decide to display problem sets differently, we don't have to change the xml.

# Other file locations (info and about)

With different course runs, we may want different course info and about materials.  This is now supported by putting files in as follows:

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

----

(Dev note: This file is generated from the mitx repo, in `doc/xml-format.md`.  Please make edits there.)

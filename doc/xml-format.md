This doc is a rough spec of our xml format

Every content element (within a course) should have a unique id.  This id is formed as {category}/{url_name}.  Categories are the different tag types ('chapter', 'problem', 'html', 'sequential', etc).  Url_name is a string containing a-z, A-Z, dot (.) and _.  This is what appears in urls that point to this object.

File layout:

- Xml files have content
- "policy", which is also called metadata in various places, should live in a policy file.

- each module (except customtag and course, which are special, see below) should live in a file, located at {category}/{url_name].xml
To include this module in another one (e.g. to put a problem in a vertical), put in a "pointer tag":  <{category} url_name="{url_name}"/>.  When we read that, we'll load the actual contents.

Customtag is already a pointer, you can just use it in place: <customtag url_name="my_custom_tag" impl="blah" attr1="..."/>

Course tags:
  - the top level course pointer tag lives in course.xml
  - have 2 extra required attributes: "org" and "course" -- organization name, and course name.  Note that the course name is referring to the platonic ideal of this course, not to any particular run of this course.  The url_name should be particular run of this course.  E.g.

If course.xml contains:
<course org="HarvardX" course="cs50" url_name="2012"/>

we would load the actual course definition from course/2012.xml

To support multiple different runs of the course, you could have a different course.xml, containing

<course org="HarvardX" course="cs50" url_name="2012H"/>

which would load the Harvard-internal version from course/2012H.xml

If there is only one run of the course for now, just have a single course.xml with the right url_name.

If there is more than one run of the course, the different course root pointer files should live in
roots/url_name.xml, and course.xml should be a symbolic link to the one you want to run in your dev instance.

If you want to run both versions, you need to checkout the repo twice, and have course.xml point to different root/{url_name}.xml files.

Policies:
 - the policy for a course url_name lives in policies/{url_name}.json

The format is called "json", and is best shown by example (though also feel free to google :)

the file is a dictionary (mapping from keys to values, syntax "{ key : value, key2 : value2, etc}"

Keys are in the form "{category}/{url_name}", which should uniquely id a content element.
Values are dictionaries of the form {"metadata-key" : "metadata-value"}.

metadata can also live in the xml files, but anything defined in the policy file overrides anything in the xml.  This is primarily for backwards compatibility, and you should probably  not use both.  If you do leave some metadata tags in the xml, please be consistent (e.g. if display_names stay in xml, they should all stay in xml).
   - note, some xml attributes are not metadata.  e.g. in <video youtube="xyz987293487293847"/>, the youtube attribute specifies what video this is, and is logically part of the content, not the policy, so it should stay in video/{url_name}.xml.

Example policy file:
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

NOTE: json is picky about commas.  If you have trailing commas before closing braces, it will complain and refuse to parse the file.  This is irritating.


Valid tag categories:

abtest
chapter
course
customtag
html
error  -- don't put these in by hand :)
problem
problemset
sequential
vertical
video
videosequence

Obsolete tags:
Use customtag instead:
  videodev
  book
  slides
  image
  discuss

Ex: instead of <book page="12"/>, use <customtag impl="book" page="12"/>

Use something semantic instead, as makes sense: sequential, vertical, videosequence if it's actually a sequence.  If the section would only contain a single element, just include that element directly.
  section

In general, prefer the most "semantic" name for containers: e.g. use problemset rather than vertical for a problem set.  That way, if we decide to display problem sets differently, we don't have to change the xml.

How customtags work:
 When we see <customtag impl="special" animal="unicorn" hat="blue"/>, we will:

 - look for a file called custom_tags/special  in your course dir.
 - render it as a mako template, passing parameters {'animal':'unicorn', 'hat':'blue'}, generating html.


METADATA

Metadata that we generally understand:
Only on course tag in courses/url_name.xml
  ispublic
  xqa_key  -- set only on course, inherited to everything else

Everything:
  display_name
  format   (maybe only content containers, e.g. "Lecture sequence", "problem set", "lab", etc. )
  start  -- modules will not show up to non-course-staff users before the start date (in production)
  hide_from_toc  -- if this is true, don't show in table of contents for the course.  Useful on chapters, and chapter subsections that are linked to from somewhere else.

Used for problems
graceperiod
showanswer
rerandomize
graded
due


These are _inherited_ : if specified on the course, will apply to everything in the course, except for things that explicitly specify them, and their children.
        'graded', 'start', 'due', 'graceperiod', 'showanswer', 'rerandomize',
        # TODO (ichuang): used for Fall 2012 xqa server access
        'xqa_key',

Example sketch:
<course start="tue">
  <chap1> -- start tue
    <problem>   --- start tue
  </chap1>
  <chap2 start="wed">  -- start wed
   <problem2 start="thu">  -- start thu
   <problem3>      -- start wed
  </chap2>
</course>


STATIC LINKS:

if your content links (e.g. in an html file)  to "static/blah/ponies.jpg", we will look for this in YOUR_COURSE_DIR/blah/ponies.jpg.  Note that this is not looking in a static/ subfolder in your course dir.  This may (should?) change at some point.

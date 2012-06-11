# Documentation for edX code (mitx repo)

This document explains the general structure of the edX platform, and defines some of the acronyms and terms you'll see flying around in the code.

## Assumptions:

You should be familiar with the following.  If you're not, go read some docs...

 - python
 - django
 - javascript
 - html, xml -- xpath, xslt
 - css
 - git
 - mako templates -- we use these instead of django templates, because they support embedding real python.
 
## Other relevant terms

 - CAPA -- lon-capa.org -- content management system that has defined a standard for online learning and assessment materials.  Many of our materials follow this standard.
    - TODO: add more details / link to relevant docs.  lon-capa.org is not immediately intuitive.  
    - lcp = loncapa problem


## Parts of the system

  - LMS -- Learning Management System.   The student-facing parts of the system.  Handles student accounts, displaying videos, tutorials, exercies, problems, etc. 

  - CMS -- Course Management System.  The instructor-facing parts of the system.  Allows instructors to see and modify their course, add lectures, problems, reorder things, etc.

  - Askbot -- the discussion forums.  We have a custom fork of this project.  We're also hoping to replace it with something better later.  (e.g. need support for multiple classes, etc)

  - Data.  In the data/ dir.  There is currently a single `course.xml` file that describes an entire course.  Speaking of which...

  - Courses.  A course is broken up into Chapters ("week 1", "week 2", etc).  A chapter is broken up into Sections ("Lecture 1", "Simple Circuits Exercises", "HW1", etc).  A section can contain modules: Problems, Html, Videos, Verticals, or Sequences.
     - Problems: specified in problem files.  May have python scripts embedded to both generate random parameters and check answers.  Also allows specifying things like tolerance or precision in answers
     - Html: any html - often description, or links to outside resources
     - Videos: links to youtube or elsewhere
     - Verticals: a nesting tag: collect several videos, problems, html modules and display them vertically.
     - Sequences: a sequence of modules, displayed with a horizontal navigation bar, displaying one component at a time.
     - see `data/course.xml` for more examples


## High Level Entities in the code

### Common libraries 

- x_modules -- generic learning modules. *x* can be sequence, video, template, html, vertical, capa, etc.  These are the things that one puts inside sections in the course structure.  Modules know how to render themselves to html, how to score themselves, and handle ajax calls from the front end. 
      - x_modules take a 'system' context parameter, which is a reference to an object that knows how to render things, track events, complain about 404s, etc.  (TODO: figure out, document the necessary interface--different in `x_module.XModule.__init__` and in `x_module tests.py`)
      - in `common/lib/xmodule`

- capa modules -- defines `LoncapaProblem` and many related things.  
    - in `common/lib/capa`

### LMS 

The LMS is a django site, with root in `lms/`.  It runs in many different environments--the settings files are in `lms/envs`. 

- We use the Django Auth system, including the is_staff and is_superuser flags.  User profiles and related code lives in `lms/djangoapps/student/`.   There is support for groups of students (e.g. 'want emails about future courses', 'have unenrolled', etc) in `lms/djangoapps/student/models.py`.

- `StudentModule` -- keeps track of where a particular student is in a module (problem, video, html)--what's their grade, have they started, are they done, etc.  [This is only partly implemented so far.]
    - `lms/djangoapps/courseware/models.py`

- Core rendering path:
  - `lms/urls.py` points to `courseware.views.index`, which gets module info from the course xml file, pulls list of `StudentModule` objects for this user (to avoid multiple db hits).  

  - Calls `render_accordion` to render the "accordion"--the display of the course structure.

  - To render the current module, calls `module_render.py:render_x_module()`, which gets the `StudentModule` instance, and passes the `StudentModule` state and other system context to the module constructor the get an instance of the appropriate module class for this user.

  - calls the module's `.get_html()` method.  If the module has nested submodules, render_x_module() will be called again for each.
  
  - ajax calls go to `module_render.py:modx_dispatch()`, which passes it to the module's `handle_ajax()` function, and then updates the grade and state if they changed.

- Tracking: there is support for basic tracking of client-side events in `lms/djangoapps/track`.  

### Other modules

- Wiki -- in `lms/djangoapps/simplewiki`.  Has some markdown extentions for embedding circuits, videos, etc.

## Testing

See `testing.md`.


## QUESTIONS:

`common/lib/capa` : what is eia, `eia.py`?   Random lists of numbers?

what is `lms/lib/dogfood`?  Looks like a way to test capa problems...  Is it being used?

is lms/envs/README.txt out of date?

## TODO:

- Only describes backend code so far.  How does the front-end work?

- What big pieces are missing?

- Where should reader go next?

---
Note: this file uses markdown.  To convert to html, run:

    markdown2 overview.md > overview.html

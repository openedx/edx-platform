# Documentation for edX code (edx-platform repo)

This document explains the general structure of the edX platform, and defines some of the acronyms and terms you'll see flying around in the code.

## Assumptions:

You should be familiar with the following.  If you're not, go read some docs...

 - [python](http://docs.python.org)
 - [django](http://docs.djangoproject.com)
 - javascript
 - html, xml -- xpath, xslt
 - css
 - [git](http://git-scm.com/documentation)
 - [mako templates](http://www.makotemplates.org/docs) -- we use these instead of django templates, because they support embedding real python.

## Other relevant terms

 - CAPA -- lon-capa.org -- content management system that has defined a standard for online learning and assessment materials.  Many of our materials follow this standard.
    - TODO: add more details / link to relevant docs.  lon-capa.org is not immediately intuitive.
    - lcp = loncapa problem


## Parts of the system

  - LMS -- Learning Management System.   The student-facing parts of the system.  Handles student accounts, displaying videos, tutorials, exercies, problems, etc.

  - CMS -- Course Management System.  The instructor-facing parts of the system.  Allows instructors to see and modify their course, add lectures, problems, reorder things, etc.

  - Forums -- this is a ruby on rails service that runs on Heroku.  Contributed by berkeley folks.  The LMS has a wrapper lib that talks to it.

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

- xmodule: generic learning modules. *x* can be sequence, video, template, html,
           vertical, capa, etc.  These are the things that one puts inside sections
           in the course structure.

    - XModuleDescriptor: This defines the problem and all data and UI needed to edit
           that problem. It is unaware of any student data, but can be used to retrieve
           an XModule, which is aware of that student state.

    - XModule: The XModule is a problem instance that is particular to a student. It knows
           how to render itself to html to display the problem, how to score itself,
           and how to handle ajax calls from the front end.

    - Both XModule and XModuleDescriptor take system context parameters. These are named
           ModuleSystem and DescriptorSystem respectively. These help isolate the XModules
           from any interactions with external resources that they require.

           For instance, the DescriptorSystem has a function to load an XModuleDescriptor
           from a Location object, and the ModuleSystem knows how to render things,
           track events, and complain about 404s

    - XModules and XModuleDescriptors are uniquely identified by a Location object, encoding the organization, course, category, name, and possibly revision of the module.

    - XModule initialization: XModules are instantiated by the `XModuleDescriptor.xmodule` method, and given a ModuleSystem, the descriptor which instantiated it, and their relevant model data.

    - XModuleDescriptor initialization: If an XModuleDescriptor is loaded from an XML-based course, the XML data is passed into its `from_xml` method, which is responsible for instantiating a descriptor with the correct attributes. If it's in Mongo, the descriptor is instantiated directly. The module's attributes will be present in the `model_data` dict.

    - `course.xml` format.  We use python setuptools to connect supported tags with the descriptors that handle them.  See `common/lib/xmodule/setup.py`.  There are checking and validation tools in `common/validate`.

         - the xml import+export functionality is in `xml_module.py:XmlDescriptor`, which is a mixin class that's used by the actual descriptor classes.

         - There is a distinction between descriptor _definitions_ that stay the same for any use of that descriptor (e.g. here is what a particular problem is), and _metadata_ describing how that descriptor is used (e.g. whether to allow checking of answers, due date, etc).  When reading in `from_xml`, the code pulls out the metadata attributes into a separate structure, and puts it back on export.

    - in `common/lib/xmodule`

- capa modules -- defines `LoncapaProblem` and many related things.
    - in `common/lib/capa`

### LMS

The LMS is a django site, with root in `lms/`.  It runs in many different environments--the settings files are in `lms/envs`.

- We use the Django Auth system, including the is_staff and is_superuser flags.  User profiles and related code lives in `lms/djangoapps/student/`.   There is support for groups of students (e.g. 'want emails about future courses', 'have unenrolled', etc) in `lms/djangoapps/student/models.py`.

- `StudentModule` -- keeps track of where a particular student is in a module (problem, video, html)--what's their grade, have they started, are they done, etc.  [This is only partly implemented so far.]
    - `lms/djangoapps/courseware/models.py`

- Core rendering path:
  - `lms/urls.py` points to `courseware.views.views.index`, which gets module info from the course xml file, pulls list of `StudentModule` objects for this user (to avoid multiple db hits).

  - Calls `render_accordion` to render the "accordion"--the display of the course structure.

  - To render the current module, calls `module_render.py:render_x_module()`, which gets the `StudentModule` instance, and passes the `StudentModule` state and other system context to the module constructor the get an instance of the appropriate module class for this user.

  - calls the module's `.get_html()` method.  If the module has nested submodules, render_x_module() will be called again for each.

  - ajax calls go to `module_render.py:handle_xblock_callback()`, which passes it to one of the `XBlock`s handler functions

- See `lms/urls.py` for the wirings of urls to views.

- Tracking: there is support for basic tracking of client-side events in `lms/djangoapps/track`.

### CMS

The CMS is a django site, with root in `cms`. It can run in a number of different
environments, defined in `cms/envs`.

- Core rendering path: Still TBD

### Static file processing

- CSS -- we use a superset of CSS called SASS.  It supports nice things like includes and variables, and compiles to CSS.  The compiler is called `sass`.

- javascript -- we use coffeescript, which compiles to js, and is much nicer to work with.  Look for `*.coffee` files.  We use _jasmine_ for testing js.

- _mako_  -- we use this for templates, and have wrapper called edxmako that makes mako look like the django templating calls.

We use a fork of django-pipeline to make sure that the js and css always reflect the latest `*.coffee` and `*.sass` files (We're hoping to get our changes merged in the official version soon).  This works differently in development and production.  Test uses the production settings.

In production, the django `collectstatic` command recompiles everything and puts all the generated static files in a static/ dir.  A starting point in the code is `django-pipeline/pipeline/packager.py:pack`.

In development, we don't use collectstatic, instead accessing the files in place.  The auto-compilation is run via `openedx/core/djangoapps/pipeline_mako/templates/static_content.html`.  Details: templates include `<%namespace name='static' file='static_content.html'/>`, then something like `<%static:css group='application'/>` to call the functions in `openedx/core/djangoapps/pipeline_mako/__init__.py`, which call the `django-pipeline` compilers.

## Testing

See `testing.rst`.

## TODO:

- describe our production environment

- describe the front-end architecture, tools, etc.  Starting point: `lms/static`

---
Note: this file uses markdown.  To convert to html, run:

    markdown2 overview.md > overview.html

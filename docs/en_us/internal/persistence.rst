


This document describes the split mongostore representation which
separates course structure from content where each course run can have
its own structure. It does not describe the original mongostore
representation which combined structure and content and used the key
to distinguish draft from published elements.

This document does not describe mongo nor its operations. See
`http://www.mongodb.org/`_ for information on Mongo.



Product Goals and Discussion
----------------------------

(Mark Chang)

This work was instigated by the studio team's need to correctly do
metadata inheritance. As we moved from an on-startup load of the
courseware, the system was able to inflate and perform an inheritance
calculation step such that the intended properties of children could
be set through inheritance. While not strictly a requirement from the
studio authoring approach, where inheritance really rears its head is
on import of existing courseware that was designed assuming
inheritance.

A short term patch was applied that allowed inheritance to act
correctly, but it was felt that it was insufficient and this would be
an opportunity to make a more clean datastore representation. After
much difficulty with how draft objects would work, Calen Pennington
worked through a split data store model ala FAT filesystem (Mark's
metaphor, not Cale's) to split the structure from the content. The
goal would be a sea of content documents that would not know about the
structure they were utilized within. Cale began the work and handed it
off to Don Mitchell.

In the interim, great discussion was had at the Architect's Council
that firmed up the design and strategy for implementation, adding
great richness and completeness to the new data structure.

The immediate
needs are two, and only two.


#. functioning metadata inheritance
#. good groundwork for versioning


While the discussions of the atomic unit of courseware available for
sharing, how these are shared, and how they refer back to the parent
definition are all valuable, they will not be built in the near term. I
understand and expect there to be many refactorings, improvements, and
migrations in the future. 

I fully anticipate much more detail to be uncovered even in this first
thin implementation. When that happens, we will need as much advice
from those watching this page to make sure we move in the right
direction. We also must have the right design artifacts to document
where we stand relative to the overall design that has loftier goals.


Representation
--------------

The xmodule collections:


+ `modulestore.active_versions`: this collection maps the org, course,
  and run to the current draft and published versions of the course.
+ `modulestore.structures`: this collection has one entry per course
  run and one for the template.
+ `modulestore.definitions`: this collection has one entry per
  "module" or "block" version.

modulestore.active_versions: 2 simple maps for dereferencing the
correct course from the structures collection. Every course run will
have a draft version. Not every course run will have a published
version. No course run will have more than one of each of these.

::

    { '_id' : uniqueid,
      'versions' : { <versionName> : versionGuid, ..}
      'creator' : user_id,
      'created' : date (native mongo rep)
    }

::



+ `id` is a unique id for finding this course run. It's a 
  location-reference string, like 'edu.mit.eng.eecs.6002x.industry.spring2013'.
+ `versions`: These are references to `modulestore.structures`. A
  location-reference like
  `edu.mit.eng.eecs.6002x.industry.spring2013;draft` refers to the value
  associated with `draft` for this document.

    + `versionName` is `draft`, `published`, or another user-defined
      string.
    + `versionGuid` is a system generated globally unique id (hash). It
      points to the entry in `modulestore.structures` ` `



`draftVersion`: the design will try to generate a new draft version
for each change to the course object: that is, for each move,
deletion, node creation, or metadata change. Cloning a course
(creating a new run of a course or such) will create a new entry in
this table with just a `draftVersion` and will cause a copy of the
corresponding entry in `modulestore.structures`. The entry in
`structures` will point to its version parent in the source course.




modulestore.structures : the entries in this collection follow this
definition:

::

    { '_id' : course_guid,
      'blocks' : 
        { block_guid :  // the guid is an arbitrary id to represent this node in the course tree
            { 'children' : [ block_guid* ],
              'metadata' : { property map },
              'definition' : definition_guid,
              'category' : 'section' | 'sequence' | ... } 


::

          ...// more guids


::

        },
      'root' : block_guid,
      'original' : course_guid, // the first version of this course from which all others were derived
      'previous' : course_guid | null, // the previous revision of this course (null if this is the original)
      'version_entry' : uniqueid, // from the active_versions collection
      'creator' : user_idÂ 
    }



+ `blocks`: each block is a node in the course such as the course, a
  section, a subsection, a unit, or a component. The block ids remain
  the same over edits (they're not versioned).
+ `root`: the true top of the course. Not all nodes without parents
  are truly roots. Some are orphans.
+ `course_guid, block_guid, definition_guid` are not those specific
  strings but instead some system generated globally unique id.

    + The one which gets passed around and pointed to by urls is the
      `block_guid`; so, it will be the one the system ensures is readable.
      Unlike the other guids, this one stays the same over revisions and can
      even be the same between course runs (although the course run
      contextualizes it to distinguish its instantiated version).

+ `definition` points to the specific revision of the given element in
  `modulestore.definitions` which this version of the course includes.
+ `children` lists the block_guids which are the children of this node
  in the course tree. It's an error if the guid in the `children` list
  does not occur in the `blocks` dictionary.
+ `metadata` is the node's explicitly defined metadata some of which
  may be inherited by its children


For debugging purposes, there may be value in adding a courseId field
(org, course, run) for use via db browsers.

modulestore.definitions : the data associated with each version of
each node in the structures. Many courses may point to the same
definition or may point to different versions derived from the same
original definition.

::

    { '_id' : guid,
      'data' : ..,
      'default_settings' : {'display_name':..,..}, // a starting point for new uses of this definition
      'category' : xblocktype, // the xmodule/xblock type such as course, problem, html, video, about
      'original' : guid, // the first kept version of this definition from which all others were derived
      'previous' : guid | null, // the previous revision of this definition (null if this is the original)
      'creator' : user_id  // the id of whomever pressed the draft or publish button
    }



+ `_id`: a guid to uniquely identify the definition.
+ `data` is the payload used by the xmodule and following the
  xmodule's data representation.
+ `category` is the xmodule type and used to figure out which xmodule
  to instantiate.


There may be some debugging value to adding a courseId field, but it
may also be misleading if the element is used in more than one course.


Templates
~~~~~~~~~

(I'm refactoring templates quite a bit from their representation prior
to this design)

All field defaults will be defined through the xblock field.default
mechanism. Templates, otoh, are for representing optional boilerplate
usually for examples such as a multiple-choice problem or a video
component with the fields all filled in. Templates are stored in yaml
files which provide a template name, sorting and filtering information
(e.g., requires advanced editor v allows simple editor), and then
field: value pairs for setting xblocks' fields upon template
selection.

Most of the pre-existing templates including all of the 'empty' ones
will go away. The ones which will stay are the ones truly just giving
examples or starting points for variants. This change will require
that the template choice code provide a default 'blank' choice to the
user which just instantiates the model w/ its defaults versus a choice
of the boilerplates. The client can therefore populate its own model
of the xblock and then send a create-item request to the server when
the user says he/she's ready to save it.


Import/export
~~~~~~~~~~~~~

Export should allow the user to select the version of the course to
export which can be any of the draft or published versions. At a
minimum, the user should choose between draft or published.

Import should import the course as a draft course regardless of
whether it was exported as a published or draft one, I believe. If
there's already a draft for the same course, in the best of all
worlds, it would have the guid to see if the guid exists in the
structures collection, and, if so, just make that the current
draftVersion (don't do any actual data changes). If there's no guid or
the guid doesn't exist in the structures collection, then we'll need
to work out the logic for how to decide what definitions to create v
update v point to.


Course ID
~~~~~~~~~

Currently, we use a triple to identify a run of a course. The triple
is organization, course name, and run identity (e.g., 2013Q1). The
system does not care what the id consists of only that it uniquely
identify an edition of the course. The system uses this id to organize
the course composition and find the course elements. It distinguishes
between a current being-edited version (aka, draft) and publicly
viewable version (published). Not every course has a published
version, but every course will have a draft version. The application
specifies whether it wants the draft or published version. This system
allows the application to easily switch between the 2; however, it
will have a configuration in which it's impossible to access the draft
so that we can add access optimizations and extraction filtering later
if needed.


Location
~~~~~~~~

The purpose of `Location` is to identify content. That is, to be able
to locate content by providing sufficient addressing. The `Location`
object is ubiquitous throughout the current code and thus will be
difficult to adapt and make more flexible. Right now, it's a very
simple `namedtuple` and a lot of code presumes this. This refactoring
generalizes and subclasses it to handle various addressing schemes and
remove direct manipulations.

Our code needs to locate several types of things and should probably
use several different types of locators for these. These are the types
of things we need to address. Some of these can be the same as others,
but I wanted to lay them out fairly fine grained here before proposing
my distinctions:


#. Courses: an object representing a course as an offering but not any
   of its content. Used for dashboards and other such navigators. These
   may specify a version or merely reference the idea of the course's
   existence.
#. Course structures: the names (and other metadata), `Locations`, and
   children pointers but not definitions for all the blocks in a course
   or a subtree of a course. Our applications often display contextual,
   outline, or other such structural information which do not need to
   include definitions but need to show display names, graded as, and
   other status info. This document's design makes fetching these a
   single document fetch; however, if it has to fetch the full course, it
   will require far more work (getting all definitions too) than the apps
   need.
#. Blocks (uses of definitions within a version of a course including
   metadata, pointers to children, and type specific content)
#. Definitions: use independent definitions of content without
   metadata (and currently w/o pointers to children).
#. Version trees Fetching the time history portrayal of a definition,
   course, or block including branching.
#. Collections of courses, definitions, or blocks matching some
   partial descriptors (e.g., all courses for org x, all definitions of
   type foo, all blocks in course y of type x, all currently accessible
   courses (published with startdate < today and enddate > today)).
#. Fetching of courses, blocks, or definitions via "human readable"
   urls. 
#. (partial descriptors) may suffice for this as human readable
   does not guarantee uniqueness.


Some of these differ not so much in how to address them but in what
should be returned. The content should be up to the functions not the
addressing scheme. So, I think the addressable things are:


#. Course as in #1 above: usually a specific offering of a course.
   Often used as a context for the other queries.
#. Blocks (aka usages) as in #3 above: a specific block contextualized
   in a course
#. Definitions (#4): a specific definition
#. Collections of courses, blocks within a specific course, or
   definitions matching a partial descriptor



Course locator (course_loc)
```````````````````````````

There are 3 ways to locate a course:


#. By its unique id in the `active_versions` collection with an
   implied or specified selection of draft or published version.
#. By its unique id in the `structures` collection.



Block locator (block_loc)
`````````````````````````

A block locator finds a specific node in a specific version of a
course. Thus, it needs a course locator plus a `usage_id`.


Definition locator (definition_loc)
```````````````````````````````````

Just a `guid`.


Partial descriptor collections locators (partial)
`````````````````````````````````````````````````

In the most general case, and to simplify implementation, these can be
any payload passable to mongo for doing the lookup. The specification
of which collection to look into can be implied by which lookup
function your code calls (get_courses, get_blocks, get_definitions) or
we could add it as another property. For now, I will leave this as
merely a search string. Thus, to find all courses for org = mitx,
`{"org": "mitx"}`. To find all blocks in a course whose display name
contains "circuit example", call `get_blocks` with the course locator
plus `{"metadata.display_name" : /circuit example/i}` (the i makes it
case insensitive and is just an example). To find if a definition is
used in a course, call get_blocks with the course locator plus
`{definition : definition_guid}`. Note, this looks for a specific
version of the definition. If you wanted to see if it used any of a
set of versions, use `{definition : {"$in" : [definition_guid*]}}`


i4x locator
```````````

To support existing xml based courses and any urls, we need to
support i4x locators. These are tuples of `(org course category id
['draft'])`. The trouble with these is that they don't uniquely
identify a course run from which to dereference the element. There's
also no requirement that `id` have any uniqueness outside the scope of
the other elements. There's some debate as to whether these address
blocks or definitions. To mean, they seem to address blocks; however,
in the current system there is no distinction between blocks and
definitions; so, either could be argued.

This version will define an `i4x_location` class for representing
these and using them for xml based courses if necessary.

Current code munges strings to make them 'acceptable' by replacing
'illegal' chars with underscores. I'd like to suggest leaving strings
as is and using url escaping to make acceptable urls. As to making
human readable names from display strings, that should be the
responsibility of the naming module not the Location representation,
imo.


Use cases (expository)
~~~~~~~~~~~~~~~~~~~~~~

There's a section below walking through a specific use case. This one
just tries to review potential functionality.


Inheritance
```````````

Our system has the notion of policies which should control the
behavior of whole courses or subtrees within courses. Such policies
include graceperiods, discussion forum controls, dates, whether to
show answers, how to randomize, etc. It's important that the course
authors' intent propagates to all relevant course sections. The
desired behavior is that (some? all?) metadata attributes on modules
flow down to all children unless overridden.

This design addresses inheritance by making course structure and
metadata separate from content thus enabling a single or small number
of db queries to get these and then compute the inheritance.


Separating editing from live production
```````````````````````````````````````

Course authors should be able to make changes in isolation from
production and then push out consistent chunks of changes for all
students to see as atomic and consistent. The current system allows
authors to change text and content without affecting production but
not metadata nor course structure. This design separates all changes
from production until pushed.


Sharing of content, part 1
``````````````````````````

Authors want to share content between course runs and even between
different courses. The current system requires copying all such
content and losing the providence information which could be used to
take advantage of other peoples' changes. This design allows multiple
courses and multiple places within a course to point to the same
definitions and thus potentially, at some day, see other changes to
the content.


Sharing of content, part 2: course structure
````````````````````````````````````````````

Because courses structures are separate from their identities, courses
can share structure and track changes in the same way as definitions.
That is, a new course run can point to an existing course instance
with its version history and then branch it from there.


Sharing of content, part 3: modules
```````````````````````````````````

Suppose a course includes a soldering tutorial (or a required lab
safety lesson). Other courses want to use the same tutorial and
possibly allow the student to skip it if the student succeeded at it
in another course. As the tutorial updates, other courses may want to
track the updates or choose to move to the updates without having to
copy the modules from the module's authoritative parent course.

This design enables sharing of composed modules but it does not track
the revisions of those modules separately from their courses. It does
not adequately address this but may be extendible enough to do so.
That is, we could represent these shared units as separate "courses"
and allow ids in block.children[] to point to courses as well as other
blocks in the same course.

We should decide on the behaviors we want. Such as, some times the
student has to repeat the content or the student never has to repeat
it or? progress should be tracked by the owning course or as a stand
alone minicourse type element? Because it's a safety lesson, all
courses should track the current published head and not have their own
heads or they should choose when to promote the head?

Are these shared elements rare and large grained enough to make the
indirection not expensive or will it result in devolving to the
current one entry per module design for deducing course structure?


Functional differences from existing modulestore:
-------------------------------------------------


+ Courses and definitions support trees of versions knowing from where
  they were derived. For now, I will not implement the server functions
  for retrieving and manipulating these version trees and will leave
  those for a future effort. I will only implement functions which
  extend the trees.
+ Changes to course structure don't immediately affect production:
  note, we need to figure out the granularity of the user's publish
  behavior for pushing out these actions. That is, do they publish a
  whole subtree which may include new children in order to make these
  effective, do they publish all structural (deletion, move) changes
  under a subtree but not insertions as an action, do they publish each
  action individually, or what? How do they know that any of these are
  not yet published? Do we have phantom placeholders for deleted nodes
  w/ "publish deletion" buttons?

    + Element deletion
    + Element move
    + metadata changes

+ No location objects used as ids! This implementation will use guids
  instead. There's a reasonable objection to guids as being too ugly,
  long, and indecipherable. I will check mongy, pymongo, and python guid
  generation mechanisms to find out if there's a way to make ones which
  include a prepended string (such as course and run or an explicitly
  stated prepend string) and minimize guid length (e.g., by using
  sequential serial # from a global or local pool).



Use case walkthrough:
---------------------

Simple course creation with no precursor course: Note, this shows that
publishing creates subsets and side copies not in line versions of
nodes.
user db create course for org, course id, run id
active_versions.draftVersion: add entry
definitions: add entry C w/ category = 'course', no data
structures: add entry w/ 1 child C, original = self, no previous,
author = user
add section S copy structures entry, new one points to old as original
and previous
active_versions.draftVersion points to new
definitions: add entry S w/ category = 'section'
structures entry:

+ add S to children of the course block,



+ add S to blocks w/ no children

add subsection T copy structures entry, new one points to old as
original and previous
active_versions.draftVersion points to new
definitions: add entry T w/ category = 'sequential'
structures entry:

+ add T to children of the S block entry,



+ add T to blocks w/ no children

add unit U copy structures entry, new one points to old as original
and previous
active_versions.draftVersion points to new
definitions: add entry U w/ category = 'vertical'
structures entry:

+ add U to children of the T block entry,



+ add U to blocks w/ no children

publish U
create structures entry, new one points to self as original (no
pointer to draft course b/c it's not really a clone)
active_versions.publishedVersion points to new
block: add U, T, S, C pointers with each as respective child
(regardless of other children they may have in draft), and their
metadata
add units V, W, X under T copy structures entry of the draftVersion,
new one points to old as original and previous
active_versions.draftVersion points to new
definitions: add entries V, W, X w/ category = 'vertical'
structures entry:

+ add V, W, X to children of the T block entry,



+ add V, W, X to blocks w/ no children

edit U copy structures entry, new one points to old as original and
previous
active_versions.draftVersion points to new
definitions: copy entry U to U_2 w/ updates, U_2 points to U as
original and previous
structures entry:

+ replace U w/ U_2 in children of the T block entry,



+ copy entry U in blocks to entry U_2 and remove U

add subsection Z under S copy structures entry, new one points to old
as original and previous
active_versions.draftVersion points to new
definitions: add entry Z w/ category = 'sequential'
structures entry:

+ add Z to children of the S block entry,



+ add Z to blocks w/ no children

edit S's name (metadata) copy structures entry, new one points to old
as original and previous
active_versions.draftVersion points to new
structures entry: update S's metadata w/ new name publish U, V copy
publishedCourse structures entry, new one points to old published as
original and previous
active_versions.publishedVersion points to new
block: update T to point to new U & V and not old U
Note: does not update S's name publish C copy publishedCourse
structures entry, new one points to old published as original and
previous
active_versions.publishedVersion points to new
blocks: note that C child S == published(S) but metadata !=, update
metadata
note that S has unpublished children: publish them (recurse on this)
note that Z is unpublished: add pointer to blocks and children of S
note that W, X unpublished: add to blocks, add to children of T edit C
metadata (e.g., graceperiod) copy draft structures entry, new one
points to old as original and previous
active_versions.draftVersion points to new
structures entry: update C's metadata add Y under Z ... publish C's
metadata change copy publishedCourse structures entry, new one points
to old published as original and previous
active_versions.publishedVersion points to new
blocks: update C's metadata
Note: no copying of Y or any other changes to published move X under Z
copy draft structures entry, new one points to old as original and
previous
active_versions.draftVersion points to new
structures entry: remove X from T's children and add to Z's
Note: making it persistently clear to the user that X still exists
under T in the published version will be crucial delete W copy draft
structures entry, new one points to old as original and previous
active_versions.draftVersion points to new
structures entry: remove W from T's children and remove W from blocks
Note: no actual deletion of W, just no longer reachable w/in the draft
course, but still in published; so, need to keep user aware of that.
publish Z Note: the interesting thing here is that X cannot occur
under both Z and T, but the user's not publishing T, here's where
having a consistent definition of original may help. If the original
of a new element == original of an existing, then it's an update?
copy publishedCourse entry...
definitions: add Y, copy/update Z, X if either have any data changes
(they don't)
blocks: remove X from T's children and add to Z's, add Y to Z, add Y
publish deletion of W copy publishedCourse entry...
structures entry: remove W from T's children and remove W from blocks
Conflict detection:

Need a scenario where 2 authors make edits to different parts of
course, to parts while parents being moved, while parents being
deleted, to same parts, ...

.. _http://www.mongodb.org/: http://www.mongodb.org/
 

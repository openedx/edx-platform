# Revamping the module system

## Goals:

* Enable CMS
* Allow reuse of content definitions between courses and within a course
* Allow contributed modules that don't have to be trusted.

## Big picture:

We a notion of a module definition (`XModuleDescriptor`) and a module in the context of a particular student (`XModule`).  We need to separate the first into a definition (e.g. for a problem: "what is 2+2?") and an instance of this definition ("What is 2+2?", in vert 3 of seq 1 of ch 4, with 3 attempts allowed, and worth 3 points).  We already have this mental distinction, but the code isn't quite there yet.

## Proposal:

3 kinds of things: XModuleDefinition ("2+2=?"), XModuleInstance (a particular use of "2+2=?"), and XModule (an instantiation of XModuleInstance for a student).

A course consists of instances.  Each instance in the course occurs exactly once, and has an instance_id which is unique within that course.  An instance_id identifies a definition, a policy, and a list of child instance_ids, which should correspond to the children of the definition.

See `common/lib/xmodule/xmodule/proposal/` for code interface sketches.

An instance is uniquely identified by "org/course/run/instance_id".  Since instance_id is trailing, it can slashes or any other chars we like.

### LMS integration

* Internally, all the code that works with modules doesn't really need to change much.

* Code that works with descriptors will primarily work with instances instead.

* urls -- the jump_to urls should now take an instance_id instead of a location.  Those urls are not publically exposed, but if anyone does have them bookmarked for some reason, they would break unless we put in special support.  I don't think we need to maintain them.


### CMS integration

* User chooses a definition, gets an instance of it, with some default instance id ('category/url_name', perhaps).  Can customize parameters, put it somewhere in the course, etc.  All the magic happens behind the scenes.

### XML integration

* file format/layout -- can support existing (new) format, interpret 'category/url_name' as the instance_id for everything by default.
* Can enable reuse of definitions, by separating out instance_ids from url_names.  So a pointer tag would become
  <category url_name='this_is_the_definition_pointer' instance_id='this_is_the_id'/>


### Modularity support....

* This set of changes doesn't have a big effect on our ability to put various things on different servers.  We should still be able to implement:
    * Definitions can live in various different places (e.g. partitioned by org or course)
    * We can (and should) design an service API that would let us run individual module code in separate processes/servers, and sandbox as necessary.

* The required_capabilities flag may allow us to pass less stuff to modules that don't need extra things.  Since I think the current plan is that edX folks will be the only ones to write container modules for now, this means that we can lock down the access modules get.



## Transition plan.

* How do we get there from here?
    * We should be able to maintain backwards compatibility throughout--I would suggest writing the new stuff straighforwardly, and having a separate import-from-old-format module that does a conversion before loading (possibly even during the build).
* capa_module/problem needs to be refactored to separate definition from student state.

## Design plan:

* I've been finding myself adding convenience methods to the XModule and XModuleDefinition interfaces over the last few months (e.g. get_child_by_url_name, compute_inherited_metadata).  It may be better to keep the core interface small, and add those to a separate util class.

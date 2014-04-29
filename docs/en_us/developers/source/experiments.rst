*******************************************
Content experiments
*******************************************

This is a brief overview of the support for content experiments in the platform.

For now, there is only one type of experiment: content split testing.  This lets course authors define an experiment with several *experimental conditions*, add xblocks that reference that experiment in various places in the course, and specify what content students in each experimental condition should see.  The LMS provides a way to randomly assign students to experimental conditions for each experiment, so that they see the right content at runtime.

Experimental conditions are essentially just a set of groups to partition users into.  This may be useful to other non-experiment uses, so the implementation is done via a generic UserPartition interface.  Copying the doc string, a UserPartition is:

    A named way to partition users into groups, primarily intended for running
    experiments.  It is expected that each user will be in at most one group in a
    partition.

    A Partition has an id, name, description, and a list of groups.
    The id is intended to be unique within the context where these are used. (e.g. for
    partitions of users within a course, the ids should be unique per-course)

There is an XModule helper library ``partitions_service`` that helps manage user partitions from XBlocks (at the moment just from the split_test module).  It provides an interface to store and retrieve the groups a user is in for particular partitions.  

User assignments to particular groups within a partition must be persisted.  This is done via a User Info service provided by the XBlock runtime, which exposes a generic user tagging interface, allowing storing key-value pairs for the user scoped to a particular course.

UserPartitions are configured at the course level (makes sense in Studio, for author context, and there's no XBlock scope to store per-course configuration state), and currently exposed via the LMS XBlock runtime as ``runtime.user_partitions``.

More details on the components below.


User metadata service
---------------------

Goals: provide a standard way to store information about users, to be used e.g. by XBlocks, and make that information easily accessible when looking at analytics.

When the course context is added to the analytics events, it should add the user's course-specific tags as well.
When the users global context is added to analytics events, it should add the user's global tags.

We have a ``user_api`` app, which has REST interface to "User Preferences" for global preferences, and now a ``user_service.py`` interface that exposes per-course tags, with string keys (<=255 chars) and arbitrary string values. The intention is that the values are fairly short, as they will be included in all analytics events about this user.

The XBlock runtime includes a ``UserServiceInterface`` mixin that provides access to this interface, automatically filling in the current user and course context.  This means that with the current design, an XBlock can't access tags for other users or from other courses.

To avoid name collisions in the keys, we rely on convention. e.g. the XBlock partition service uses ``'xblock.partition_service.partition_{0}'.format(user_partition.id)``.



Where the code is:
----------------


common:

- partitions library--defines UserPartitions, provides partitions_service API.
- split_test_module -- a block that has one child per experimental condition (could be a vertical or other container with more blocks inside), and config specifying which child corresponds to which condition.
- course_module -- a course has a list of UserPartitions, each of which specifies the set of groups to divide users into.

LMS:

- runtime--LmsUserPartitions, UserServiceMixin mixins.  Provides a way for the partition_service to get the list of UserPartitions defined in a course, and get/set per-user tags within a course scope.
- user_api app -- provides persistence for the user tags.

Things to watch out for (some not implemented yet):
-------------------------------------------

- grade export needs to be smarter, because different students can see different graded things
- grading needs to only grade the children that a particular student sees (so if there are problems in both conditions in a split_test, any student would see only one set)
- ui -- icons in sequences need to be passed through
   - tooltips need to be passed through
- author changes post-release: conditions can be added or deleted after an experiment is live.  This is usually a bad idea, but can be useful, so it's allowed.  Need to handle all the cases.
- analytics logging needs to log all the user tags (if we really think it's a good idea).  We'll probably want to cache the tags in memory for the duration of the request, being careful that they may change as the request is processed.
- need to add a "hiding" interface to XBlocks that verticals, sequentials, and courses understand, to hide children that set it.  Then give the split test module a way to say that particular condition should be empty and hidden, and pass that up.
- staff view should show all the conditions, clearly marked
 
Things to test:
  - randomization
  - persistence
  - correlation between test that use the same groups
  - non-correlation between tests that use different groups


# Refactoring group access checks

## Problem: `_has_group_access` is horribly inefficient
## Suggested Solution: prefetch a bunch of data

### Here's how that will work:
  - instead of looking up the correct partition and groups *per thread*, we'll just look up all of them once
  - then, if prefetch data exists, the actual check can just look at that instead

#### The data that is currently looked up per thread:
  - `partition_id, group_ids in merged_access.items()`
    - read: the partitions that have access to this thread, and their corresponding group ids
    - only active partitions are included
    - new plan: prefetch *all* partitions in the course:
      - via `descriptor.runtime.service(self, 'partitions').course_partitions`
      - ref: https://github.com/edx/edx-platform/blob/master/common/lib/xmodule/xmodule/partitions/partitions_service.py#L107
  - `partition.get_group(group_id)` for each partition in `merged_access`
    - new plan: exactly that, for all partitions in the course
  - `partition.scheme.get_group_for_user` for each partition in `merged_access`
    - new plan: exactly that, for all partitions in the course
  - Then we proceed with the check, which I'll address below
  - End result of new plan prefetch data:
    - a dictionary of *all* ids of partitions in the course, mapped to *all* the group ids that exist in that partition
    - a dictionary of *all* ids of partitions in the course, mapped to *only* the group ids the user belongs to

#### Actually checking access

This turns out to be a fairly simple question: `For each partition in merged_access, does the user's assigned group_id appear in the list of allowed group_ids?`

#### Implementation

- In [this function](https://github.com/edx/edx-platform/blob/239177a5f543f2d2beb263e1501299af8acf181d/lms/djangoapps/django_comment_client/utils.py#L133), I plan to add the "prefetch data" logic to gather the course-wide data specified above
  - Said data will then be passed through as an optional param to the `has_access` call that appears in the following list comprehension
  - `has_access` will need to continue passing the additional `prefetch_data` param [here](https://github.com/edx/edx-platform/blob/1f5c94d9b60ec1a4c3b65e244a5b54f7ac371372/lms/djangoapps/courseware/access.py#L153), [then here](https://github.com/edx/edx-platform/blob/1f5c94d9b60ec1a4c3b65e244a5b54f7ac371372/lms/djangoapps/courseware/access.py#L496) in order to get it into `_has_group_access`
- Inside of `_has_group_access`, we'll need special logic to check `prefetch_data`
  - It will probabaly involve creating a new subset of `prefetch_data`, containing only those values that are also present in `merged_group_access`
  - Doing that to short-circuit the construction of `partition_groups` and `user_groups` will allow us to leave the final line in place:
    - `if not all(user_groups.get(partition.id) in groups for partition, groups in partition_groups):`

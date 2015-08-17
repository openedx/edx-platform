"""
Social Facebook API
"""

# TODO
# There are still some performance and scalability issues that should be
# addressed for the various endpoints in this social_facebook djangoapp.
#
# For the Courses and Friends API:
# For both endpoints, we are retrieving the same data from the Facebook server.
# We are then simply organizing and filtering that data differently for each endpoint.
#
# Here are 3 ideas that can be explored further:
#
# Option 1. The app can just call one endpoint that provides a mapping between CourseIDs and Friends,
# and then cache that data once. The reverse map from Friends to CourseIDs can then be created on the app side.
#
# Option 2. The app once again calls just one endpoint (since the same data is computed for both),
# and caches the data once. The difference from #1 is that the server does the computation of the reverse-map and
# sends both maps down to the client. It's a tradeoff between bandwidth and client-side computation. So the payload
# could be something like:
#
# {
#   courses: [
#      {course_id: "c/ourse/1", friend_indices: [1, 2, 3]},
#      {course_id: "c/ourse/2", friend_indices: [3, 4, 5]},
#      ..
#   ],
#   friends: [
#      {username: "friend1", facebook_id: "xxx", course_indices: [2, 7, 9]},
#      {username: "friend2", facebook_id: "yyy", course_indices: [1, 4, 3]},
#      ...
#   ]
# }
#
# Option 3. Alternatively, continue to have separate endpoints, but have both endpoints call the same underlying method
# with a built-in cache.
#
# All 3 options can make use of a common cache of results from FB.
#
# At a minimum, some performance/load testing would need to be done
# so we have an idea of these endpoints' limitations and thresholds.

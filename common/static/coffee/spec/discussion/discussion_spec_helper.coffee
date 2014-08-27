class @DiscussionSpecHelper
    # This is sad. We should avoid dependence on global vars.
    @setUpGlobals = ->
        DiscussionUtil.loadRoles({"Moderator": [], "Administrator": [], "Community TA": []})
        window.$$course_id = "edX/999/test"
        window.user = new DiscussionUser({username: "test_user", id: "567", upvoted_ids: []})

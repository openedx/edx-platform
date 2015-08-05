define([
    'underscore', 'common/js/spec_helpers/ajax_helpers'
], function (_, AjaxHelpers) {
    'use strict';
    var createMockPostResponse, createMockDiscussionResponse, createAnnotatedContentInfo, createMockThreadResponse,
        testCourseID = 'course/1',
        testUser = 'testUser',
        testTeamDiscussionID = "12345";

    createMockPostResponse = function(options) {
        return _.extend(
            {
                username: testUser,
                course_id: testCourseID,
                commentable_id: testTeamDiscussionID,
                type: 'thread',
                body: "",
                anonymous_to_peers: false,
                unread_comments_count: 0,
                updated_at: '2015-07-29T18:44:56Z',
                group_name: 'Default Group',
                pinned: false,
                votes: {count: 0, down_count: 0, point: 0, up_count: 0},
                user_id: "9",
                abuse_flaggers: [],
                closed: false,
                at_position_list: [],
                read: false,
                anonymous: false,
                created_at: "2015-07-29T18:44:56Z",
                thread_type: 'discussion',
                comments_count: 0,
                group_id: 1,
                endorsed: false
            },
            options || {}
        );
    };

    createMockDiscussionResponse = function(threads) {
        if (_.isUndefined(threads)) {
            threads = [
                createMockPostResponse({ id: "1", title: "First Post"}),
                createMockPostResponse({ id: "2", title: "Second Post"}),
                createMockPostResponse({ id: "3", title: "Third Post"})
            ];
        }
        return {
            "num_pages": 1,
            "page": 1,
            "discussion_data": threads,
            "user_info": {
                "username": testUser,
                "follower_ids": [],
                "default_sort_key": "date",
                "downvoted_ids": [],
                "subscribed_thread_ids": [],
                "upvoted_ids": [],
                "external_id": "9",
                "id": "9",
                "subscribed_user_ids": [],
                "subscribed_commentable_ids": []
            },
            "annotated_content_info": {
            },
            "roles": {"Moderator": [], "Administrator": [], "Community TA": []},
            "course_settings": {
                "is_cohorted": false,
                "allow_anonymous_to_peers": false,
                "allow_anonymous": true,
                "category_map": {"subcategories": {}, "children": [], "entries": {}},
                "cohorts": []
            }
        };
    };

    createAnnotatedContentInfo = function() {
        return {
            voted: '',
            subscribed: true,
            ability: {
                can_reply: true,
                editable: true,
                can_openclose: true,
                can_delete: true,
                can_vote: true
            }
        };
    };

    createMockThreadResponse = function(options) {
        return _.extend(
            {
                username: testUser,
                course_id: testCourseID,
                commentable_id: testTeamDiscussionID,
                children: [],
                comments_count: 0,
                anonymous_to_peers: false,
                unread_comments_count: 0,
                updated_at: "2015-08-04T21:44:28Z",
                resp_skip: 0,
                id: "55c1323c56c02ce921000001",
                pinned: false,
                votes: {"count": 0, "down_count": 0, "point": 0, "up_count": 0},
                resp_limit: 25,
                abuse_flaggers: [],
                closed: false,
                resp_total: 1,
                at_position_list: [],
                type: "thread",
                read: true,
                anonymous: false,
                user_id: "5",
                created_at: "2015-08-04T21:44:28Z",
                thread_type: "discussion",
                context: "standalone",
                endorsed: false
            },
            options || {}
        );
    };

    return {
        testCourseID: testCourseID,
        testUser: testUser,
        testTeamDiscussionID: testTeamDiscussionID,
        createMockPostResponse: createMockPostResponse,
        createMockDiscussionResponse: createMockDiscussionResponse,
        createAnnotatedContentInfo: createAnnotatedContentInfo,
        createMockThreadResponse: createMockThreadResponse
    };
});

define([
    'underscore', 'common/js/spec_helpers/ajax_helpers'
], function (_, AjaxHelpers) {
    'use strict';
    var createMockThreadResponse, createMockDiscussionResponse, createAnnotatedContentInfo, loadDiscussionView,
        testCourseID = 'course/1',
        testUser = 'testUser';

    createMockThreadResponse = function(options) {
        return _.extend(_.extend({
                type: 'thread',
                body: "Test body",
                anonymous_to_peers: false,
                unread_comments_count: 0,
                updated_at: '2015-07-29T18:44:56Z',
                group_name: 'Default Group',
                course_id: testCourseID,
                pinned: false,
                votes: {count: 0, down_count: 0, point: 0, up_count: 0},
                user_id: "9",
                commentable_id: "67890",
                abuse_flaggers: [],
                closed: false,
                at_position_list: [],
                read: false,
                anonymous: false,
                created_at: "2015-07-29T18:44:56Z",
                thread_type: 'discussion',
                username: testUser,
                comments_count: 0,
                group_id: 1,
                endorsed: false
            }),
            options);
    };

    createMockDiscussionResponse = function() {
        return {
            "num_pages": 1,
            "page": 1,
            "discussion_data": [
                createMockThreadResponse({ id: "1", title: "First Post"}),
                createMockThreadResponse({ id: "2", title: "Second Post"}),
                createMockThreadResponse({ id: "3", title: "Third Post"})
            ],
            "user_info": {
                "username": testUser,
                "follower_ids": [],
                "default_sort_key": "date",
                "downvoted_ids": [],
                "subscribed_thread_ids": ["55b91ef756c02c54a1000001", "55b91f2856c02c0d1d000003"],
                "upvoted_ids": [],
                "external_id": "9",
                "id": "9",
                "subscribed_user_ids": [],
                "subscribed_commentable_ids": []
            },
            "annotated_content_info": {
                "55b78e2956c02c6655000001": {
                    "voted": "",
                    "subscribed": false,
                    "ability": {"can_reply": true, "editable": false, "can_openclose": false, "can_delete": false, "can_vote": true}
                },
                "55b91ef756c02c54a1000001": {
                    "voted": "",
                    "subscribed": true,
                    "ability": {"can_reply": true, "editable": true, "can_openclose": false, "can_delete": true, "can_vote": true}
                },
                "55b91f2856c02c0d1d000003": {
                    "voted": "",
                    "subscribed": true,
                    "ability": {"can_reply": true, "editable": true, "can_openclose": false, "can_delete": true, "can_vote": true}
                }
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

    return {
        createMockThreadResponse: createMockThreadResponse,
        createMockDiscussionResponse: createMockDiscussionResponse,
        createAnnotatedContentInfo: createAnnotatedContentInfo
    };
});

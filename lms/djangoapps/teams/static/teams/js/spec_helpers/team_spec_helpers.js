define([
    'backbone',
    'underscore',
    'teams/js/collections/team',
    'teams/js/collections/team_membership',
    'teams/js/collections/topic'
], function (Backbone, _, TeamCollection, TeamMembershipCollection, TopicCollection) {
    'use strict';
    var createMockPostResponse, createMockDiscussionResponse, createAnnotatedContentInfo, createMockThreadResponse,
        createMockTopicData, createMockTopicCollection,
        testCourseID = 'course/1',
        testUser = 'testUser',
        testTeamDiscussionID = "12345",
        teamEvents = _.clone(Backbone.Events),
        testCountries = [
            ['', ''],
            ['US', 'United States'],
            ['CA', 'Canada'],
            ['MX', 'Mexico']
        ],
        testLanguages = [
            ['', ''],
            ['en', 'English'],
            ['es', 'Spanish'],
            ['fr', 'French']
        ];

    var createMockTeamData = function (startIndex, stopIndex) {
        return _.map(_.range(startIndex, stopIndex + 1), function (i) {
            return {
                name: "team " + i,
                id: "id " + i,
                language: testLanguages[i%4][0],
                country: testCountries[i%4][0],
                is_active: true,
                membership: [],
                last_activity_at: ''
            };
        });
    };

    var createMockTeams = function(teamData) {
        if (!teamData) {
            teamData = createMockTeamData(1, 5);
        }
        return new TeamCollection(
            {
                count: 6,
                num_pages: 2,
                current_page: 1,
                start: 0,
                results: teamData
            },
            {
                teamEvents: teamEvents,
                course_id: 'my/course/id',
                parse: true
            }
        );
    };

    var createMockTeamMembershipsData = function(startIndex, stopIndex) {
        var teams = createMockTeamData(startIndex, stopIndex);
        return _.map(_.range(startIndex, stopIndex + 1), function (i) {
            return {
                user: {
                    'username': testUser,
                    'url': 'https://openedx.example.com/api/user/v1/accounts/' + testUser
                },
                team: teams[i-1]
            };
        });
    };

    var createMockTeamMemberships = function(teamMembershipData, options) {
        if (!teamMembershipData) {
            teamMembershipData = createMockTeamMembershipsData(1, 5);
        }
        return new TeamMembershipCollection(
            {
                count: 11,
                num_pages: 3,
                current_page: 1,
                start: 0,
                results: teamMembershipData
            },
            _.extend(_.extend({}, {
                    teamEvents: teamEvents,
                    course_id: 'my/course/id',
                    parse: true,
                    url: 'api/teams/team_memberships',
                    username: testUser,
                    privileged: false,
                    staff: false
                }),
                options)
        );
    };

    var createMockUserInfo = function(options) {
        return _.extend(
            {
                username: testUser,
                privileged: false,
                staff: false,
                team_memberships_data: createMockTeamMembershipsData(1, 5)
            },
            options
        );
    };

    var verifyCards = function(view, teams) {
        var teamCards = view.$('.team-card');
        _.each(teams, function (team, index) {
            var currentCard = teamCards.eq(index);
            expect(currentCard.text()).toMatch(team.name);
            expect(currentCard.text()).toMatch(_.object(testLanguages)[team.language]);
            expect(currentCard.text()).toMatch(_.object(testCountries)[team.country]);
        });
    };

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

    createMockTopicData = function (startIndex, stopIndex) {
        return _.map(_.range(startIndex, stopIndex + 1), function (i) {
            return {
                "description": "description " + i,
                "name": "topic " + i,
                "id": "id " + i,
                "team_count": 0
            };
        });
    };

    createMockTopicCollection = function (topicData) {
        topicData = topicData !== undefined ? topicData : createMockTopicData(1, 5);

        return new TopicCollection(
            {
                count: topicData.length + 1,
                current_page: 1,
                num_pages: 2,
                start: 0,
                results: topicData,
                sort_order: "name"
            },
            {
                teamEvents: teamEvents,
                course_id: 'my/course/id',
                parse: true,
                url: 'api/teams/topics'
            }
        );
    };

    return {
        teamEvents: teamEvents,
        testCourseID: testCourseID,
        testUser: testUser,
        testCountries: testCountries,
        testLanguages: testLanguages,
        testTeamDiscussionID: testTeamDiscussionID,
        createMockTeamData: createMockTeamData,
        createMockTeams: createMockTeams,
        createMockTeamMembershipsData: createMockTeamMembershipsData,
        createMockTeamMemberships: createMockTeamMemberships,
        createMockUserInfo: createMockUserInfo,
        createMockPostResponse: createMockPostResponse,
        createMockDiscussionResponse: createMockDiscussionResponse,
        createAnnotatedContentInfo: createAnnotatedContentInfo,
        createMockThreadResponse: createMockThreadResponse,
        createMockTopicData: createMockTopicData,
        createMockTopicCollection: createMockTopicCollection,
        verifyCards: verifyCards
    };
});

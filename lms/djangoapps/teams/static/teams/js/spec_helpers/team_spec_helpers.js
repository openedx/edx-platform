define([
    'backbone',
    'underscore',
    'teams/js/collections/team',
    'teams/js/collections/topic',
    'teams/js/models/topic'
], function(Backbone, _, TeamCollection, TopicCollection, TopicModel) {
    'use strict';
    var createMockPostResponse, createMockDiscussionResponse, createAnnotatedContentInfo, createMockThreadResponse,
        createMockTopicData, createMockTopicCollection, createMockTopic,
        createMockContext,
        testContext,
        testCourseID = 'course/1',
        testUser = 'testUser',
        testTopicID = 'test-topic-1',
        testTeamDiscussionID = '12345',
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

    var createMockTeamData = function(startIndex, stopIndex) {
        return _.map(_.range(startIndex, stopIndex + 1), function(i) {
            var id = 'id' + i;
            return {
                name: 'team ' + i,
                id: id,
                language: testLanguages[i % 4][0],
                country: testCountries[i % 4][0],
                membership: [],
                last_activity_at: '',
                topic_id: 'topic_id' + i,
                url: 'api/team/v0/teams/' + id
            };
        });
    };

    var createMockTeamsResponse = function(options) {
        return _.extend(
            {
                count: 6,
                num_pages: 2,
                current_page: 1,
                start: 0,
                results: createMockTeamData(1, 5)
            },
            options
        );
    };

    var createMockTeams = function(responseOptions, options, collectionType) {
        if (_.isUndefined(collectionType)) {
            collectionType = TeamCollection; // eslint-disable-line no-param-reassign
        }
        return new collectionType(
            createMockTeamsResponse(responseOptions),
            _.extend({
                perPage: 5,
                teamEvents: teamEvents,
                course_id: testCourseID,
                parse: true
            }, options)
        );
    };

    var createMockTeamAssignments = function(assignments, options) {
        if (_.isUndefined(assignments)) {
            assignments = [ // eslint-disable-line no-param-reassign
                {
                    display_name: 'Send me',
                    location: 'your location'
                }
            ];
        }
        return _.extend(assignments, options);
    };

    var createMockTeamMembershipsData = function(startIndex, stopIndex) {
        var teams = createMockTeamData(startIndex, stopIndex);
        return _.map(_.range(startIndex, stopIndex + 1), function(i) {
            return {
                user: {
                    username: testUser,
                    url: 'https://openedx.example.com/api/user/v1/accounts/' + testUser,
                    profile_image: {
                        image_url_small: 'test_profile_image'
                    }
                },
                team: teams[i - 1]
            };
        });
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


    /**
     * Verify that the given view shows cards for each of the teams included.
     * If showTeamset is included (true or false), the test will also verify that the teamset
     * label/penannt is or is not included in the card accordingly.
     *
     * @param {JQ Element} view - jquery DOM element for the card container
     * @param {TeamModel[]} teams - list of teams to verify.
     * @param {[bool]} showTeamset - should show teamset string? (if not included, do not check
     *     the teamset string at all)
     */
    var verifyCards = function(view, teams, showTeamset) {
        var teamCards = view.$('.team-card');
        _.each(teams, function(team, index) {
            var currentCard = teamCards.eq(index);
            var teamsetString = 'teamset-name-' + team.topic_id;
            expect(currentCard.text()).toMatch(team.name);
            expect(currentCard.text()).toMatch(_.object(testLanguages)[team.language]);
            expect(currentCard.text()).toMatch(_.object(testCountries)[team.country]);
            if (showTeamset === false) {
                expect(currentCard.text()).not.toMatch(teamsetString);
            }
            if (showTeamset === true) {
                expect(currentCard.text()).toMatch(teamsetString);
            }
        });
    };

    var triggerTeamEvent = function(action) {
        teamEvents.trigger('teams:update', {action: action});
    };

    createMockPostResponse = function(options) {
        return _.extend(
            {
                username: testUser,
                course_id: testCourseID,
                commentable_id: testTeamDiscussionID,
                type: 'thread',
                body: '',
                anonymous_to_peers: false,
                unread_comments_count: 0,
                updated_at: '2015-07-29T18:44:56Z',
                group_name: 'Default Group',
                pinned: false,
                votes: {count: 0, down_count: 0, point: 0, up_count: 0},
                user_id: '9',
                abuse_flaggers: [],
                closed: false,
                at_position_list: [],
                read: false,
                anonymous: false,
                created_at: '2015-07-29T18:44:56Z',
                thread_type: 'discussion',
                comments_count: 0,
                group_id: 1,
                endorsed: false
            },
            options
        );
    };

    createMockDiscussionResponse = function(threads) {
        var responseThreads = threads;
        if (_.isUndefined(threads)) {
            responseThreads = [
                createMockPostResponse({id: '1', title: 'First Post'}),
                createMockPostResponse({id: '2', title: 'Second Post'}),
                createMockPostResponse({id: '3', title: 'Third Post'})
            ];
        }
        return {
            num_pages: 1,
            page: 1,
            discussion_data: responseThreads,
            user_info: {
                username: testUser,
                follower_ids: [],
                default_sort_key: 'date',
                downvoted_ids: [],
                subscribed_thread_ids: [],
                upvoted_ids: [],
                external_id: '9',
                id: '9',
                subscribed_user_ids: [],
                subscribed_commentable_ids: []
            },
            annotated_content_info: {
            },
            roles: {Moderator: [], Administrator: [], 'Community TA': []},
            course_settings: {
                is_cohorted: false,
                allow_anonymous_to_peers: false,
                allow_anonymous: true,
                category_map: {subcategories: {}, children: [], entries: {}},
                cohorts: []
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
                updated_at: '2015-08-04T21:44:28Z',
                resp_skip: 0,
                id: '55c1323c56c02ce921000001',
                pinned: false,
                votes: {count: 0, down_count: 0, point: 0, up_count: 0},
                resp_limit: 25,
                abuse_flaggers: [],
                closed: false,
                resp_total: 1,
                at_position_list: [],
                type: 'thread',
                read: true,
                anonymous: false,
                user_id: '5',
                created_at: '2015-08-04T21:44:28Z',
                thread_type: 'discussion',
                context: 'standalone',
                endorsed: false
            },
            options
        );
    };

    createMockTopicData = function(startIndex, stopIndex) {
        return _.map(_.range(startIndex, stopIndex + 1), function(i) {
            return {
                description: 'Test description ' + i,
                name: 'Test Topic ' + i,
                id: 'test-topic-' + i,
                team_count: 0
            };
        });
    };

    createMockTopic = function(options) {
        return new TopicModel(_.extend(
            {
                id: testTopicID,
                name: 'Test Topic 1',
                description: 'Test description 1',
                type: 'open'
            },
            options
        ));
    };

    testContext = {
        courseID: testCourseID,
        topics: {
            count: 5,
            num_pages: 1,
            current_page: 1,
            start: 0,
            results: createMockTopicData(1, 5)
        },
        hasOpenTopic: true,
        hasPublicManagedTopic: false,
        hasManagedTopic: false,
        courseMaxTeamSize: 6,
        languages: testLanguages,
        countries: testCountries,
        topicUrl: '/api/team/v0/topics/topic_id,' + testCourseID,
        teamsUrl: '/api/team/v0/teams/',
        teamsAssignmentsUrl: '/api/team/v0/teams/team_id/assignments',
        teamsDetailUrl: '/api/team/v0/teams/team_id',
        teamMembershipsUrl: '/api/team/v0/team_memberships/',
        teamMembershipDetailUrl: '/api/team/v0/team_membership/team_id,' + testUser,
        myTeamsUrl: '/api/team/v0/teams/',
        userInfo: createMockUserInfo()
    };

    createMockContext = function(options) {
        return _.extend({}, testContext, options);
    };

    createMockTopicCollection = function(topicData) {
        // eslint-disable-next-line no-param-reassign
        topicData = topicData !== undefined ? topicData : createMockTopicData(1, 5);

        return new TopicCollection(
            {
                count: topicData.length + 1,
                current_page: 1,
                num_pages: 2,
                start: 0,
                results: topicData,
                sort_order: 'name'
            },
            {
                teamEvents: teamEvents,
                course_id: testCourseID,
                parse: true,
                url: testContext.topicUrl
            }
        );
    };

    return {
        teamEvents: teamEvents,
        testCourseID: testCourseID,
        testUser: testUser,
        testTopicID: testTopicID,
        testCountries: testCountries,
        testLanguages: testLanguages,
        testTeamDiscussionID: testTeamDiscussionID,
        testContext: testContext,
        createMockTeamData: createMockTeamData,
        createMockTeamsResponse: createMockTeamsResponse,
        createMockTeams: createMockTeams,
        createMockTeamAssignments: createMockTeamAssignments,
        createMockUserInfo: createMockUserInfo,
        createMockContext: createMockContext,
        createMockTopic: createMockTopic,
        createMockPostResponse: createMockPostResponse,
        createMockDiscussionResponse: createMockDiscussionResponse,
        createAnnotatedContentInfo: createAnnotatedContentInfo,
        createMockThreadResponse: createMockThreadResponse,
        createMockTopicData: createMockTopicData,
        createMockTopicCollection: createMockTopicCollection,
        triggerTeamEvent: triggerTeamEvent,
        verifyCards: verifyCards
    };
});

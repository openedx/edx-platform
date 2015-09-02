define(['backbone', 'URI', 'underscore', 'common/js/spec_helpers/ajax_helpers',
        'teams/js/spec_helpers/team_spec_helpers'],
    function (Backbone, URI, _, AjaxHelpers, TeamSpecHelpers) {
        'use strict';
        describe('TopicCollection', function () {
            var topicCollection;
            beforeEach(function () {
                topicCollection = TeamSpecHelpers.createMockTopicCollection();
            });

            var testRequestParam = function (self, param, value) {
                var requests = AjaxHelpers.requests(self),
                    url,
                    params;
                topicCollection.fetch();
                expect(requests.length).toBe(1);
                url = new URI(requests[0].url);
                params = url.query(true);
                expect(params[param]).toBe(value);
            };

            it('sets its perPage based on initial page size', function () {
                expect(topicCollection.perPage).toBe(5);
            });

            it('sorts by name', function () {
                testRequestParam(this, 'order_by', 'name');
            });

            it('passes a course_id to the server', function () {
                testRequestParam(this, 'course_id', TeamSpecHelpers.testCourseID);
            });

            it('URL encodes its course_id ', function () {
                topicCollection.course_id = 'my+course+id';
                testRequestParam(this, 'course_id', 'my+course+id');
            });
        });
    });

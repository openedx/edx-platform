define(['URI', 'underscore', 'common/js/spec_helpers/ajax_helpers', 'teams/js/collections/topic'],
    function (URI, _, AjaxHelpers, TopicCollection) {
        'use strict';
        describe('TopicCollection', function () {
            var topicCollection;
            beforeEach(function () {
                topicCollection = new TopicCollection(
                    {
                        "count": 6,
                        "num_pages": 2,
                        "current_page": 1,
                        "start": 0,
                        "results": [
                            {
                                "description": "asdf description",
                                "name": "asdf",
                                "id": "_asdf"
                            },
                            {
                                "description": "bar description",
                                "name": "bar",
                                "id": "_bar"
                            },
                            {
                                "description": "baz description",
                                "name": "baz",
                                "id": "_baz"
                            },
                            {
                                "description": "foo description",
                                "name": "foo",
                                "id": "_foo"
                            },
                            {
                                "description": "qwerty description",
                                "name": "qwerty",
                                "id": "_qwerty"
                            }
                        ],
                        "sort_order": "name"
                    },
                    {course_id: 'my/course/id', parse: true});
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
                testRequestParam(this, 'course_id', 'my/course/id');
            });

            it('URL encodes its course_id ', function () {
                topicCollection.course_id = 'my+course+id';
                testRequestParam(this, 'course_id', 'my+course+id');
            });
        });
    });

define(['teams/js/views/topic_header', 'teams/js/collections/topic'],
    function (TopicHeader, TopicCollection) {
        'use strict';
        describe('TopicHeader', function () {
            var topicHeader,
                courseId = 'testX/test/test_20XX',
                newCollection = function (size, perPage) {
                    var pageSize = 5,
                        results = _.map(_.range(size), function (i) {
                            return {
                                "description": "description " + i,
                                "name": "topic " + i,
                                "id": "id " + i
                            };
                        });
                    var collection = new TopicCollection(
                        {
                            count: results.length,
                            num_pages: results.length / pageSize,
                            current_page: 1,
                            start: 0,
                            results: _.first(results, perPage)
                        },
                        {course_id: courseId, parse: true}
                    );
                    collection.start = 0;
                    collection.totalCount = results.length;
                    return collection;
                };

            it('can load templates', function () {
                topicHeader = new TopicHeader({
                    collection: new TopicCollection(
                        {
                            count: 0,
                            num_pages: 1,
                            current_page: 1,
                            start: 0,
                            results: []
                        },
                        {course_id: courseId}
                    )
                }).render();
                expect(topicHeader.$el.find('.search-count').text()).toContain('Currently viewing');
            });

            it('correctly displays which topics are being viewed', function () {
                topicHeader = new TopicHeader({
                    collection: newCollection(20, 5)
                }).render();
                expect(topicHeader.$el.find('.search-count').text())
                    .toContain('Currently viewing 1 through 5 of 20 topics');
            });

            it('reports that all topics are on the current page', function () {
                topicHeader = new TopicHeader({
                    collection: newCollection(5, 5)
                }).render();
                expect(topicHeader.$el.find('.search-count').text())
                    .toContain('Currently viewing all 5 topics');
            });

            it('reports that the page contains a single topic', function () {
                topicHeader = new TopicHeader({
                    collection: newCollection(1, 1)
                }).render();
                expect(topicHeader.$el.find('.search-count').text())
                    .toContain('Currently viewing 1 topic');
            });
        });
    });

define([
    'teams/js/collections/topic', 'teams/js/views/topics'
], function (TopicCollection, TopicsView) {
    'use strict';
    describe('TopicsView', function () {
        var initialTopics, topicCollection, topicsView,
            generateTopics = function (startIndex, stopIndex) {
            return _.map(_.range(startIndex, stopIndex + 1), function (i) {
                return {
                    "description": "description " + i,
                    "name": "topic " + i,
                    "id": "id " + i,
                    "team_count": 0
                };
            });
        };

        beforeEach(function () {
            setFixtures('<div class="topics-container"></div>');
            initialTopics = generateTopics(1, 5);
            topicCollection = new TopicCollection(
                {
                    "count": 6,
                    "num_pages": 2,
                    "current_page": 1,
                    "start": 0,
                    "results": initialTopics
                },
                {course_id: 'my/course/id', parse: true}
            );
            topicsView = new TopicsView({el: '.topics-container', collection: topicCollection}).render();
        });

        it('can render the first of many pages', function () {
            var footerEl = topicsView.$('.topics-paging-footer'),
                topicCards = topicsView.$('.topic-card');
            expect(topicsView.$('.topics-paging-header').text()).toMatch('Showing 1-5 out of 6 total');
            _.each(initialTopics, function (topic, index) {
                var currentCard = topicCards.eq(index);
                expect(currentCard.text()).toMatch(topic.name);
                expect(currentCard.text()).toMatch(topic.description);
                expect(currentCard.text()).toMatch(topic.team_count + ' Teams');
            });
            expect(footerEl.text()).toMatch('1\\s+out of\\s+\/\\s+2');
            expect(footerEl).not.toHaveClass('hidden');
        });
    });
});

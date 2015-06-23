define([
    'common/js/spec_helpers/ajax_helpers', 'teams/js/collections/topic', 'teams/js/views/topics'
], function (AjaxHelpers, TopicCollection, TopicsView) {
    describe('TopicsView', function () {
        var generateTopics, initialTopics, topicCollection, topicsView, expectHeaderOnPage, expectViewReflectsState;

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

        /**
         * Verify that the topics view's header reflects the page we're currently viewing.
         * @param options a parameters hash containing:
         *  - firstIndex: the one-indexed index of the first topic on the page
         *  - lastIndex: the one-indexed index of the last topic on the page
         *  - totalCount: the total number of topics to page through
         * @param onlyPage if true, expect to see the only page version of the header message
         */
        expectHeaderOnPage = function (options, onlyPage) {
            if (onlyPage) {
                expect(topicsView.$('.topics-paging-header').text()).toMatch(
                    interpolate('Currently viewing all %(total)s topics', {
                        total: options.totalCount
                    }, true)
                );
            } else {
                expect(topicsView.$('.topics-paging-header').text()).toMatch(
                    interpolate('Currently viewing %(start)s through %(end)s of %(total)s topics', {
                        start: options.firstIndex, end: options.lastIndex, total: options.totalCount
                    }, true)
                );
            }
        };

        /**
         * Verify that the topics list view and footer reflects the page and topics states.
         * @param options a parameters hash containing:
         *  - expectedTopics: an array of topic objects we expect to see
         *  - currentPage: the one-indexed page we expect to be viewing
         *  - totalPages: the total number of pages to page through
         */
        expectViewReflectsState = function (options) {
            var topicCards;
            // Verify the topics list
            topicCards = topicsView.$('.topic-card');
            _.each(options.expectedTopics, function (topic, index) {
                var currentCard = topicCards.eq(index);
                expect(currentCard.text()).toMatch(topic.name);
                expect(currentCard.text()).toMatch(topic.description);
                expect(currentCard.text()).toMatch(topic.team_count + ' Teams');
            });
            // Verify the footer
            expect(topicsView.$('.topics-paging-footer').text())
                .toMatch(new RegExp(options.currentPage + '\\s+\/\\s+' + topicCollection.totalPages));
        };

        it('can render the first of many pages', function () {
            expectHeaderOnPage({firstIndex: 1, lastIndex: 5, totalCount: 6});
            expectViewReflectsState({currentPage: 1, totalPages: 2, expectedTopics: initialTopics});
        });

        it('can render the only page', function () {
            initialTopics = generateTopics(1, 1);
            topicCollection.set(
                {
                    "count": 1,
                    "num_pages": 1,
                    "current_page": 1,
                    "start": 0,
                    "results": initialTopics
                },
                {parse: true}
            );
            expectHeaderOnPage({totalCount: 1}, true);
            expectViewReflectsState({currentPage: 1, totalPages: 1, expectedTopics: initialTopics});
        });

        it('can change to the next page', function () {
            var requests = AjaxHelpers.requests(this),
                newTopics = generateTopics(1, 1);
            expectHeaderOnPage({firstIndex: 1, lastIndex: 5, totalCount: 6});
            expectViewReflectsState({currentPage: 1, totalPages: 2, expectedTopics: initialTopics});
            expect(requests.length).toBe(0);
            topicsView.$('.next-page-link').click();
            expect(requests.length).toBe(1);
            AjaxHelpers.respondWithJson(requests, {
                "count": 6,
                "num_pages": 2,
                "current_page": 2,
                "start": 5,
                "results": newTopics
            });
            expectHeaderOnPage({firstIndex: 6, lastIndex: 6, totalCount: 6});
            expectViewReflectsState({currentPage: 2, totalPages: 2, expectedTopics: newTopics});
        });

        it('can change to the previous page', function () {
            var requests = AjaxHelpers.requests(this);
            initialTopics = generateTopics(1, 1);
            topicCollection.set(
                {
                    "count": 6,
                    "num_pages": 2,
                    "current_page": 2,
                    "start": 5,
                    "results": initialTopics
                },
                {parse: true}
            );
            expectHeaderOnPage({firstIndex: 6, lastIndex: 6, totalCount: 6});
            expectViewReflectsState({currentPage: 2, totalPages: 2});
            topicsView.$('.previous-page-link').click();
            var previousPageTopics = generateTopics(1, 5);
            AjaxHelpers.respondWithJson(requests, {
                "count": 6,
                "num_pages": 2,
                "current_page": 1,
                "start": 0,
                "results": previousPageTopics
            });
            expectHeaderOnPage({firstIndex: 1, lastIndex: 5, totalCount: 6});
            expectViewReflectsState({currentPage: 1, totalPages: 2});
        });
    });
});

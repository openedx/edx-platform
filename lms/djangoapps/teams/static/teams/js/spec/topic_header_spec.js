define(['teams/js/views/topic_header', 'teams/js/collections/topic'],
       function (TopicHeader, TopicCollection) {
           'use strict';
           describe('topic list view header', function () {
               var topicHeader,
                   courseId = 'testX/test/test_20XX',
                   newCollection = function (size, perPage) {
                       var results = _.map(_.range(size), function (i) {
                           return {
                               "description": "description " + i,
                               "name": "topic " + i,
                               "id": "id " + i
                           };
                       });
                       var collection = new TopicCollection(
                           {results: _.first(results, perPage)},
                           {course_id: courseId, parse: true}
                       );
                       collection.start = 0;
                       collection.totalCount = results.length;
                       return collection;
                   };

               it('can load templates', function () {
                   topicHeader = new TopicHeader({
                       collection: new TopicCollection({results: []}, {course_id: courseId})
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
           });
});

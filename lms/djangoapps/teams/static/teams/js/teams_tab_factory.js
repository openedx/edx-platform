;(function (define) {
    'use strict';

    define(['jquery', 'teams/js/views/teams_tab', 'teams/js/collections/topic'],
        function ($, TeamsTabView, TopicCollection) {
            return function (topics, topics_url) {
                var topicCollection = new TopicCollection(topics, {url: topics_url, parse: true});
                topicCollection.bootstrap();
                var view = new TeamsTabView({
                    el: $('.teams-content'),
                    topicCollection: topicCollection
                });
                view.render();
            };
        });
}).call(this, define || RequireJS.define);

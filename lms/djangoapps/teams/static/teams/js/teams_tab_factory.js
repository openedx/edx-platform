;(function (define) {
    'use strict';

    define(['jquery', 'teams/js/views/teams_tab'],
        function ($, TeamsTabView) {
            return function (options) {
                var teamsTab = new TeamsTabView(_.extend(options, {el: $('.teams-content')}));
                teamsTab.render();
                Backbone.history.start();
            };
        });
}).call(this, define || RequireJS.define);

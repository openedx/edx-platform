;(function (define) {
    'use strict';

    define(['jquery', 'underscore', 'backbone', 'teams/js/views/teams_tab'],
        function ($, _, Backbone, TeamsTabView) {
            return function (options) {
                var teamsTab = new TeamsTabView({
                    el: $('.teams-content'),
                    context: options
                });
                teamsTab.start();
            };
        });
}).call(this, define || RequireJS.define);

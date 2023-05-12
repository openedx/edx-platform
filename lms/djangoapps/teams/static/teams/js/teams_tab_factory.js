(function(define) {
    'use strict';

    define(['jquery', 'teams/js/views/teams_tab'],
        function($, TeamsTabView) {
            return function(options) {
                var teamsTab = new TeamsTabView({
                    el: $('.teams-content'),
                    context: options,
                    viewLabel: gettext('Teams')
                });
                teamsTab.start();
            };
        });
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);

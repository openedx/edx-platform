;(function (define) {
    'use strict';

    define(['jquery','teams/js/views/teams_tab'],
        function ($, TeamsTabView) {
            return function () {
                var view = new TeamsTabView({
                    el: $('.teams-content')
                });
                view.render();
            };
        });
}).call(this, define || RequireJS.define);

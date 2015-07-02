;(function (define) {
    'use strict';

    define(['jquery','teams/js/views/teams_tab'],
        function ($, TeamsTabView) {
            return function (element) {
                var view = new TeamsTabView({
                    el: element
                });
                view.render();
            };
        });
}).call(this, define || RequireJS.define);

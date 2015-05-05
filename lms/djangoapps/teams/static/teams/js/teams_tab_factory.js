;(function (define, undefined) {
    'use strict';

    // Hack: how can we set this correctly so that RequireJS.text can see it?
    window.define = define;

    define(['jquery', 'teams/js/views/teams_tab'],
        function ($, TeamsTabView) {
            return function () {
                var view = new TeamsTabView({
                    el: $('.team-tab-content')
                });
                view.render();
            };
        });
}).call(this, define || RequireJS.define);

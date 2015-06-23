define(['jquery','teams/js/views/teams_tab'],
   function ($, TeamsTabView) {
        'use strict';
        return function () {
            var view = new TeamsTabView({
                el: $('.teams-content')
            });
            view.render();
        };
    });

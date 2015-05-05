;(function (define, undefined) {
    'use strict';
    define(['backbone', 'text!teams/js/templates/teams_tab.underscore'],
        function (Backbone, teamsTabTemplate) {
            var TeamTabView = Backbone.View.extend({
                render: function() {
                    this.$el.html(_.template(teamsTabTemplate, {

                    }));
                    return this;
                }
            });

            return TeamTabView;
        });
}).call(this, define || RequireJS.define);

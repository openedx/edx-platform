;(function (define) {
    'use strict';

    define(['backbone', 'underscore', 'text!teams/templates/teams-tab.underscore'],
        function (Backbone, _, teamsTabTemplate) {
            var TeamTabView = Backbone.View.extend({
                render: function() {
                    this.$el.html(_.template(teamsTabTemplate, {}));
                }
            });

            return TeamTabView;
        });
}).call(this, define || RequireJS.define);

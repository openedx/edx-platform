;(function (define) {
    'use strict';

    define(['backbone',
            'underscore',
            'gettext',
            'js/components/header/views/header',
            'js/components/header/models/header',
            'text!teams/templates/teams-tab.underscore'],
           function (Backbone, _, gettext, HeaderView, HeaderModel, teamsTabTemplate) {
               var TeamTabView = Backbone.View.extend({
                   initialize: function() {
                       this.headerModel = new HeaderModel({
                           description: gettext("Course teams are organized into topics created by course instructors. Try to join others in an existing team before you decide to create a new team!"),
                           title: gettext("Teams")
                       });
                       this.headerView = new HeaderView({
                           model: this.headerModel
                       });
                   },

                   render: function() {
                       this.$el.html(_.template(teamsTabTemplate, {}));
                       this.$el.prepend(this.headerView.$el);
                       this.headerView.render();
                   }
               });

               return TeamTabView;
           });
}).call(this, define || RequireJS.define);

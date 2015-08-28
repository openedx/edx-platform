;(function (define) {
    'use strict';

    define(['backbone',
            'underscore',
            'gettext',
            'teams/js/views/team_utils',
            'text!teams/templates/instructor-toolbar.underscore'],
        function (Backbone, _, gettext, TeamUtils, instructorToolbarTemplate) {
            return Backbone.View.extend({

                events: {
                    "click": "stubbedAlert"
                },

                initialize: function(options) {
                    this.teamEvents = options.teamEvents;
                    this.template = _.template(instructorToolbarTemplate);
                    this.courseID = options.courseID;
                    this.maxTeamSize = options.maxTeamSize;
                    this.currentUsername = options.currentUsername;
                    this.teamMembershipsUrl = options.teamMembershipsUrl;
                    this.showEditButton = options.showEditButton;
                    this.topicID = options.topicID;
                    _.bindAll(this, 'render', 'stubbedAlert');
                    this.listenTo(this.model, "change", this.render);
                },

                render: function() {
                    var view = this;
                    view.$el.html(view.template);
                    return view;
                },

                stubbedAlert: function() {
                    alert("You clicked the button!");
                }
            });
        });
}).call(this, define || RequireJS.define);

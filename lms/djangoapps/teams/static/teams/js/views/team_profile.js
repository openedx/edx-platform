/**
 * View for an individual team.
 */
;(function (define) {
    'use strict';
    define(['backbone', 'underscore', 'gettext', 'teams/js/views/team_discussion',
            'text!teams/templates/team-profile.underscore'],
        function (Backbone, _, gettext, TeamDiscussionView, teamTemplate) {
            var TeamProfileView = Backbone.View.extend({
                initialize: function (options) {
                    this.courseID = options.courseID;
                    this.discussionTopicID = this.model.get('discussion_topic_id');
                    this.readOnly = options.readOnly;
                },

                render: function () {
                    this.$el.html(_.template(teamTemplate, {
                        courseID: this.courseID,
                        discussionTopicID: this.discussionTopicID,
                        readOnly: this.readOnly
                    }));
                    this.discussionView = new TeamDiscussionView({
                        el: this.$('.discussion-module')
                    });
                    this.discussionView.render();
                    return this;
                }
            });

            return TeamProfileView;
        });
}).call(this, define || RequireJS.define);

/**
 * View for an individual team.
 */
;(function (define) {
    'use strict';
    define(['backbone', 'underscore', 'gettext', 'teams/js/views/team_discussion',
            'text!teams/templates/team-profile.underscore'],
        function (Backbone, _, gettext, TeamDiscussionView, team_template) {
            var TeamProfileView = Backbone.View.extend({
                initialize: function (options) {
                    this.courseID = options.courseID;
                    this.discussionTopicID = this.model.get('discussion_topic_id');
                    // TODO: remove this once the discussion ID works from the server!
                    if (!this.discussionTopicID) {
                        this.discussionTopicID = '7065c53dcac4fe469fb66997da075f9af7e760a9';
                    }
                },

                render: function () {
                    this.$el.html(_.template(team_template, {
                        courseID: this.courseID,
                        discussionTopicID: this.discussionTopicID
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

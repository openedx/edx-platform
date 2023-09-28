/* globals DiscussionThreadView */
(function(define) {
    'use strict';

    define([
        'underscore',
        'jquery',
        'backbone',
        'gettext',
        'URI',
        'edx-ui-toolkit/js/utils/html-utils',
        'common/js/components/utils/view_utils',
        'common/js/discussion/discussion',
        'common/js/discussion/utils',
        'common/js/discussion/views/discussion_thread_profile_view',
        'text!discussion/templates/user-profile.underscore',
        'common/js/discussion/views/discussion_thread_list_view'
    ],
    function(_, $, Backbone, gettext, URI, HtmlUtils, ViewUtils, Discussion, DiscussionUtil,
        DiscussionThreadProfileView, userProfileTemplate, DiscussionThreadListView) {
        var DiscussionUserProfileView = Backbone.View.extend({
            events: {
                'click .all-posts-btn': 'navigateToAllThreads'
            },

            initialize: function(options) {
                this.courseSettings = options.courseSettings;
                this.discussion = options.discussion;
                this.mode = 'user';
                this.listenTo(this.model, 'change', this.render);
            },

            render: function() {
                HtmlUtils.setHtml(this.$el,
                    HtmlUtils.template(userProfileTemplate)({})
                );

                this.discussionThreadListView = new DiscussionThreadListView({
                    collection: this.discussion,
                    el: this.$('.inline-threads'),
                    courseSettings: this.courseSettings,
                    mode: this.mode,
                    // @TODO: On the profile page, thread read state for the viewing user is not accessible via API.
                    // Fix this when the Discussions API can support this query. Until then, hide read state.
                    hideReadState: true
                }).render();

                this.discussionThreadListView.on('thread:selected', _.bind(this.navigateToThread, this));

                return this;
            },

            navigateToThread: function(threadId) {
                var thread = this.discussion.get(threadId);
                this.threadView = new DiscussionThreadView({
                    el: this.$('.forum-content'),
                    model: thread,
                    mode: 'inline',
                    courseSettings: this.courseSettings
                });
                this.threadView.render();
                this.listenTo(this.threadView.showView, 'thread:_delete', this.navigateToAllThreads);
                this.discussionThreadListView.$el.addClass('is-hidden');
                this.$('.inline-thread').removeClass('is-hidden');
            },

            navigateToAllThreads: function() {
                // Hide the inline thread section
                this.$('.inline-thread').addClass('is-hidden');

                // Delete the thread view
                this.threadView.$el.empty().off();
                this.threadView.stopListening();
                this.threadView = null;

                // Show the thread list view
                this.discussionThreadListView.$el.removeClass('is-hidden');

                // Set focus to thread list item that was saved as active
                this.discussionThreadListView.$('.is-active').focus();
            }
        });

        return DiscussionUserProfileView;
    });
}).call(this, define || RequireJS.define);

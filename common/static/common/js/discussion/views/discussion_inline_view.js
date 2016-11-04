/* globals
    _, Backbone, Content, Discussion, DiscussionUtil, DiscussionUser, DiscussionCourseSettings,
    DiscussionThreadListView, NewPostView
*/

(function() {
    'use strict';

    this.DiscussionInlineView = Backbone.View.extend({
        events: {
            'click .discussion-show': 'toggleDiscussion'
        },

        initialize: function(options) {
            this.$el = options.el;
            this.toggleDiscussionBtn = this.$('.discussion-show');
        },

        loadPage: function($elem, error) {
            var discussionId = this.$el.data('discussion-id'),
                url = DiscussionUtil.urlFor('retrieve_discussion', discussionId) + ('?page=' + this.page),
                self = this;

            DiscussionUtil.safeAjax({
                $elem: this.$el,
                $loading: this.$el,
                takeFocus: true,
                url: url,
                type: 'GET',
                dataType: 'json',
                success: function(response, textStatus) {
                    self.renderDiscussion(self.$el, response, textStatus, discussionId);
                },
                error: error
            });
        },

        renderDiscussion: function($elem, response, textStatus, discussionId) {
            var $discussion,
                user = new DiscussionUser(response.user_info),
                self = this;

            $elem.focus();

            window.user = user;
            DiscussionUtil.setUser(user);
            Content.loadContentInfos(response.annotated_content_info);
            DiscussionUtil.loadRoles(response.roles);

            this.course_settings = new DiscussionCourseSettings(response.course_settings);

            this.discussion = new Discussion();
            this.discussion.reset(response.discussion_data, {
                silent: false
            });

            $discussion = _.template($('#inline-discussion-template').html())({
                threads: response.discussion_data,
                read_only: this.readOnly,
                discussionId: discussionId
            });

            if (this.$('section.discussion').length) {
                this.$('section.discussion').replaceWith($discussion);
            } else {
                this.$el.append($discussion);
            }

            this.threadListView = new DiscussionThreadListView({
                el: this.$('section.threads'),
                collection: self.discussion,
                courseSettings: self.course_settings
            });

            this.threadListView.render();

            DiscussionUtil.bulkUpdateContentInfo(window.$$annotated_content_info);

            this.newPostForm = this.$el.find('.new-post-article');

            this.newPostView = new NewPostView({
                el: this.newPostForm,
                collection: this.discussion,
                course_settings: this.course_settings,
                topicId: discussionId,
                is_commentable_cohorted: response.is_commentable_cohorted
            });

            this.newPostView.render();

            this.listenTo(this.newPostView, 'newPost:cancel', this.hideNewPost);
            this.discussion.on('add', this.addThread);

            this.retrieved = true;
            this.showed = true;

            if (this.isWaitingOnNewPost) {
                this.newPostForm.show().focus();
            }
        },

        toggleDiscussion: function() {
            var self = this;

            if (this.showed) {
                this.hideDiscussion();
            } else {
                this.toggleDiscussionBtn.addClass('shown');
                this.toggleDiscussionBtn.find('.button-text').html(gettext('Hide Discussion'));
                if (this.retrieved) {
                    this.$('section.discussion').slideDown();
                    this.showed = true;
                } else {
                    this.loadPage(this.$el, function() {
                        self.hideDiscussion();
                        DiscussionUtil.discussionAlert(
                            gettext('Sorry'),
                            gettext('We had some trouble loading the discussion. Please try again.')
                        );
                    });
                }
            }
        },

        hideDiscussion: function() {
            this.$('section.discussion').slideUp();
            this.toggleDiscussionBtn.removeClass('shown');
            this.toggleDiscussionBtn.find('.button-text').html(gettext('Show Discussion'));
            this.showed = false;
        }
    });
}).call(window);

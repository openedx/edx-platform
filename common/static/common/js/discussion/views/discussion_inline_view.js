/* globals
 _, Backbone, Content, Discussion, DiscussionUtil, DiscussionUser, DiscussionCourseSettings,
 DiscussionThreadListView, DiscussionThreadView, NewPostView
 */

(function() {
    'use strict';

    this.DiscussionInlineView = Backbone.View.extend({
        events: {
            'click .discussion-show': 'toggleDiscussion',
            'keydown .discussion-show': function(event) {
                return DiscussionUtil.activateOnSpace(event, this.toggleDiscussion);
            },
            'click .new-post-btn': 'toggleNewPost',
            'click .all-posts-btn': 'navigateToAllPosts',
            'keydown .new-post-btn': function(event) {
                return DiscussionUtil.activateOnSpace(event, this.toggleNewPost);
            }
        },

        page_re: /\?discussion_page=(\d+)/,

        initialize: function(options) {
            var match;

            this.$el = options.el;
            this.showByDefault = options.showByDefault || false;
            this.toggleDiscussionBtn = this.$('.discussion-show');
            this.newPostForm = this.$el.find('.new-post-article');
            this.listenTo(this.newPostView, 'newPost:cancel', this.hideNewPost);
            this.listenTo(this.model, 'change', this.render);

            match = this.page_re.exec(window.location.href);
            if (match) {
                this.page = parseInt(match[1], 10);
            } else {
                this.page = 1;
            }

            // By default the view is displayed in a hidden state. If you want it to be shown by default (e.g. in Teams)
            // pass showByDefault as an option. This code will open it on initialization.
            if (this.showByDefault) {
                this.toggleDiscussion();
            }
        },

        loadDiscussions: function($elem, error) {
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
                el: this.$('.inline-threads'),
                collection: self.discussion,
                courseSettings: self.course_settings
            });

            this.threadListView.render();

            this.threadListView.on('thread:selected', _.bind(this.navigateToThread, this));

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

            this.renderPagination(response.num_pages);

            if (this.isWaitingOnNewPost) {
                this.newPostForm.show().focus();
            }

            // Hide the thread view initially
            this.$('.inline-thread').addClass('is-hidden');
        },

        renderPagination: function(numPages) {
            var pageUrl, pagination, params;
            pageUrl = function(number) {
                return '?discussion_page=' + number;
            };
            params = DiscussionUtil.getPaginationParams(this.page, numPages, pageUrl);
            pagination = _.template($('#pagination-template').html())(params);
            return this.$('section.discussion-pagination').html(pagination);
        },

        navigateToThread: function(threadId) {
            var thread = this.discussion.get(threadId);
            this.threadView = new DiscussionThreadView({
                el: this.$('.forum-content'),
                model: thread,
                mode: 'tab',
                course_settings: this.course_settings
            });
            this.threadView.render();
            this.threadListView.$el.addClass('is-hidden');
            this.$('.inline-thread').removeClass('is-hidden');
        },

        navigateToAllPosts: function() {
            // Hide the inline thread section
            this.$('.inline-thread').addClass('is-hidden');

            // Delete the thread view
            this.threadView.$el.empty().off();
            this.threadView.stopListening();
            this.threadView = null;

            // Show the thread list view
            this.threadListView.$el.removeClass('is-hidden');
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
                    this.loadDiscussions(this.$el, function() {
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
        },

        toggleNewPost: function(event) {
            event.preventDefault();
            if (!this.newPostForm) {
                this.toggleDiscussion();
                this.isWaitingOnNewPost = true;
                return;
            }
            if (this.showed) {
                this.newPostForm.slideDown(300);
            } else {
                this.newPostForm.show().focus();
            }
            this.toggleDiscussionBtn.addClass('shown');
            this.toggleDiscussionBtn.find('.button-text').html(gettext('Hide Discussion'));
            this.$('section.discussion').slideDown();
            this.showed = true;
        },

        hideNewPost: function() {
            return this.newPostForm.slideUp(300);
        }
    });
}).call(window);

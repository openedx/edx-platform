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
            keydown: 'handleKeydown',
            'keydown .new-post-btn': function(event) {
                return DiscussionUtil.activateOnSpace(event, this.toggleNewPost);
            }
        },

        page_re: /\?discussion_page=(\d+)/,

        initialize: function(options) {
            var match;
            this.$el = options.el;
            this.readOnly = options.readOnly;
            this.showByDefault = options.showByDefault || false;
            this.toggleDiscussionBtn = this.$('.discussion-show');
            this.listenTo(this.model, 'change', this.render);
            this.escKey = 27;

            if (options.startHeader !== undefined) {
                this.startHeader = options.startHeader;
            } else {
                this.startHeader = 4; // Start the header levels at H<startHeader>
            }

            match = this.page_re.exec(window.location.href);
            if (match) {
                this.page = parseInt(match[1], 10);
            } else {
                this.page = 1;
            }

            this.defaultSortKey = 'activity';
            this.defaultSortOrder = 'desc';

            // By default the view is displayed in a hidden state. If you want it to be shown by default (e.g. in Teams)
            // pass showByDefault as an option. This code will open it on initialization.
            if (this.showByDefault) {
                this.toggleDiscussion();
            }
        },

        loadDiscussions: function($elem, error) {
            var discussionId = this.$el.data('discussion-id'),
                url = DiscussionUtil.urlFor('retrieve_discussion', discussionId) + ('?page=' + this.page)
                    + ('&sort_key=' + this.defaultSortKey) + ('&sort_order=' + this.defaultSortOrder),
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
            var discussionHtml,
                user = new DiscussionUser(response.user_info),
                self = this;
            $elem.focus();

            window.user = user;
            DiscussionUtil.setUser(user);
            Content.loadContentInfos(response.annotated_content_info);
            DiscussionUtil.loadRoles(response.roles);

            this.courseSettings = new DiscussionCourseSettings(response.course_settings);

            this.discussion = new Discussion(undefined, {pages: response.num_pages});
            this.discussion.reset(response.discussion_data, {
                silent: false
            });

            discussionHtml = edx.HtmlUtils.template($('#inline-discussion-template').html())({
                threads: response.discussion_data,
                read_only: this.readOnly,
                discussionId: discussionId
            });

            if (this.$('section.discussion').length) {
                edx.HtmlUtils.setHtml(this.$el, discussionHtml);
                this.$('section.discussion').replaceWith(edx.HtmlUtils.ensureHtml(discussionHtml).toString());
            } else {
                edx.HtmlUtils.append(this.$el, discussionHtml);
            }

            this.threadListView = new DiscussionThreadListView({
                el: this.$('.inline-threads'),
                collection: self.discussion,
                courseSettings: self.courseSettings
            });

            this.threadListView.render();

            this.threadListView.on('thread:selected', _.bind(this.navigateToThread, this));

            DiscussionUtil.bulkUpdateContentInfo(window.$$annotated_content_info);

            this.newPostForm = this.$el.find('.new-post-article');

            this.newPostView = new NewPostView({
                el: this.newPostForm,
                collection: this.discussion,
                course_settings: this.courseSettings,
                topicId: discussionId,
                startHeader: this.startHeader,
                is_commentable_cohorted: response.is_commentable_cohorted
            });

            this.newPostView.render();

            this.listenTo(this.newPostView, 'newPost:createPost', this.onNewPostCreated);
            this.listenTo(this.newPostView, 'newPost:cancel', this.hideNewPost);
            this.discussion.on('add', this.addThread);

            this.retrieved = true;
            this.showed = true;

            if (this.isWaitingOnNewPost) {
                this.newPostForm.removeClass('is-hidden').focus();
            }

            // Hide the thread view initially
            this.$('.inline-thread').addClass('is-hidden');
        },

        navigateToThread: function(threadId) {
            var thread = this.discussion.get(threadId);
            this.threadView = new DiscussionThreadView({
                el: this.$('.forum-content'),
                model: thread,
                mode: 'inline',
                startHeader: this.startHeader,
                courseSettings: this.courseSettings
            });
            this.threadView.render();
            this.listenTo(this.threadView.showView, 'thread:_delete', this.navigateToAllPosts);
            this.threadListView.$el.addClass('is-hidden');
            this.$('.inline-thread').removeClass('is-hidden');
        },

        navigateToAllPosts: function() {
            // Hide the inline thread section
            this.$('.inline-thread').addClass('is-hidden');

            // Delete the thread view
            if (this.threadView) {
                this.threadView.$el.empty().off();
                this.threadView.stopListening();
                this.threadView = null;
            }

            // Show the thread list view
            this.threadListView.$el.removeClass('is-hidden');

            // Set focus to thread list item that was saved as active
            this.threadListView.$('.is-active').focus();
        },

        toggleDiscussion: function() {
            var self = this;

            if (this.showed) {
                this.hideDiscussion();
            } else {
                this.toggleDiscussionBtn.addClass('shown');
                this.toggleDiscussionBtn.find('.button-text').text(gettext('Hide Discussion'));
                if (this.retrieved) {
                    this.$('section.discussion').removeClass('is-hidden');
                    this.showed = true;
                } else {
                    this.loadDiscussions(this.$el, function() {
                        self.hideDiscussion();
                        DiscussionUtil.discussionAlert(
                            gettext('Error'),
                            gettext('This discussion could not be loaded. Refresh the page and try again.')
                        );
                    });
                }
            }
            this.toggleDiscussionBtn.focus();
        },

        hideDiscussion: function() {
            this.$('section.discussion').addClass('is-hidden');
            this.toggleDiscussionBtn.removeClass('shown');
            this.toggleDiscussionBtn.find('.button-text').text(gettext('Show Discussion'));
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
                this.$('section.discussion').find('.inline-discussion-thread-container').addClass('is-hidden');
                this.$('section.discussion').find('.add_post_btn_container').addClass('is-hidden');
                this.newPostForm.removeClass('is-hidden');
            }
            this.newPostView.$el.removeClass('is-hidden');
            this.toggleDiscussionBtn.addClass('shown');
            this.toggleDiscussionBtn.find('.button-text').text(gettext('Hide Discussion'));
            this.showed = true;
        },

        onNewPostCreated: function() {
            this.navigateToAllPosts();
            this.hideNewPost();
        },

        hideNewPost: function() {
            this.$('section.discussion').find('.inline-discussion-thread-container').removeClass('is-hidden');
            this.$('section.discussion').find('.add_post_btn_container')
                .removeClass('is-hidden')
                .focus();
            this.newPostForm.addClass('is-hidden');
        },

        handleKeydown: function(event) {
            var keyCode = event.keyCode;
            if (keyCode === this.escKey) {
                this.$('section.discussion').find('.cancel').trigger('click');
            }
        }
    });
}).call(window);

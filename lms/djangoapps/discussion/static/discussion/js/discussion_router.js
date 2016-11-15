(function(define) {
    'use strict';

    define(
        [
            'underscore',
            'backbone',
            'common/js/discussion/utils',
            'common/js/discussion/views/discussion_thread_list_view',
            'common/js/discussion/views/discussion_thread_view'
        ],
        function(_, Backbone, DiscussionUtil, DiscussionThreadListView, DiscussionThreadView) {
            var DiscussionRouter = Backbone.Router.extend({
                routes: {
                    '': 'allThreads',
                    ':forum_name/threads/:thread_id': 'showThread'
                },

                initialize: function(options) {
                    Backbone.Router.prototype.initialize.call(this);
                    _.bindAll(this, 'allThreads', 'showThread');
                    this.courseId = options.courseId;
                    this.discussion = options.discussion;
                    this.course_settings = options.courseSettings;
                    this.newPostView = options.newPostView;
                    this.nav = new DiscussionThreadListView({
                        collection: this.discussion,
                        el: $('.forum-nav'),
                        courseSettings: this.course_settings
                    });
                    this.nav.render();
                },

                start: function() {
                    var self = this,
                        $newPostButton = $('.new-post-btn');
                    this.listenTo(this.newPostView, 'newPost:cancel', this.hideNewPost);
                    $newPostButton.bind('click', _.bind(this.showNewPost, this));
                    $newPostButton.bind('keydown', function(event) {
                        DiscussionUtil.activateOnSpace(event, self.showNewPost);
                    });

                    // Automatically navigate when the user selects threads
                    this.nav.on('thread:selected', _.bind(this.navigateToThread, this));
                    this.nav.on('thread:removed', _.bind(this.navigateToAllThreads, this));
                    this.nav.on('threads:rendered', _.bind(this.setActiveThread, this));
                    this.nav.on('thread:created', _.bind(this.navigateToThread, this));

                    Backbone.history.start({
                        pushState: true,
                        root: '/courses/' + this.courseId + '/discussion/forum/'
                    });
                },

                stop: function() {
                    Backbone.history.stop();
                },

                allThreads: function() {
                    this.nav.updateSidebar();
                    return this.nav.goHome();
                },

                setActiveThread: function() {
                    if (this.thread) {
                        return this.nav.setActiveThread(this.thread.get('id'));
                    } else {
                        return this.nav.goHome;
                    }
                },

                showThread: function(forumName, threadId) {
                    this.thread = this.discussion.get(threadId);
                    this.thread.set('unread_comments_count', 0);
                    this.thread.set('read', true);
                    this.setActiveThread();
                    return this.showMain();
                },

                showMain: function() {
                    var self = this;
                    if (this.main) {
                        this.main.cleanup();
                        this.main.undelegateEvents();
                    }
                    if (!($('.forum-content').is(':visible'))) {
                        $('.forum-content').fadeIn();
                    }
                    if (this.newPostView.$el.is(':visible')) {
                        this.newPostView.$el.fadeOut();
                    }
                    this.main = new DiscussionThreadView({
                        el: $('.forum-content'),
                        model: this.thread,
                        mode: 'tab',
                        course_settings: this.course_settings
                    });
                    this.main.render();
                    this.main.on('thread:responses:rendered', function() {
                        return self.nav.updateSidebar();
                    });
                    return this.thread.on('thread:thread_type_updated', this.showMain);
                },

                navigateToThread: function(threadId) {
                    var thread;
                    thread = this.discussion.get(threadId);
                    return this.navigate('' + (thread.get('commentable_id')) + '/threads/' + threadId, {
                        trigger: true
                    });
                },

                navigateToAllThreads: function() {
                    return this.navigate('', {
                        trigger: true
                    });
                },

                showNewPost: function() {
                    var self = this;
                    return $('.forum-content').fadeOut({
                        duration: 200,
                        complete: function() {
                            return self.newPostView.$el.fadeIn(200).focus();
                        }
                    });
                },

                hideNewPost: function() {
                    return this.newPostView.$el.fadeOut({
                        duration: 200,
                        complete: function() {
                            return $('.forum-content').fadeIn(200).find('.thread-wrapper')
                                .focus();
                        }
                    });
                }
            });

            return DiscussionRouter;
        });
}).call(this, define || RequireJS.define);

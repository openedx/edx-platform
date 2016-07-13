(function(define) {
    'use strict';

    define(
        [
            'jquery',
            'backbone',
            'discussion/js/discussion_router',
            'discussion/js/views/discussion_fake_breadcrumbs',
            'common/js/discussion/views/new_post_view'
        ],
        function($, Backbone, DiscussionRouter, DiscussionFakeBreadcrumbs, NewPostView) {
            return function(options) {
                var userInfo = options.user_info,
                    sortPreference = options.sort_preference,
                    threads = options.threads,
                    threadPages = options.thread_pages,
                    contentInfo = options.content_info,
                    user = new window.DiscussionUser(userInfo),
                    discussion,
                    courseSettings,
                    newPostView,
                    router,
                    breadcrumbs,
                    BreadcrumbsModel;

                // TODO: Perhaps eliminate usage of global variables when possible
                window.DiscussionUtil.loadRoles(options.roles);
                window.$$course_id = options.courseId;
                window.courseName = options.course_name;
                window.DiscussionUtil.setUser(user);
                window.user = user;
                window.Content.loadContentInfos(contentInfo);

                discussion = new window.Discussion(threads, {pages: threadPages, sort: sortPreference});
                courseSettings = new window.DiscussionCourseSettings(options.course_settings);

                // Create the new post view
                newPostView = new NewPostView({
                    el: $('.new-post-article'),
                    collection: discussion,
                    course_settings: courseSettings,
                    mode: 'tab'
                });
                newPostView.render();

                // Set up the router to manage the page's history
                router = new DiscussionRouter({
                    courseId: options.courseId,
                    discussion: discussion,
                    courseSettings: courseSettings,
                    newPostView: newPostView
                });
                router.start();

                BreadcrumbsModel = Backbone.Model.extend({
                    defaults: {
                        contents: [],
                    }
                });

                breadcrumbs = new DiscussionFakeBreadcrumbs({
                    el: $('.has-breadcrumbs'),
                    model: new BreadcrumbsModel(),
                    events: {
                        'click .all-topics': function(event) {
                            event.preventDefault();
                            this.model.set('contents', []);
                            router.navigate('', {trigger: true});
                            router.nav.selectTopic($('.forum-nav-browse-menu-all'));
                        }
                    }
                }).render();

                // Add new breadcrumbs when the user selects topics
                router.nav.on('topic:selected', function(topic) {
                    breadcrumbs.model.set('contents', topic);
                });
            };
        });
}).call(this, define || RequireJS.define);

(function(define) {
    'use strict';

    define(
        [
            'jquery',
            'backbone',
            'discussion/js/discussion_router',
            'discussion/js/views/discussion_fake_breadcrumbs',
            'discussion/js/views/discussion_search_view',
            'common/js/discussion/views/new_post_view'
        ],
        function($, Backbone, DiscussionRouter, DiscussionFakeBreadcrumbs, DiscussionSearchView, NewPostView) {
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
                    BreadcrumbsModel,
                    searchBox,
                    routerEvents;

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

                // Initialize and render search box
                searchBox = new DiscussionSearchView({
                    el: $('.forum-search'),
                    threadListView: router.nav
                }).render();

                // Initialize and render breadcrumbs
                BreadcrumbsModel = Backbone.Model.extend({
                    defaults: {
                        contents: []
                    }
                });

                breadcrumbs = new DiscussionFakeBreadcrumbs({
                    el: $('.has-breadcrumbs'),
                    model: new BreadcrumbsModel(),
                    events: {
                        'click .all-topics': function(event) {
                            event.preventDefault();
                            searchBox.clearSearch();
                            this.model.set('contents', []);
                            router.navigate('', {trigger: true});
                            router.nav.toggleBrowseMenu(event);
                        }
                    }
                }).render();

                routerEvents = {
                    // Add new breadcrumbs and clear search box when the user selects topics
                    'topic:selected': function(topic) {
                        breadcrumbs.model.set('contents', topic);
                    },
                    // Clear search box when a thread is selected
                    'thread:selected': function() {
                        searchBox.clearSearch();
                    },
                    // Add 'Search Results' to breadcrumbs when user searches
                    'search:initiated': function() {
                        breadcrumbs.model.set('contents', ['Search Results']);
                    }
                };

                Object.keys(routerEvents).forEach(function(key) {
                    router.nav.on(key, routerEvents[key]);
                });
            };
        });
}).call(this, define || RequireJS.define);

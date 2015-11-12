;(function (define) {
    'use strict';

    define(['backbone',
        'underscore',
        'gettext',
        'js/dashboard/routers/dashboard_router',
        'js/dashboard/collection/courses',
        'js/dashboard/views/course_list_view',
        'js/components/tabbed/views/tabbed_view'
    ], function (Backbone,
                 _,
                 gettext,
                 DashboardRouter,
                 CourseCollection,
                 CourseListView,
                 TabbedView) {

        var CourseListTabbedView = Backbone.View.extend({

            el: '.wrapper-header-courses',

            tabs: {
                current: {
                    title: gettext('Current'),
                    url: '/courses/current',
                    index: 0
                },
                archived: {
                    title: gettext('Archived'),
                    url: '/courses/archived',
                    index: 1
                }
            },

            initialize: function (currentCourses, archivedCourses, templateSettings) {

                var router = new DashboardRouter(),
                    dispatcher = _.clone(Backbone.Events),
                    settings = templateSettings;

                dispatcher.listenTo(router, 'goToTab', _.bind(function (tab) {
                    this.goToTab(tab);
                }, this));

                this.setElement(this.el);

                this.currentCourseListView = new CourseListView({
                    collection: new CourseCollection(currentCourses),
                    settings: settings
                });
                this.archivedCourseListView = new CourseListView({
                    collection: new CourseCollection(archivedCourses),
                    settings: settings,
                    is_archived: true
                });

                this.mainView = new TabbedView({
                    tabs: [{
                        title: this.tabs.current.title,
                        url: this.tabs.current.url,
                        view: this.currentCourseListView
                    }, {
                        title: this.tabs.archived.title,
                        url: this.tabs.archived.url,
                        view: this.archivedCourseListView
                    }],
                    router: router
                });

                Backbone.history.start();
            },

            render: function () {
                this.mainView.setElement(this.el).render();

                return this;
            },

            /**
             * Set up the tabbed view and switch tabs.
             */
            goToTab: function (tab) {

                // Note that `render` should be called first so
                // that the tabbed view's element is set
                // correctly.
                this.render();
                this.mainView.setActiveTab(this.tabs[tab].index);
            }

        });

        return CourseListTabbedView;
    });

}).call(this, define || RequireJS.define);

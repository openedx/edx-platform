;(function (define) {
    'use strict';

    define(['backbone',
            'underscore',
            'gettext',
            'js/components/header/views/header',
            'js/components/header/models/header',
            'js/components/tabbed/views/tabbed_view',
            'onboarding/js/views/course_list',
            'onboarding/js/models/course_info',
            'onboarding/js/collections/course_info',
            'text!teams/templates/teams_tab.underscore'],
        function (Backbone, _, gettext, HeaderView, HeaderModel, TabbedView,
                  CourseListView, CourseInfo, CourseInfoCollection, TeamsView, TeamCollection, teamsTemplate) {
            var ViewWithHeader = Backbone.View.extend({
                initialize: function (options) {
                    this.header = options.header;
                    this.main = options.main;
                },

                render: function () {
                    this.$el.html(_.template(teamsTemplate));
                    this.$('p.error').hide();
                    this.header.setElement(this.$('.teams-header')).render();
                    this.main.setElement(this.$('.page-content')).render();
                    return this;
                }
            });

            var OnboardingView = Backbone.View.extend({
                initialize: function(options) {
                    var TempTabView, router;
                    // This slightly tedious approach is necessary
                    // to use regular expressions within Backbone
                    // routes, allowing us to capture which tab
                    // name is being routed to
                    router = this.router = new Backbone.Router();
                    _.each([
                        [':default', _.bind(this.routeNotFound, this)],
                    ], function (route) {
                        router.route.apply(router, route);
                    });
                    this.mainView = new CourseListView({
                        collection: this.collection,
                        router: this.router
                    });
                },

                render: function() {
                    this.mainView.setElement(this.$el).render();
                    this.hideWarning();
                    return this;
                },

                /**
                 * Immediately return a promise for the given
                 * object.
                 */
                identityPromise: function (obj) {
                    return new $.Deferred().resolve(obj).promise();
                },

                // Error handling

                routeNotFound: function (route) {
                    this.notFoundError(
                        interpolate(
                            gettext('The page "%(route)s" could not be found.'),
                            {route: route},
                            true
                        )
                    );
                },

                courseNotFound: function (courseId) {
                    this.notFoundError(
                        interpolate(
                            gettext('The course "%(course)s" could not be found.'),
                            {course: courseId},
                            true
                        )
                    );
                },

                /**
                 * Called when the user attempts to navigate to a
                 * route that doesn't exist. "Redirects" back to
                 * the main teams tab, and adds an error message.
                 */
                notFoundError: function (message) {
                    this.router.navigate('teams', {trigger: true});
                    this.showWarning(message);
                },

                showWarning: function (message) {
                    var warningEl = this.$('.warning');
                    warningEl.find('.copy').html('<p>' + message + '</p');
                    warningEl.toggleClass('is-hidden', false);
                },

                hideWarning: function () {
                    this.$('.warning').toggleClass('is-hidden', true);
                }
            });

            return OnboardingView;
        });
}).call(this, define || RequireJS.define);

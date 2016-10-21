/**
 * View that shows the discussion for a team.
 */
(function(define) {
    'use strict';
    define(['backbone', 'underscore', 'gettext', 'common/js/discussion/discussion_module_view'],
        function(Backbone, _, gettext, DiscussionModuleView) {
            var TeamDiscussionView = Backbone.View.extend({
                initialize: function() {
                    window.$$course_id = this.$el.data('course-id');
                },

                render: function() {
                    var discussionModuleView = new DiscussionModuleView({
                        el: this.$el,
                        readOnly: this.$el.data('read-only') === true,
                        context: 'standalone'
                    });
                    discussionModuleView.render();
                    discussionModuleView.loadPage(this.$el);
                    return this;
                }
            });

            return TeamDiscussionView;
        });
}).call(this, define || RequireJS.define);

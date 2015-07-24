;(function (define) {
    'use strict';
    define([
        'onboarding/js/views/course_card',
        'common/js/components/views/paginated_view'
    ], function (CourseCardView, PaginatedView) {
        var CourseListView = PaginatedView.extend({
            type: 'courses',

            initialize: function (options) {
                this.itemViewClass = CourseCardView.extend({router: options.router});
                PaginatedView.prototype.initialize.call(this);
            }
        });
        return CourseListView;
    });
}).call(this, define || RequireJS.define);

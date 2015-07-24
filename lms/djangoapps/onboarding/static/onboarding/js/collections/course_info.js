;(function (define) {
    'use strict';
    define(['backbone', 'common/js/components/collections/paging_collection', 'onboarding/js/models/course_info'],
        function(Backbone, PagingCollection, CourseInfoModel) {
            var CourseInfoCollection = PagingCollection.extend({
                initialize: function(courses, options) {
                    PagingCollection.prototype.initialize.call(this);
                    this.isZeroIndexed = false;
                    this.perPage = options.per_page;
                },

                model: CourseInfoModel
            });
            return CourseInfoCollection;
    });
}).call(this, define || RequireJS.define);

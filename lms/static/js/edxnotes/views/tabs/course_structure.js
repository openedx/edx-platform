;(function (define, undefined) {
'use strict';
define([
    'gettext', 'js/edxnotes/views/subview', 'js/edxnotes/views/tab_view'
], function (gettext, SubView, TabView) {
    var CourseStructureView = TabView.extend({
        SubViewConstructor: SubView.extend({
            id: 'edx-notes-page-course-structure',
            templateName: 'course-structure-item',

            render: function () {
                this.$el.html(this.template({
                    structure: this.collection.getSortedByCourseStructure()
                }));

                return this;
            }
        }),

        getSubView: function () {
            var collection = this.getCollection();
            return new this.SubViewConstructor({
                collection: collection
            });
        },

        tabInfo: {
            name: gettext('Course Strucutre'),
            class_name: 'tab-recent-activity'
        }
    });

    return CourseStructureView;
});
}).call(this, define || RequireJS.define);

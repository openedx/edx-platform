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
                this.preprocess();
                this.$el.html(this.template({
                    structure: this.options.structure
                }));

                return this;
            },

            preprocess: function () {
                var strucutre = this.options.structure;
                this.collection.each(function (note) {
                    chapter_label:
                    for (var i = 0, len = strucutre.length; i < len; i++) {
                        var sections = strucutre[i].sections;
                        for (var j = 0, lenj = sections.length; j < lenj; j++) {
                            var units = sections[j].units;
                            for (var z = 0, lenz = units.length; z < lenz; z++) {
                                var unit = units[z];
                                if (unit.url_name === note.get('unit').url_name) {
                                    unit.notes = unit.notes || [];
                                    unit.notes.push(note);
                                    break chapter_label;
                                }
                            }
                        }
                    }
                }, this);
            }
        }),

        getSubView: function () {
            var collection = this.getCollection();
            return new this.SubViewConstructor({
                structure: this.options.structure,
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

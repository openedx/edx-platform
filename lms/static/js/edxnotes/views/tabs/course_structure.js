;(function (define, undefined) {
'use strict';
define([
    'gettext', 'js/edxnotes/views/note_group', 'js/edxnotes/views/tab_panel',
    'js/edxnotes/views/tab_view'
], function (gettext, NoteGroupView, TabPanelView, TabView) {
    var CourseStructureView = TabView.extend({
        SubViewConstructor: TabPanelView.extend({
            id: 'structure-panel',
            title: 'Course Structure',

            renderContent: function () {
                var courseStructure = this.collection.getCourseStructure();
                _.each(courseStructure.chapters, function (chapter) {
                    _.each(chapter.children, function (location) {
                        var section = courseStructure.sections[location],
                            group;
                        if (section) {
                            group = this.getGroup(chapter, section);
                            _.each(section.children, function (location) {
                                var notes = courseStructure.units[location];
                                if (notes) {
                                    group.addChild(this.getNotes(notes))
                                }
                            }, this);
                            group.render().$el.appendTo(this.$el);
                        }
                    }, this);
                }, this);

                return this;
            },

            getGroup: function (chapter, section) {
                return new NoteGroupView({
                    chapter: chapter,
                    section: section
                });
            }
        }),

        tabInfo: {
            name: gettext('Course Structure'),
            class_name: 'view-course-structure',
            icon: 'icon-list-ul'
        }
    });

    return CourseStructureView;
});
}).call(this, define || RequireJS.define);

(function(define, undefined) {
    'use strict';
    define([
        'gettext', 'underscore', 'js/edxnotes/views/note_group', 'js/edxnotes/views/tab_panel',
        'js/edxnotes/views/tab_view', 'edx-ui-toolkit/js/utils/html-utils'
    ], function(gettext, _, NoteGroupView, TabPanelView, TabView, HtmlUtils) {
        var view = 'Location in Course';
        var CourseStructureView = TabView.extend({
            PanelConstructor: TabPanelView.extend({
                id: 'structure-panel',
                title: view,

                renderContent: function() {
                    var courseStructure = this.collection.getCourseStructure(),
                        container = document.createDocumentFragment();

                    _.each(courseStructure.chapters, function(chapterInfo) {
                        var chapterView = this.getChapterGroupView(chapterInfo);
                        _.each(chapterInfo.children, function(location) {
                            var sectionInfo = courseStructure.sections[location],
                                sectionView;
                            if (sectionInfo) {
                                sectionView = chapterView.addChild(sectionInfo);
                                _.each(sectionInfo.children, function(location) {
                                    var notes = courseStructure.units[location];
                                    if (notes) {
                                        sectionView.addChild(this.getNotes(notes));
                                    }
                                }, this);
                            }
                        }, this);
                        container.appendChild(chapterView.render().el);
                    }, this);
                    this.$el.append(HtmlUtils.HTML(container).toString());
                    return this;
                },

                getChapterGroupView: function(chapter, section) {
                    var group = new NoteGroupView.ChapterView({
                        chapter: chapter,
                        section: section
                    });
                    this.children.push(group);
                    return group;
                }
            }),

            tabInfo: {
                name: gettext('Location in Course'),
                identifier: 'view-course-structure',
                icon: 'fa fa-list-ul',
                view: view
            }
        });

        return CourseStructureView;
    });
}).call(this, define || RequireJS.define);

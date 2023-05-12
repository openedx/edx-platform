/* eslint-disable-next-line no-shadow-restricted-names, no-unused-vars */
(function(define, undefined) {
    'use strict';

    define([
        'gettext', 'underscore', 'js/edxnotes/views/note_group', 'js/edxnotes/views/tab_panel',
        'js/edxnotes/views/tab_view', 'edx-ui-toolkit/js/utils/html-utils'
    ], function(gettext, _, NoteGroupView, TabPanelView, TabView, HtmlUtils) {
        // eslint-disable-next-line no-var
        var view = 'Location in Course';
        // eslint-disable-next-line no-var
        var CourseStructureView = TabView.extend({
            PanelConstructor: TabPanelView.extend({
                id: 'structure-panel',
                title: view,

                renderContent: function() {
                    // eslint-disable-next-line no-var
                    var courseStructure = this.collection.getCourseStructure(),
                        container = document.createDocumentFragment();

                    _.each(courseStructure.chapters, function(chapterInfo) {
                        // eslint-disable-next-line no-var
                        var chapterView = this.getChapterGroupView(chapterInfo);
                        _.each(chapterInfo.children, function(location) {
                            // eslint-disable-next-line no-var
                            var sectionInfo = courseStructure.sections[location],
                                sectionView;
                            if (sectionInfo) {
                                sectionView = chapterView.addChild(sectionInfo);
                                // eslint-disable-next-line no-shadow
                                _.each(sectionInfo.children, function(location) {
                                    // eslint-disable-next-line no-var
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
                    // eslint-disable-next-line no-var
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
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);

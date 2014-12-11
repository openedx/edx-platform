;(function (define, undefined) {
'use strict';
define([
    'jquery', 'gettext', 'backbone', 'js/edxnotes/utils/template',
    'js/edxnotes/views/note_item', 'js/edxnotes/views/tab_view'
], function ($, gettext, Backbone, templateUtils, NoteItemView, TabView) {
    var NoteGroupView, CourseStructureView;

    NoteGroupView = Backbone.View.extend({
        tagName: 'section',
        className: 'note-group',
        id: function () {
            return 'note-group-' + _.uniqueId();
        },

        initialize: function () {
            this.template = templateUtils.loadTemplate('note-group');
            this.children = [];
        },

        render: function () {
            this.$el.html(this.template({
                chapterName: this.getChapterName(),
                sectionName: this.getSectionName()
            }));

            _.each(this.children, function (child) {
                this.$el.append(child);
            }, this);

            return this;
        },

        getChapterName: function () {
            return this.options.chapter.display_name || '';
        },

        getSectionName: function () {
            return this.options.section.display_name || '';
        },

        addChild: function (child) {
            this.children.push(child);
        }
    });

    CourseStructureView = TabView.extend({
        SubViewConstructor: Backbone.View.extend({
            className: 'tab-panel',
            id: 'structure-panel',

            render: function () {
                var courseStructure = this.collection.getCourseStructure();

                this.$el.append(this.getTitle());
                _.each(courseStructure.chapters, function (chapter) {
                    _.each(chapter.children, function (location) {
                        var section = courseStructure.sections[location],
                            group;

                        if (section) {
                            group = this.getGroup(chapter, section);
                            _.each(section.children, function (location) {
                                var unit = courseStructure.units[location];
                                if (unit) {
                                    group.addChild(this.getNotes(unit))
                                }
                            }, this);
                            group.render().$el.appendTo(this.$el);
                        }
                    }, this);
                }, this);

                return this;
            },

            getNotes: function (models, id) {
                var container = document.createDocumentFragment();
                _.each(models, function (model) {
                    var item = new NoteItemView({model: model});
                    container.appendChild(item.render().el);
                });

                return container;
            },

            getGroup: function (chapter, section) {
                return  new NoteGroupView({
                    chapter: chapter,
                    section: section
                });
            },

            getTitle: function () {
                return $('<h2></h2>', {
                    'class': 'sr',
                    'text': gettext('Course Strucutre')
                }).get(0);
            }
        }),

        tabInfo: {
            name: gettext('Course Strucutre'),
            class_name: 'view-course-structure',
            icon: 'icon-list-ul'
        }
    });

    return CourseStructureView;
});
}).call(this, define || RequireJS.define);

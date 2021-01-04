(function(define, undefined) {
    'use strict';
    define([
        'gettext', 'underscore', 'backbone', 'edx-ui-toolkit/js/utils/html-utils'
    ], function(gettext, _, Backbone, HtmlUtils) {
        var GroupView, ChapterView;

        GroupView = Backbone.View.extend({
            tagName: 'section',
            id: function() {
                return 'note-section-' + _.uniqueId();
            },

            initialize: function(options) {
                this.options = _.extend({}, options);
                this.template = HtmlUtils.template(this.options.template);
                this.className = this.options.className;
            },

            render: function() {
                HtmlUtils.prepend(this.$el, this.template({
                    displayName: this.options.displayName
                }));

                return this;
            },

            addChild: function(child) {
                this.$el.append(HtmlUtils.HTML(child).toString());
            }
        });

        ChapterView = Backbone.View.extend({
            tagName: 'section',
            className: 'note-group',
            id: function() {
                return 'note-group-' + _.uniqueId();
            },
            template: HtmlUtils.template('<h3 class="course-title"><%- chapterName %></h3>'),

            initialize: function(options) {
                this.children = [];
                this.options = _.extend({}, options);
            },

            render: function() {
                var container = document.createDocumentFragment();
                HtmlUtils.setHtml(this.$el, this.template({chapterName: this.options.chapter.display_name || ''}));
                _.each(this.children, function(section) {
                    container.appendChild(section.render().el);
                });
                this.$el.append(HtmlUtils.HTML(container).toString());

                return this;
            },

            addChild: function(sectionInfo) {
                var section = new GroupView(
                    {
                        displayName: sectionInfo.display_name,
                        template: '<h4 class="course-subtitle"><%- displayName %></h4>',
                        className: 'note-section'
                    }
            );
                this.children.push(section);
                return section;
            },

            remove: function() {
                _.invoke(this.children, 'remove');
                this.children = null;
                Backbone.View.prototype.remove.call(this);
                return this;
            }
        });

        return {GroupView: GroupView, ChapterView: ChapterView};
    });
}).call(this, define || RequireJS.define);

(function(define, undefined) {
    'use strict';
    define([
        'gettext', 'underscore', 'backbone'
    ], function(gettext, _, Backbone) {
        var GroupView, ChapterView;

        GroupView = Backbone.View.extend({
            tagName: 'section',
            id: function() {
                return 'note-section-' + _.uniqueId();
            },

            initialize: function(options) {
                this.options = _.extend({}, options);
                this.template = _.template(this.options.template);
                this.className = this.options.className;
            },

            render: function() {
                this.$el.prepend(this.template({
                    displayName: this.options.displayName
                }));

                return this;
            },

            addChild: function(child) {
                this.$el.append(child);
            }
        });

        ChapterView = Backbone.View.extend({
            tagName: 'section',
            className: 'note-group',
            id: function() {
                return 'note-group-' + _.uniqueId();
            },
            template: _.template('<h3 class="course-title"><%- chapterName %></h3>'),

            initialize: function(options) {
                this.children = [];
                this.options = _.extend({}, options);
            },

            render: function() {
                var container = document.createDocumentFragment();
                this.$el.html(this.template({
                    chapterName: this.options.chapter.display_name || ''
                }));
                _.each(this.children, function(section) {
                    container.appendChild(section.render().el);
                });
                this.$el.append(container);

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

(function(define, undefined) {
    'use strict';
    define(['gettext', 'underscore', 'backbone', 'js/edxnotes/views/note_item',
        'common/js/components/views/paging_header', 'common/js/components/views/paging_footer',
        'edx-ui-toolkit/js/utils/html-utils'],
    function(gettext, _, Backbone, NoteItemView, PagingHeaderView, PagingFooterView, HtmlUtils) {
        var TabPanelView = Backbone.View.extend({
            tagName: 'section',
            className: 'tab-panel',
            title: '',
            titleTemplate: HtmlUtils.template('<h2 class="sr"><%- text %></h2>'),
            attributes: {
                tabindex: -1
            },

            initialize: function(options) {
                this.children = [];
                this.options = _.extend({}, options);
                if (this.options.createHeaderFooter) {
                    this.pagingHeaderView = new PagingHeaderView({collection: this.collection});
                    this.pagingFooterView = new PagingFooterView({collection: this.collection, hideWhenOnePage: true});
                }
                if (this.hasOwnProperty('collection')) {
                    this.listenTo(this.collection, 'page_changed', this.render);
                }
            },

            render: function() {
                HtmlUtils.setHtml(
                    this.$el,
                    this.getTitle()
                );
                this.renderView(this.pagingHeaderView);
                this.renderContent();
                this.renderView(this.pagingFooterView);
                return this;
            },

            renderView: function(view) {
                if (this.options.createHeaderFooter && this.collection.models.length) {
                    this.$el.append(view.render().el);
                    view.delegateEvents();
                }
            },

            renderContent: function() {
                return this;
            },

            getNotes: function(collection) {
                var container = document.createDocumentFragment(),
                    scrollToTag = this.options.scrollToTag,
                    view = this.title,
                    notes = _.map(collection, function(model) {
                        var note = new NoteItemView({model: model, scrollToTag: scrollToTag, view: view});
                        container.appendChild(note.render().el);
                        return note;
                    });

                this.children = this.children.concat(notes);
                return container;
            },

            getTitle: function() {
                return this.title ? this.titleTemplate({text: gettext(this.title)}) : '';
            },

            remove: function() {
                _.invoke(this.children, 'remove');
                this.children = null;
                Backbone.View.prototype.remove.call(this);
                return this;
            }
        });

        return TabPanelView;
    });
}).call(this, define || RequireJS.define);

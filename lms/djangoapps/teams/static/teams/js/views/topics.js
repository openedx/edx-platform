;(function (define) {
    'use strict';
    define([
        'backbone',
        'underscore',
        'gettext',
        'common/js/components/views/list',
        'common/js/components/views/paging_header',
        'common/js/components/views/paging_footer',
        'teams/js/views/topic_card',
        'text!teams/templates/topics.underscore'
    ], function (Backbone, _, gettext, ListView, PagingHeader, PagingFooterView, TopicCardView, topics_template) {
        var TopicsListView = ListView.extend({
            tagName: 'div',
            className: 'topics-container',
            itemViewClass: TopicCardView
        });

        var TopicsView = Backbone.View.extend({
            initialize: function() {
                this.listView = new TopicsListView({collection: this.collection});
                this.headerView = new PagingHeader({collection: this.collection});
                this.pagingFooterView = new PagingFooterView({
                    collection: this.collection, hideWhenOnePage: true
                });
                // Focus top of view for screen readers
                this.collection.on('page_changed', function () {
                    this.$('.sr-is-focusable.sr-topics-view').focus();
                }, this);
            },

            render: function() {
                this.$el.html(_.template(topics_template));
                this.assign(this.listView, '.topics-list');
                this.assign(this.headerView, '.topics-paging-header');
                this.assign(this.pagingFooterView, '.topics-paging-footer');
                return this;
            },

            /**
             * Helper method to render subviews and re-bind events.
             *
             * Borrowed from http://ianstormtaylor.com/rendering-views-in-backbonejs-isnt-always-simple/
             *
             * @param view The Backbone view to render
             * @param selector The string CSS selector which the view should attach to
             */
            assign: function(view, selector) {
                view.setElement(this.$(selector)).render();
            }
        });
        return TopicsView;
    });
}).call(this, define || RequireJS.define);

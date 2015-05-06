;(function (define) {

define([
    'jquery',
    'underscore',
    'backbone',
    'gettext',
    'js/discovery/result_item_view'
], function ($, _, Backbone, gettext, ResultItemView) {
   'use strict';

    return Backbone.View.extend({

        el: 'section.courses',
        $window: $(window),
        $document: $(document),

        initialize: function () {
            this.$list = this.$el.find('.courses-listing');
            this.attachScrollHandler();
        },

        render: function () {
            this.$list.empty();
            this.renderItems();
            return this;
        },

        renderNext: function () {
            this.renderItems();
            this.isLoading = false;
        },

        renderItems: function () {
            var latest = this.collection.latestModels();
            var items = latest.map(function (result) {
                var item = new ResultItemView({ model: result });
                return item.render().el;
            }, this);
            this.$list.append(items);
        },

        attachScrollHandler: function () {
            this.nextScrollEvent = true;
            this.$window.on('scroll', this.scrollHandler.bind(this));
        },

        scrollHandler: function () {
            if (this.nextScrollEvent) {
                setTimeout(this.throttledScrollHandler.bind(this), 400);
                this.nextScrollEvent = false;
            }
        },

        throttledScrollHandler: function () {
            if (this.isNearBottom()) {
                this.scrolledToBottom();
            }
            this.nextScrollEvent = true;
        },

        isNearBottom: function () {
            var scrollBottom = this.$window.scrollTop() + this.$window.height();
            var threshold = this.$document.height() - 200;
            return scrollBottom >= threshold;
        },

        scrolledToBottom: function () {
            if (this.thereIsMore() && !this.isLoading) {
                this.trigger('next');
                this.isLoading = true;
            }
        },

        thereIsMore: function () {
            return this.collection.hasNextPage();
        }

    });

});


})(define || RequireJS.define);

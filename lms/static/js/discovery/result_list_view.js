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
        originalContent: '',
        $window: $(window),
        $document: $(document),

        initialize: function () {
            this.loadingTemplate = _.template($('#loading-tpl').html());
            this.errorTemplate = _.template($('#error-tpl').html());
            this.loadingIndicator = $('<div>', {id: 'loading-indicator', style: 'display:none'});
            this.loadingIndicator.html(this.loadingTemplate());
            this.$el.append(this.loadingIndicator);
            this.$list = this.$el.find('.courses-listing');
            this.originalContent = this.$list.html();
        },

        render: function () {
            this.hideLoadingIndicator();
            this.$list.empty();
            this.renderItems();
            this.attachScrollHandler();
            return this;
        },

        renderNext: function () {
            this.hideLoadingIndicator();
            this.renderItems();
            this.isLoading = false;
            // if has more attach
        },

        renderItems: function () {
            var latest = this.collection.latestModels();
            var items = latest.map(function (result) {
                var item = new ResultItemView({ model: result });
                return item.render().el;
            }, this);
            this.$list.append(items);
        },

        showLoadingIndicator: function () {
            this.loadingIndicator.show();
        },

        hideLoadingIndicator: function () {
            this.loadingIndicator.hide();
        },

        showErrorMessage: function () {
            // this.$el.html(this.errorTemplate());
            // this.$el.show();
            // this.$contentElement.hide();
        },

        loadNext: function (event) {
            event && event.preventDefault();
            this.showLoadingIndicator();
            this.trigger('next');
        },

        clear: function() {
            this.$list.html(this.originalContent);
            this.detachScrollHandler();
        },

        attachScrollHandler: function () {
            this.nextScrollEvent = true;
            this.$window.on('scroll', this.scrollHandler.bind(this));
        },

        detachScrollHandler: function () {
            this.$window.off('scroll', this.scrollHandler);
        },

        scrollHandler: function () {
            if (this.nextScrollEvent) {
                setTimeout(this.throttledScrollHandler.bind(this), 400);
                this.nextScrollEvent = false;
            }
        },

        throttledScrollHandler: function () {
            if (this.isBottom()) {
                this.scrolledToBottom();
            }
            this.nextScrollEvent = true;
        },

        isBottom: function () {
            var scrollBottom = this.$window.scrollTop() + this.$window.height();
            return scrollBottom >= this.$document.height();
        },

        scrolledToBottom: function () {
            this.hasMore = true;
            if (this.hasMore && !this.isLoading) {
                this.loadNext();
                this.isLoading = true;
            }
        }


    });

});


})(define || RequireJS.define);

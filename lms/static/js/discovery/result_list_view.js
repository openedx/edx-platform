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
        events: {
            'click #discovery-clear': 'clearAll'
        },

        initialize: function () {
            this.loadingTemplate = _.template($('#loading-tpl').html());
            this.notFoundTemplate = _.template($('#not_found-tpl').html());
            this.errorTemplate = _.template($('#error-tpl').html());
            this.loadingIndicator = $('<div>', {id: 'loading-indicator', style: 'display:none'});
            this.loadingIndicator.html(this.loadingTemplate());
            this.$el.append(this.loadingIndicator);
            this.$list = this.$el.find('.courses-listing');
            this.$message = this.$el.find('#discovery-message');
            this.originalContent = this.$list.html();
        },

        render: function () {
            this.$message.empty();
            this.hideLoadingIndicator();
            if (this.collection.length > 0) {
                this.$list.empty();
                this.renderItems();
                this.showClearAllButton();
                this.attachScrollHandler();
            }
            else {
                var msg = this.notFoundTemplate({term: this.collection.searchTerm});
                this.$message.html(msg);
                this.hideClearAllButton();
            }
            return this;
        },

        renderNext: function () {
            this.hideLoadingIndicator();
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

        showLoadingIndicator: function () {
            this.loadingIndicator.show();
        },

        hideLoadingIndicator: function () {
            this.loadingIndicator.hide();
        },

        showErrorMessage: function () {
            var msg = this.errorTemplate();
            this.$message.html(msg);
        },

        loadNext: function (event) {
            event && event.preventDefault();
            this.showLoadingIndicator();
            this.trigger('next');
        },

        clearResults: function() {
            this.$list.html(this.originalContent);
            this.detachScrollHandler();
        },

        showClearAllButton: function () {
            this.$el.find('#discovery-clear').removeClass('hidden');
        },

        hideClearAllButton: function() {
            this.$el.find('#discovery-clear').addClass('hidden');
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
                this.loadNext();
                this.isLoading = true;
            }
        },

        thereIsMore: function () {
            return this.collection.hasNextPage();
        },

        clearAll: function () {
            this.hideClearAllButton();
            this.clearResults();
            this.trigger('clear');
            return false;
        }


    });

});


})(define || RequireJS.define);

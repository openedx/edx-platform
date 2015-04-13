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

        el: 'ul.courses-listing',

        initialize: function () {
            // this.resultsTemplate = _.template($(this.resultsTemplateId).html());
            // this.loadingTemplate = _.template($(this.loadingTemplateId).html());
            // this.errorTemplate = _.template($(this.errorTemplateId).html());
            this.collection.on('search', this.render, this);
            this.collection.on('next', this.renderNext, this);
            this.collection.on('error', this.showErrorMessage, this);
        },

        render: function () {
            this.$el.empty();
            this.renderItems();
            // this.$el.find(this.spinner).hide();
            return this;
        },

        renderNext: function () {
            // total count may have changed
            // this.$el.find('.search-count').text(this.totalCountMsg());
            this.renderItems();
            // if (! this.collection.hasNextPage()) {
            //     this.$el.find('.search-load-next').remove();
            // }
            // this.$el.find(this.spinner).hide();
        },

        renderItems: function () {
            var latest = this.collection.latestModels();
            var items = latest.map(function (result) {
                var item = new ResultItemView({ model: result });
                return item.render().el;
            }, this);
            this.$el.append(items);
        },

        totalCountMsg: function () {
            var fmt = ngettext('%s result', '%s results', this.collection.totalCount);
            return interpolate(fmt, [this.collection.totalCount]);
        },

        clear: function () {
            // this.$el.hide().empty();
            // this.$contentElement.show();
        },

        showLoadingMessage: function () {
            // this.$el.html(this.loadingTemplate());
            // this.$el.show();
            // this.$contentElement.hide();
        },

        showErrorMessage: function () {
            // this.$el.html(this.errorTemplate());
            // this.$el.show();
            // this.$contentElement.hide();
        },

        loadNext: function (event) {
            event && event.preventDefault();
            this.$el.find(this.spinner).show();
            this.trigger('next');
        }

    });

});


})(define || RequireJS.define);

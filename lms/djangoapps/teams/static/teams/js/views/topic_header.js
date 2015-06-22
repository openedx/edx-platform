;(function (define) {
    'use strict';
    define([
        'backbone',
        'underscore',
        'gettext',
        'text!teams/templates/topic-header.underscore'
    ], function (Backbone, _, gettext, headerTemplate) {
        var TopicHeader = Backbone.View.extend({
            initialize: function (options) {
                this.collections = options.collection;
                this.collection.bind('add', _.bind(this.render, this));
                this.collection.bind('remove', _.bind(this.render, this));
                this.collection.bind('reset', _.bind(this.render, this));
            },

            render: function () {
                var currentlyViewing,
                    start = this.collection.start,
                    perPage = this.collection.perPage,
                    end = start + perPage,
                    size = this.collection.totalCount;
                // Translators: becomes either "all 10 topics" or "1 through 5 of 10 topics"
                if (end >= size && start === 0) {
                    currentlyViewing = gettext("all ") + size;
                }
                else {
                    currentlyViewing = Math.min(start + 1, end) + gettext(" through ") + end + gettext(" of ") + size;
                }
                this.$el.html(_.template(headerTemplate, {currentlyViewing: currentlyViewing}));
                return this;
            }
        });
        return TopicHeader;
    });
}).call(this, define || RequireJS.define);

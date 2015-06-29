;(function (define) {
    'use strict';
    define([
        'backbone',
        'underscore',
        'gettext',
        'text!common/templates/components/paging-header.underscore'
    ], function (Backbone, _, gettext, headerTemplate) {
        var PagingHeader = Backbone.View.extend({
            initialize: function (options) {
                this.collections = options.collection;
                this.collection.bind('add', _.bind(this.render, this));
                this.collection.bind('remove', _.bind(this.render, this));
                this.collection.bind('reset', _.bind(this.render, this));
            },

            render: function () {
                var message,
                    start = this.collection.start,
                    end = start + this.collection.length,
                    num_items = this.collection.totalCount,
                    context = {first_index: Math.min(start + 1, end), last_index: end, num_items: num_items};
                if (end <= 1) {
                    message = interpolate(gettext('Showing %(first_index)s out of %(num_items)s total'), context, true);
                } else {
                    message = interpolate(
                        gettext('Showing %(first_index)s-%(last_index)s out of %(num_items)s total'),
                        context, true
                    );
                }
                this.$el.html(_.template(headerTemplate, {message: message}));
                return this;
            }
        });
        return PagingHeader;
    });
}).call(this, define || RequireJS.define);

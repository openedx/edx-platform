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
                this.itemDisplayNameSingular = options.itemDisplayNameSingular || gettext('item');
                this.itemDisplayNamePlural = options.itemDisplayNamePlural || gettext('items');
                this.collection.bind('add', _.bind(this.render, this));
                this.collection.bind('remove', _.bind(this.render, this));
                this.collection.bind('reset', _.bind(this.render, this));
            },

            render: function () {
                var message,
                    start = this.collection.start,
                    end = start + this.collection.length,
                    num_items = this.collection.totalCount;
                if (!this.collection.hasPreviousPage() && !this.collection.hasNextPage()) {
                    // One page of results
                    message = interpolate(
                        ngettext(
                            /*
                             * Translators: 'num_items' is the number of items that the student sees
                             * 'item_display_name_singular' is the translated singular form of the item name
                             * 'item_display_name_plural' is the translated plural form of the item name
                             */
                            'Currently viewing %(num_items)s %(item_display_name_singular)s',
                            'Currently viewing all %(num_items)s %(item_display_name_plural)s',
                            num_items
                        ), {
                            num_items: num_items,
                            item_display_name_singular: this.itemDisplayNameSingular,
                            item_display_name_plural: this.itemDisplayNamePlural
                        }, true
                    );
                } else {
                    // Many pages of results
                    message = interpolate(
                        ngettext(
                            'Currently viewing %(first_index)s through %(last_index)s of %(num_items)s %(item_display_name_singular)s',
                            'Currently viewing %(first_index)s through %(last_index)s of %(num_items)s %(item_display_name_plural)s',
                            num_items
                        ), {
                            first_index: Math.min(start + 1, end),
                            last_index: end,
                            num_items: num_items,
                            item_display_name_singular: this.itemDisplayNameSingular,
                            item_display_name_plural: this.itemDisplayNamePlural
                        }, true
                    );
                }
                this.$el.html(_.template(headerTemplate, {message: message}));
                return this;
            }
        });
        return PagingHeader;
    });
}).call(this, define || RequireJS.define);

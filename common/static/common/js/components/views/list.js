/**
 * Generic view to render a collection.
 */
;(function (define) {
    'use strict';
    define(['backbone', 'underscore'], function(Backbone, _) {
        var ListView = Backbone.View.extend({
            /**
             * Override with the view used to render models in the collection.
             */
            itemViewClass: Backbone.View,

            initialize: function () {
                this.collection.on('update', this.render, this);
                this.collection.on('reset', this.render, this);
                this.collection.on('sync', this.render, this);
                this.collection.on('sort', this.render, this);

                // Keep track of our children for garbage collection
                this.itemViews = [];
            },

            /**
             * Naive render.  Any time the collection changes at all we
             * re-render the entire list due to ordering
             */
            render: function () {
                // Remove old children views
                _.each(this.itemViews, function (childView) {
                    childView.remove();
                });
                this.itemViews = [];
                // Render the collection
                this.collection.each(function (model) {
                    var itemView = new this.itemViewClass({model: model});
                    this.$el.append(itemView.render().el);
                    this.itemViews.push(itemView);
                }, this);
                return this;
            }
        });
        return ListView;
    });
}).call(this, define || RequireJS.define);

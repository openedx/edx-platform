/**
 * A Backbone view that renders breadcrumbs-type tiered navigation.
 *
 * Initialize the view by passing in the following attributes:
 *
 *~~~ javascript
 * var view = new BreadcrumbsView({
 *     el: $('selector for element that will contain breadcrumbs'),
 *     model: new BreadcrumbsModel({
 *         breadcrumbs: [{url: '/', title: 'Overview'}]
 *     }),
 *     events: {
 *         'click nav.breadcrumbs a.nav-item': function (event) {
 *             event.preventDefault();
 *             window.location = $(event.currentTarget).attr('href');
 *         }
 *     }
 * });
 *~~~
 * @module BreadcrumbsView
 */
(function(define) {
    'use strict';

    define(['backbone', 'edx-ui-toolkit/js/utils/html-utils', 'text!./breadcrumbs.underscore'],
        function(Backbone, HtmlUtils, breadcrumbsTemplate) {
            var BreadcrumbsView = Backbone.View.extend({
                initialize: function() {
                    this.template = HtmlUtils.template(breadcrumbsTemplate);
                    this.listenTo(this.model, 'change', this.render);
                    this.render();
                },

                render: function() {
                    var json = this.model.attributes;
                    HtmlUtils.setHtml(this.$el, this.template(json));
                    return this;
                }
            });

            return BreadcrumbsView;
        });
}).call(
    this,
    // Use the default 'define' function if available, else use 'RequireJS.define'
    typeof define === 'function' && define.amd ? define : RequireJS.define
);

/**
 * A Backbone model that works with the BreadcrumbsView to provide breadcrumb navigation
 *
 * Here's what initializing a BreadcrumbsModel looks like:
 *
 *~~~ javascript
 * var model = new BreadcrumbsModel({
 *     breadcrumbs: [
 *         {
 *             url: '/',
 *             title: 'Item List'
 *         },
 *         {
 *             url: '/details/1',
 *             title: 'Item Details'
 *         }
 *     ],
 *     label: 'Demo Page'
 * });
 *~~~
 * @module BreadcrumbsModel
 */
(function(define) {
    'use strict';

    define(['backbone'], function(Backbone) {
        var BreadcrumbsModel = Backbone.Model.extend({
            defaults: {
                breadcrumbs: null,
                label: ''
            }
        });

        return BreadcrumbsModel;
    });
}).call(
    this,
    // Use the default 'define' function if available, else use 'RequireJS.define'
    typeof define === 'function' && define.amd ? define : RequireJS.define
);

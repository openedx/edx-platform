/**
 * A generic header model.
 */
;(function (define) {
'use strict';
define(['backbone'], function (Backbone) {
    var HeaderModel = Backbone.Model.extend({
        defaults: {
            'title': '',
            'description': '',
            'breadcrumbs': null,
            'nav_aria_label': ''
        }
    });

    return HeaderModel;
});
}).call(this, define || RequireJS.define);

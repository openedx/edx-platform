/**
 * A generic header model.
 */
(function(define) {
    'use strict';

    define(['backbone'], function(Backbone) {
        // eslint-disable-next-line no-var
        var HeaderModel = Backbone.Model.extend({
            defaults: {
                title: '',
                description: '',
                breadcrumbs: null,
                nav_aria_label: ''
            }
        });

        return HeaderModel;
    });
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);

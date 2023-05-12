// eslint-disable-next-line no-shadow-restricted-names
(function(define, undefined) {
    'use strict';

    define([
        'backbone', 'js/edxnotes/models/tab'
    ], function(Backbone, TabModel) {
        var TabsCollection = Backbone.Collection.extend({
            model: TabModel
        });

        return TabsCollection;
    });
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);

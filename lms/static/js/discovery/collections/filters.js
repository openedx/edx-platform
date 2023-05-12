(function(define) {
    define(['backbone', 'js/discovery/models/filter'], function(Backbone, Filter) {
        'use strict';

        return Backbone.Collection.extend({
            model: Filter,
            getTerms: function() {
                return this.reduce(function(terms, filter) {
                    terms[filter.id] = filter.get('query');
                    return terms;
                }, {});
            }
        });
    });
// eslint-disable-next-line no-undef
}(define || RequireJS.define));

(function(define) {
    'use strict';
    define(['backbone', 'js/groups/models/cohort'], function(Backbone, CohortModel) {
        var CohortCollection = Backbone.Collection.extend({
            model: CohortModel,
            comparator: 'name',

            parse: function(response) {
                return response.cohorts;
            }
        });
        return CohortCollection;
    });
}).call(this, define || RequireJS.define);

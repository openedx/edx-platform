(function(define) {
    'use strict';

    define(['backbone', 'js/groups/models/cohort'], function(Backbone, CohortModel) {
        // eslint-disable-next-line no-var
        var CohortCollection = Backbone.Collection.extend({
            model: CohortModel,
            comparator: 'name',

            parse: function(response) {
                return response.cohorts;
            }
        });
        return CohortCollection;
    });
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);

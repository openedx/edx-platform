var edx = edx || {};

(function(Backbone, CohortModel) {
    'use strict';

    edx.groups = edx.groups || {};

    edx.groups.CohortCollection = Backbone.Collection.extend({
        model : CohortModel,
        comparator: "name",

        parse: function(response) {
            return response.cohorts;
        }
    });
}).call(this, Backbone, edx.groups.CohortModel);

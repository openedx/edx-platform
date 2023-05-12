(function(define) {
    'use strict';

    define(['backbone'], function(Backbone) {
        // eslint-disable-next-line no-var
        var CohortModel = Backbone.Model.extend({
            idAttribute: 'id',
            defaults: {
                name: '',
                user_count: 0,
                /**
                * Indicates how students are added to the cohort. Will be "manual" (signifying manual assignment) or
                * "random" (indicating students are randomly assigned).
                */
                assignment_type: '',
                /**
                * If this cohort is associated with a user partition group, the ID of the user partition.
                */
                user_partition_id: null,
                /**
                * If this cohort is associated with a user partition group, the ID of the group within the
                * partition associated with user_partition_id.
                */
                group_id: null
            }
        });
        return CohortModel;
    });
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);

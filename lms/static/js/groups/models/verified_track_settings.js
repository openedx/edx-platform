(function(define) {
    'use strict';
    define(['backbone'], function(Backbone) {
        var VerifiedTrackSettingsModel = Backbone.Model.extend({
            defaults: {
                enabled: false,
                verified_cohort_name: ''
            }
        });
        return VerifiedTrackSettingsModel;
    });
}).call(this, define || RequireJS.define);

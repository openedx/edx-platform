;(function (define) {
    'use strict';

    define([
        'js/learner_dashboard/views/program_details_view'
    ],
    function(ProgramDetailsView) {
        return function (options) {
            var ProgramDetails = new ProgramDetailsView(options.programData);
            return ProgramDetails;
        };
    });
}).call(this, define || RequireJS.define);

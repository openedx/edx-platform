(function() {
    'use strict';

    var Metrics;

    Metrics = (function() {

        function Metrics($section) {
            this.$section = $section;
            this.$section.data('wrapper', this);
        }

        Metrics.prototype.onClickTitle = function() {};

        return Metrics;
    })();

    if (typeof _ !== 'undefined' && _ !== null) {
        _.defaults(window, {
            InstructorDashboard: {}
        });
        _.defaults(window.InstructorDashboard, {
            sections: {}
        });
        _.defaults(window.InstructorDashboard.sections, {
            Metrics: Metrics
        });
    }

}).call(this);

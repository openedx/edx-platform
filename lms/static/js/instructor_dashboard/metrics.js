(function() {
    'use strict';
    var Metrics;

    Metrics = (function() {
        function metrics($section) {
            this.$section = $section;
            this.$section.data('wrapper', this);
        }

        metrics.prototype.onClickTitle = function() {};

        return metrics;
    }());

    window.InstructorDashboard.sections.Metrics = Metrics;
}).call(this);

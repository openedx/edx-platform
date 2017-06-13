/* globals _ */

(function(_) {
    'use strict';

    var OpenResponseAssessment = (function() {
        function OpenResponseAssessmentBlock($section) {
            this.$section = $section;
            this.$section.data('wrapper', this);
            this.initialized = false;
        }

        OpenResponseAssessmentBlock.prototype.onClickTitle = function() {
            var block = this.$section.find('.open-response-assessment');
            if (!this.initialized) {
                this.initialized = true;
                XBlock.initializeBlock($(block).find('.xblock')[0]);
            }
        };

        return OpenResponseAssessmentBlock;
    }());

    if (typeof window.setup_debug === 'undefined') {
        // eslint-disable-next-line no-unused-vars, camelcase
        window.setup_debug = function(element_id, edit_link, staff_context) {
            // stub function.
        };
    }

    _.defaults(window, {
        InstructorDashboard: {}
    });

    _.defaults(window.InstructorDashboard, {
        sections: {}
    });

    _.defaults(window.InstructorDashboard.sections, {
        OpenResponseAssessment: OpenResponseAssessment
    });

    this.OpenResponseAssessment = OpenResponseAssessment;
}).call(this, _);

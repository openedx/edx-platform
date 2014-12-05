/**
 * Show progress steps in the payment/verification flow.
 */

 var edx = edx || {};

 (function( $, _, Backbone, gettext ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.ProgressView = Backbone.View.extend({

        template: '#progress-tpl',

        initialize: function( obj ) {
            this.displaySteps = obj.displaySteps || {};
            this.currentStepIndex = obj.currentStepIndex || 0;
        },

        render: function() {
            var renderedHtml, context;

            context = {
                steps: this.steps()
            };

            renderedHtml = _.template( $(this.template).html(), context );
            $(this.el).html(renderedHtml);
        },

        steps: function() {
            var i,
                stepDescription,
                steps = [];

            for ( i = 0; i < this.displaySteps.length; i++ ) {
                stepDescription = {
                    title: this.displaySteps[i].title,
                    isCurrent: (i === this.currentStepIndex ),
                    isComplete: (i < this.currentStepIndex )
                };
                steps.push(stepDescription);
            }

            return steps;
        }
    });
 })( $, _, Backbone, gettext );

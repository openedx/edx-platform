(function(define) {
    'use strict';

    define([
        'js/financial-assistance/views/financial_assistance_form_view'
    ],
    function(FinancialAssistanceFormView) {
        return function(options) {
            var formView = new FinancialAssistanceFormView({
                el: '.financial-assistance-wrapper',
                context: options
            });

            return formView;
        };
    });
}).call(this, define || RequireJS.define);

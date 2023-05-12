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
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);

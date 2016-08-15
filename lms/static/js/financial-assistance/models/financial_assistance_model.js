/**
 * Model for Financial Assistance.
 */
(function (define) {
    'use strict';
    define(['backbone'], function (Backbone) {
        var FinancialAssistance = Backbone.Model.extend({
            initialize: function(options) {
                this.url = options.url;
            }
        });
        return FinancialAssistance;
    });
}).call(this, define || RequireJS.define);

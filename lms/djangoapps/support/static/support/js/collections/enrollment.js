(function(define) {
    'use strict';

    define(['backbone', 'support/js/models/enrollment'],
        function(Backbone, EnrollmentModel) {
            return Backbone.Collection.extend({
                model: EnrollmentModel,

                initialize: function(models, options) {
                    this.user = options.user || '';
                    this.baseUrl = options.baseUrl;
                },

                url: function() {
                    return this.baseUrl + this.user;
                }
            });
        });
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);

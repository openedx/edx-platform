;(function (define) {
  'use strict';
  define(["backbone", "moment"], function(Backbone, moment) {
    var LicenseModel = Backbone.Model.extend({
      defaults: {
        "code": null,
        "valid_from": null,
        "valid_to": null,
        "simulations_count": 0,
        "students_count": 0,
        "score": 0,
        "questions_answered": 0
      },

      isExpired: function() {
        return moment(this.get("valid_to")) > moment();
      },

      isExpiredSoon: function() {
        var validTo = moment(this.get("valid_to"));

        return validTo.diff(moment(), 'months') < 1;
      }
    });

    return LicenseModel;
  });
}).call(this, define || RequireJS.define);

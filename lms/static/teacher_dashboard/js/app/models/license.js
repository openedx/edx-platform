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
        return moment(this.get("valid_to")) < moment();
      },

      isExpiredSoon: function() {
        var validTo = moment(this.get("valid_to"));

        return validTo.diff(moment(), 'months') < 1;
      },

      getExpirationMessage: function() {
        var msg = '', timeToExpire;

        if (this.isExpired()) {
          msg = "This license is expired.";
        } else if (this.isExpiredSoon()) {
          timeToExpire = moment(this.get("valid_to")).fromNow();
          msg = [
            "This license is going to expire ", timeToExpire, "."].join('');
        }
        return msg;
      }
    });

    return LicenseModel;
  });
}).call(this, define || RequireJS.define);

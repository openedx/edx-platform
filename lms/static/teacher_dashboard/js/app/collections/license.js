;(function (define) {
  'use strict';
  define(["backbone", "teacher_dashboard/js/app/models/license"], function(Backbone, LicenseModel) {
    var LicenseCollection = Backbone.Collection.extend({
      comparator: "code",
      model: LicenseModel
    }, {
      factory: function(models, options) {
        return new LicenseCollection(models, options);
      }
    });

    return LicenseCollection;
  });
}).call(this, define || RequireJS.define);

;(function (define) {
  'use strict';
  define([
      "jquery", "teacher_dashboard/js/app/collections/license",
      "teacher_dashboard/js/app/views/license_list", "teacher_dashboard/js/app/utils"
  ], function ($, LicenseCollection, LicenseListView, utils) {
      var buildLicenseList = _.once(function (collection) {
          var view = new LicenseListView({collection: collection});
          $(document.getElementById("main-content")).html(view.$el);
      });
      var licenseCollection = LicenseCollection.factory();
      buildLicenseList(licenseCollection);
      licenseCollection.url = utils.getUrl("licenses", {}, true);
      licenseCollection.fetch({data: {course_id: course_id}});
  });
}).call(this, define || RequireJS.define);

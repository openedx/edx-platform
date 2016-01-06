;(function (define) {
  'use strict';
  define(["backbone", "teacher_dashboard/js/app/models/user", "teacher_dashboard/js/app/utils"], function(Backbone, UserModel, utils) {
    var UserCollection = Backbone.Collection.extend({
      comparator: 'full_name',
      model: UserModel
    }, {
      factory: function(models, options, license_id, simulation_id) {
        var collection = new UserCollection(models, options);
        collection.url = utils.getUrl("students", {
          license_id: license_id,
          simulation_id: simulation_id
        }, false);
        return collection;
      }
    });

    return UserCollection;
  });
}).call(this, define || RequireJS.define);

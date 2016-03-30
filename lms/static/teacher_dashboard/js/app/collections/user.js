;(function (define) {
  'use strict';
  define(["backbone", "teacher_dashboard/js/app/models/user"], function(Backbone, UserModel) {
    var UserCollection = Backbone.Collection.extend({
      comparator: 'email',
      model: UserModel
    }, {
      factory: function(models, options) {
        return new UserCollection(models, options);
      }
    });

    return UserCollection;
  });
}).call(this, define || RequireJS.define);

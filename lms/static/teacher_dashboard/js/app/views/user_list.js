;(function (define) {
  "use strict";
  define([
    "teacher_dashboard/js/app/views/base", "underscore", "text!teacher_dashboard/templates/user_list.underscore"
  ], function(BaseView, _, UserListTemplate) {
    var UserListView = BaseView.extend({
      tagName: "div",
      className: "user-list",
      template: _.template(UserListTemplate),

      constructor: function() {
        BaseView.prototype.constructor.apply(this, arguments);
        this.listenTo(this.collection, 'sync', this.render);
        this.collection.fetch();
      },

      getContext: function() {return {collection: this.collection};}
  });

    return UserListView;
  });
}).call(this, define || RequireJS.define);

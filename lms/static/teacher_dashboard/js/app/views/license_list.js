;(function (define) {
  'use strict';
  define([
    "teacher_dashboard/js/app/views/base", "underscore", "teacher_dashboard/js/app/views/license_item"
  ], function(BaseView, _, LicenseItemView) {
    var LicenseListView = BaseView.extend({
      className: "license-list",

      constructor: function(options) {
        _.bindAll(this, "renderChildren");
        this.children = [];
        BaseView.prototype.constructor.apply(this, arguments);
        this.listenTo(this.collection, "sync update reset", this.render);
      },

      render: function(context) {
        BaseView.prototype.render.apply(this, arguments);
        if (this.collection.length) {
          this.renderChildren();
        } else {
          this.$el.html(
            "<div class='simulation-list-empty is-empty-section'>There is no available Licenses.</div>"
          );
        }
        return this;
      },

      renderChildren: function(collection) {
        var fragment = document.createDocumentFragment(),
            children = this.children;

        if (children.length) {
          _.invoke(children, "remove");
          children.length = 0;
        }

        this.collection.forEach(function(model) {
          var view = new LicenseItemView({model: model});
          fragment.appendChild(view.render().el);
          children.push(view);
        });
        this.$el.html(fragment);
      }
    });

    return LicenseListView;
  });
}).call(this, define || RequireJS.define);

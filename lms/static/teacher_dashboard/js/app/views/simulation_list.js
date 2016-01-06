;(function (define) {
  "use strict";
  define([
    "teacher_dashboard/js/app/views/base", "underscore", "text!teacher_dashboard/templates/simulation_list.underscore",
    "teacher_dashboard/js/app/views/simulation_item", "jquery.sticky"
  ], function(BaseView, _, SimualtionListTemplate, SimulationItemView) {
    var SimulationListView = BaseView.extend({
      tagName: "section",
      className: "simulation-list",
      template: _.template(SimualtionListTemplate),

      constructor: function(options) {
        _.bindAll(this, "renderChildren");
        this.children = [];
        BaseView.prototype.constructor.apply(this, arguments);
        this.listenTo(this.collection, "sync", this.render);
        this.collection.fetch();
      },

      render: function(context) {
        this.$(".simulation-list-info").trigger("sticky_kit:detach");
        BaseView.prototype.render.apply(this, arguments);
        if (this.collection.length) {
          this.renderChildren();
        } else {
          this.$el.append(
            "<div class='simulation-list-empty is-empty-section'>There is no available simulations.</div>"
          );
        }
        this.$(".simulation-list-info").stick_in_parent({offset_top: $(".navbar-fixed-top").height()});
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
          var view = new SimulationItemView({model: model});
          fragment.appendChild(view.render().el);
          children.push(view);
        });
        this.el.appendChild(fragment);
      }
    });

    return SimulationListView;
  });
}).call(this, define || RequireJS.define);

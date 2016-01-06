;(function (define) {
  "use strict";
  define([
    "teacher_dashboard/js/app/views/base", "underscore", "text!teacher_dashboard/templates/simulation_item.underscore",
    "teacher_dashboard/js/app/collections/user", "teacher_dashboard/js/app/views/user_list",
    "teacher_dashboard/js/app/utils"
  ], function(BaseView, _, SimulationItemTemplate, UserCollection, UserListView, utils) {
    var SimulationItemView = BaseView.extend({
      tagName: "div",
      className: "simulation-item",
      template: _.template(SimulationItemTemplate),
      events: {"click .simulation-item-name": "expand"},

      render: function() {
        BaseView.prototype.render.apply(this, arguments);
        if (this.isExpanded) {
          var userCollection = UserCollection.factory(null, null, this.model.get("license"), this.model.get("id")),
              userListView = new UserListView({collection: userCollection});

          userListView.$el.appendTo(this.$el);
        }
        return this;
      },

      getContext: function() {
        var csvUrl = utils.getUrl("students", {
          license_id: this.model.get("license"),
          simulation_id: this.model.get("id")
        }) + "?format=csv";
        return {
          "display_name": this.model.get("display_name"),
          "score": this.model.get("score"),
          "questions_answered": this.model.get("questions_answered"),
          "is_expanded": this.isExpanded,
          "csv_url": csvUrl
        };
      },

      expand: function(event) {
        event.stopPropagation();
        if (this.isExpanded) {
          this.$el.removeClass("is-expanded");
          this.isExpanded = false;
        } else {
          this.$el.addClass("is-expanded");
          this.isExpanded = true;
        }
        this.render();
      }
    });

    return SimulationItemView;
  });
}).call(this, define || RequireJS.define);

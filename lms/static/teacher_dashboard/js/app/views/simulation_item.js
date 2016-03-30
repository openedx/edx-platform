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
          var userCollection = UserCollection.factory(),
              userListView = new UserListView({collection: userCollection});

          userListView.$el.appendTo(this.$el);

          utils.fetch(userCollection, {
            type: 'students',
            license: this.model.get('license').get('id'),
            simulation: this.model.get('id')
          });
        }
        return this;
      },

      getContext: function() {
        return {
          "display_name": this.model.get("display_name"),
          "is_expanded": this.isExpanded,
          "csv_url": utils.getUrl({
              type: 'attempts',
              license: this.model.get('license').get('id'),
              simulation: this.model.get('id')
            })
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

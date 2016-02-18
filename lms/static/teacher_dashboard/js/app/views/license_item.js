;(function (define) {
  'use strict';
  define([
    "teacher_dashboard/js/app/views/base", "underscore", "moment", "text!teacher_dashboard/templates/license_item.underscore",
    'teacher_dashboard/js/app/collections/simulation', 'teacher_dashboard/js/app/views/simulation_list'
  ], function(BaseView, _, moment, LicenseItemTemplate, SimulationCollection, SimulationListView) {
    var DATE_FORMAT = "L";

    var LicenseView = BaseView.extend({
      tagName: "section",
      className: "license-item",
      template: _.template(LicenseItemTemplate),
      events: {
        "click .license-item-code": "expand"
      },

      render: function(context) {
        BaseView.prototype.render.apply(this, arguments);
        this.renderChildren();
        return this;
      },

      renderChildren: function() {
        if (this.chldrenView) {
          this.chldrenView.remove();
          this.chldrenView = null;
        }
        if (this.isExpanded) {
          var collection = SimulationCollection.factory(null, null, this.model.get('id'));
          this.chldrenView = new SimulationListView({collection: collection});
          this.chldrenView.$el.appendTo(this.$el);
        }
      },

      getContext: function() {
        return {
          "code": this.model.get("code"),
          "simulations_count": this.model.get("simulations_count"),
          "display_expiration_message": this.model.isExpired() || this.model.isExpiredSoon(),
          "expiration_message": this.model.getExpirationMessage(),
          "valid_from": moment(this.model.get("valid_from")).format(DATE_FORMAT),
          "valid_to": moment(this.model.get("valid_to")).format(DATE_FORMAT),
          "is_expanded": this.isExpanded
        };
      },

      expand: function() {
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

    return LicenseView;
  });
}).call(this, define || RequireJS.define);

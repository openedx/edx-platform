var define = window.define || RequireJS.define;  // jshint ignore:line

define(
  [
    'backbone',
    'jquery',
    'underscore',
    'gettext',
    'text!templates/ccx/ccx_schedule_node.underscore'
  ],
  function ( Backbone, $, _, gettext, scheduleTreeNodeTemplate) {
    'use strict';

    var ccxScheduleTreeNodeView = Backbone.View.extend({
      template: _.template(scheduleTreeNodeTemplate),
      tagName: "tr",

      initialize: function () {
          this.model.on("change", this.modelChanged, this);
      },

      events: {
          "click": "viewClicked"
      },

      render: function () {
          var modelToJson = this.model.toJSON();
          var outputHtml = this.template(modelToJson);
          this.$el.html(outputHtml);
          this.$el.attr('data-location', modelToJson.location);
          this.$el.attr('class', modelToJson.category + " collapsed");

          if (modelToJson.category === "chapter") {
            this.$el.attr('data-depth', "1");
          } else if (modelToJson.category === "sequential") {
            this.$el.attr('data-depth', "2");
          } else {
            this.$el.attr('data-depth', "3");
          }
          return this;
      },

      modelChanged: function (model, changes) {
          console.log("modelChanged:" + model.get("title"));
          this.render();
      },

      viewClicked: function (event) {
          console.log("viewClicked: " + this.model.get("title"));
      }
    });

    return {
      "ccxScheduleTreeNodeView": ccxScheduleTreeNodeView
    };
  }
);
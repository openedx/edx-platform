var define = window.define || RequireJS.define;  // jshint ignore:line

define(
  [
    'backbone',
    'jquery',
    'underscore',
    'gettext',
    'js/ccx/model/schedule_model',
    'js/ccx/view/schedule_tree_node'
  ],
  function ( Backbone, $, _, gettext, scheduleModel, scheduleTreeNode) {
    'use strict';
    var ccxScheduleTreeView = Backbone.View.extend({
      render: function () {
        _.each(this.collection.models, this.processChapters, this);
        return this;
      },
      processChapters: function(chapter){
        var ccxScheduleTreeNode = new scheduleTreeNode.
          ccxScheduleTreeNodeView({ model: chapter });
        ccxScheduleTreeNode.render();
        this.$el.append(ccxScheduleTreeNode.el);
        _.each(chapter.toJSON().children, this.processSequential, this);

      },

      processSequential: function(sequential){
        var model = new scheduleModel.ccxScheduleModel(sequential);
        var ccxScheduleTreeNode = new scheduleTreeNode.
          ccxScheduleTreeNodeView({ model: model });
        ccxScheduleTreeNode.render();
        this.$el.append(ccxScheduleTreeNode.el);
        _.each(sequential.children, this.processVertical, this);

      },

      processVertical: function(vertical){
        var model = new scheduleModel.ccxScheduleModel(vertical);
        var ccxScheduleTreeNode = new scheduleTreeNode.
          ccxScheduleTreeNodeView({ model: model });
        ccxScheduleTreeNode.render();
        this.$el.append(ccxScheduleTreeNode.el);
      }

    });

    return {
      "ccxScheduleTreeView": ccxScheduleTreeView
    };
  }
);
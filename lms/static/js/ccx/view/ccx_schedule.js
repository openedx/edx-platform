var define = window.define || RequireJS.define;  // jshint ignore:line

define(
  [
    'backbone',
    'jquery',
    'underscore',
    'gettext',
    'js/ccx/collection/schedule_collection',
    'js/ccx/view/schedule_tree',
    'text!templates/ccx/ccx_schedule.underscore'
  ],
  function (
    Backbone,
    $,
    _,
    gettext,
    scheduleCollection,
    scheduleTree,
    scheduleTemplate
  ) {
    'use strict';
    var ccxScheduleView = Backbone.View.extend({

      initialize: function(options) {
        this.scheduleJson = options.scheduleJson;
        this.saveCCXScheduleUrl = options.saveCCXScheduleUrl;
        this.setUpCollection();
      },

      render: function() {
        this.$el.html(_.template(scheduleTemplate) ({}));
        this.splitTreeDataFromFormData();

        // Load schedule tree
        this.loadScheduleTree();

        return this;
      },

      setUpCollection: function() {
        // init and fetch collection
        this.collection.bind('reset', this.render);
      },

      splitTreeDataFromFormData: function() {
        // prepare data for schedule page components i.e form and tree.
        var scheduleJson = this.collection.toJSON();

        // Hidden data will be shown into form,
        // from there user can add this data to schedule tree
        this.scheduleFormData = this.pruned(scheduleJson, function(node) {
          return node.hidden || node.category !== 'vertical';
        });

        // This data will be render on schedule tree.
        this.scheduleTreeData = this.pruned(scheduleJson, function(node) {
          return !node.hidden;
        });
      },

      pruned: function(tree, filter) {
        // filter schedule tree
        var self = this;
        return tree.filter(filter)
          .map(function(node) {
            var copy = {};
            $.extend(copy, node);
            if (node.children) {
              copy.children = self.pruned(node.children, filter);
            }
            return copy;
          }).filter(function(node) {
            return node.children === undefined || node.children.length;
        });
      },

      loadScheduleTree: function() {
        // load schedule tree view
        if (!_.isUndefined(this.scheduleTreeData)) {
          var ccxScheduleTreeCollection = new scheduleCollection.
            ccxScheduleCollection(this.scheduleTreeData);
          var scheduleTreeView = new scheduleTree.ccxScheduleTreeView({
            el: $("#ccx-schedule_tbody"),
            collection: ccxScheduleTreeCollection
          });
          scheduleTreeView.render();
        }
      }
    });

    return {
      "ccxScheduleView": ccxScheduleView
    };
  }
);
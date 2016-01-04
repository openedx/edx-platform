var define = window.define || RequireJS.define;  // jshint ignore:line

define(
  [
    'backbone',
    'js/ccx/model/schedule_model'
  ],
  function (Backbone, scheduleModel) {
    'use strict';
    var ccxScheduleCollection = Backbone.Collection.extend({
      model: scheduleModel.ccxScheduleModel,
      url: 'ccx_schedule'
    });

    return {
      "ccxScheduleCollection": ccxScheduleCollection
    };
  }
);
var define = window.define || RequireJS.define;  // jshint ignore:line

define(
  [
    'backbone'
  ],
  function (Backbone) {
    'use strict';
    var ccxScheduleModel = Backbone.Model.extend({
      defaults: {
        location: '',
        display_name: '',
        start: null,
        due: null,
        category: '',
        hidden: false,
        children: []
      }
    });

    return {
      "ccxScheduleModel": ccxScheduleModel
    };
  }
);
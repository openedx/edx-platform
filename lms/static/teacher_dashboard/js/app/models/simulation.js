;(function (define) {
  'use strict';
  define(["backbone"], function(Backbone) {
    var SimulationModel = Backbone.Model.extend({
      defaults: {
        "display_name": '',
        "score": 0,
        "questions_answered": 0
      }
    });

    return SimulationModel;
  });
}).call(this, define || RequireJS.define);

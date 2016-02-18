;(function (define) {
  'use strict';
  define(["backbone"], function(Backbone) {
    var SimulationModel = Backbone.Model.extend({
      defaults: {
        "display_name": ''
      }
    });

    return SimulationModel;
  });
}).call(this, define || RequireJS.define);

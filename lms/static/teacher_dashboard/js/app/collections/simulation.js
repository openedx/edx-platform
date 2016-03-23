;(function (define) {
  'use strict';
  define([
    "backbone", "underscore", "teacher_dashboard/js/app/models/simulation"
  ], function(Backbone, _, SimulationModel) {
    var SimulationCollection = Backbone.Collection.extend({
      comparator: "display_name",
      model: SimulationModel,

      constructor: function(models, options) {
        Backbone.Collection.prototype.constructor.apply(this, arguments);
        this.options = options;
      },

      parse: function(response) {
        if (this.options && _.isUndefined(this.options.license)) {
          return response;
        }

        return _.map(response, function(rawModel) {
          rawModel.license = this.options.license;
          return rawModel;
        }, this);
      },

      toJSON: function(data) {
        return _.map(data, function(rawModel) {
          delete data.license;
          return rawModel;
        }, this);
      }
    }, {
      factory: function(models, options, license) {
        var collection;

        options = _.extend({license: license}, options);
        collection =  new SimulationCollection(models, options);
        return collection;
      }
    });

    return SimulationCollection;
  });
}).call(this, define || RequireJS.define);

;(function (define) {
  define(["underscore", "URI"], function (_, URI) {
    var utils = {},
        URL_BASE = "/teacher/api/v0",
        URL_TEMPLATES;

    URL_TEMPLATES = {
      "licenses": _.template("<%= base %>/licenses/"),
      "simulations": _.template("<%= base %>/licenses/<%=license_id %>/simulations/"),
      "students": _.template("<%= base %>/licenses/<%=license_id %>/simulations/<%=simulation_id %>/students/")
    };

    utils.getUrl = function(type, context, addUser) {
      var url = "";

      if (!URL_TEMPLATES[type]) {
        throw new Error("Url with type `" + type + "` does not exist.");
      }
      context = _.extend({base: URL_BASE}, context);
      url = URL_TEMPLATES[type](context);
      return url;
    };

    utils.time = function(time, formatFull) {
      var hours, minutes, seconds;


      var _pad = function (number) {
          return (number < 10 ? '0' : '') + number;
      };

      if (!_.isFinite(time) || time < 0) {
          time = 0;
      }

      seconds = Math.floor(time);
      minutes = Math.floor(seconds / 60);
      hours = Math.floor(minutes / 60);
      seconds = seconds % 60;
      minutes = minutes % 60;

      if (formatFull) {
          return '' + _pad(hours) + ':' + _pad(minutes) + ':' + _pad(seconds % 60);
      } else if (hours) {
          return '' + hours + ':' + _pad(minutes) + ':' + _pad(seconds % 60);
      } else {
          return '' + minutes + ':' + _pad(seconds % 60);
      }
    };

    return utils;
  });
}).call(this, define || RequireJS.define);

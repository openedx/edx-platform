;(function (define) {
  define(["jquery", "underscore"], function ($, _) {
    var utils = {};

    utils.getUrl = function(params) {
      var url = window.Labster.url;

      if (params) {
        url += '?' + $.param(params);
      }

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

    utils.fetch = function (collection, params) {
      return $.ajax({
        url: utils.getUrl(),
        type: 'POST',
        dataType: 'json',
        data: params || {},
        success: function(data) {
          collection.reset(data, {parse: true});
        }
      });
    };

    return utils;
  });
}).call(this, define || RequireJS.define);

/*
 * jquery.ajax-retry
 * https://github.com/johnkpaul/jquery-ajax-retry
 *
 * Copyright (c) 2012 John Paul
 * Licensed under the MIT license.
 */
(function(factory) {
    if (typeof define === 'function' && define.amd) {
      // AMD. Register as an anonymous module.
      define(['jquery'], factory);
    } else if (typeof exports === 'object') {
        // Node/CommonJS
        factory(require('jquery'));
    } else {
      // Browser globals
      factory(jQuery);
    }
})(function($) {

  // enhance all ajax requests with our retry API
  $.ajaxPrefilter(function(options, originalOptions, jqXHR) {
    jqXHR.retry = function(opts) {
      if(opts.timeout) {
        this.timeout = opts.timeout;
      }
      if (opts.statusCodes) {
        this.statusCodes = opts.statusCodes;
      }
      return this.pipe(null, pipeFailRetry(this, opts));
    };
  });

  // generates a fail pipe function that will retry `jqXHR` `times` more times
  function pipeFailRetry(jqXHR, opts) {
    var times = opts.times;
    var timeout = jqXHR.timeout;

    // takes failure data as input, returns a new deferred
    return function(input, status, msg) {
      var ajaxOptions = this;
      var output = new $.Deferred();
      var retryAfter = jqXHR.getResponseHeader('Retry-After');

      // whenever we do make this request, pipe its output to our deferred
      function nextRequest() {
        $.ajax(ajaxOptions)
          .retry({times: times - 1, timeout: opts.timeout})
          .pipe(output.resolve, output.reject);
      }

      if (times > 1 && (!jqXHR.statusCodes || $.inArray(input.status, jqXHR.statusCodes) > -1)) {
        // implement Retry-After rfc
        // http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.37
        if (retryAfter) {
          // it must be a date
          if (isNaN(retryAfter)) {
            timeout = new Date(retryAfter).getTime() - $.now();
          // its a number in seconds
          } else {
            timeout = parseInt(retryAfter, 10) * 1000;
          }
          // ensure timeout is a positive number
          if (isNaN(timeout) || timeout < 0) {
            timeout = jqXHR.timeout;
          }
        }

        if (timeout !== undefined){
          setTimeout(nextRequest, timeout);
        } else {
          nextRequest();
        }
      } else {
        // no times left, reject our deferred with the current arguments
        output.rejectWith(this, arguments);
      }

      return output;
    };
  }

});

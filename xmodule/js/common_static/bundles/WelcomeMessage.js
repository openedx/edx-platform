(function(e, a) { for(var i in a) e[i] = a[i]; }(window, webpackJsonp([36],{

/***/ "./common/static/common/js/utils/clamp-html.js":
/***/ (function(module, exports) {

/**
 * Used to ellipsize a section of arbitrary HTML after a specified number of words.
 *
 * Note: this will modify the DOM structure of root in place.
 * To keep the original around, you may want to save the result of cloneNode(true) before calling this method.
 *
 * Known bug: This method will ignore any special whitespace in the source and simply output single spaces.
 * Which means that &nbsp; will not be respected. This is not considered worth solving at time of writing.
 *
 * Returns how many words remain (or a negative number if the content got clamped)
 */
function clampHtmlByWords(root, wordsLeft) {
    'use strict';

    if (root.nodeName === 'SCRIPT' || root.nodeName === 'STYLE') {
        return wordsLeft; // early exit and ignore
    }

    var remaining = wordsLeft;
    var nodes = Array.from(root.childNodes ? root.childNodes : []);
    var words, chopped;

    // First, cut short any text in our node, as necessary
    if (root.nodeName === '#text' && root.data) {
        // split on words, ignoring any resulting empty strings
        words = root.data.split(/\s+/).filter(Boolean);
        if (remaining < 0) {
            root.data = ''; // eslint-disable-line no-param-reassign
        } else if (remaining > words.length) {
            remaining -= words.length;
        } else {
            // OK, let's add an ellipsis and cut some of root.data
            chopped = words.slice(0, remaining).join(' ') + '…';
            // But be careful to get any preceding space too
            if (root.data.match(/^\s/)) {
                chopped = ' ' + chopped;
            }
            root.data = chopped; // eslint-disable-line no-param-reassign
            remaining = -1;
        }
    }

    // Now do the same for any child nodes
    nodes.forEach(function (node) {
        if (remaining < 0) {
            root.removeChild(node);
        } else {
            remaining = clampHtmlByWords(node, remaining);
        }
    });

    return remaining;
}

module.exports = {
    clampHtmlByWords: clampHtmlByWords
};

/***/ }),

/***/ "./common/static/js/vendor/jquery.cookie.js":
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(jQuery) {/*!
 * jQuery Cookie Plugin
 * https://github.com/carhartl/jquery-cookie
 *
 * Copyright 2011, Klaus Hartl
 * Dual licensed under the MIT or GPL Version 2 licenses.
 * http://www.opensource.org/licenses/mit-license.php
 * http://www.opensource.org/licenses/GPL-2.0
 */
(function ($) {
    $.cookie = function (key, value, options) {

        // key and at least value given, set cookie...
        if (arguments.length > 1 && (!/Object/.test(Object.prototype.toString.call(value)) || value === null || value === undefined)) {
            options = $.extend({}, options);

            if (value === null || value === undefined) {
                options.expires = -1;
            }

            if (typeof options.expires === 'number') {
                var days = options.expires,
                    t = options.expires = new Date();
                t.setDate(t.getDate() + days);
            }

            value = String(value);

            return document.cookie = [encodeURIComponent(key), '=', options.raw ? value : encodeURIComponent(value), options.expires ? '; expires=' + options.expires.toUTCString() : '', // use expires attribute, max-age is not supported by IE
            options.path ? '; path=' + options.path : '', options.domain ? '; domain=' + options.domain : '', options.secure ? '; secure' : ''].join('');
        }

        // key and possibly options given, get cookie...
        options = value || {};
        var decode = options.raw ? function (s) {
            return s;
        } : decodeURIComponent;

        var pairs = document.cookie.split('; ');
        for (var i = 0, pair; pair = pairs[i] && pairs[i].split('='); i++) {
            if (decode(pair[0]) === key) return decode(pair[1] || ''); // IE saves cookies with empty string as "c; ", e.g. without "=" as opposed to EOMB, thus pair[1] may be undefined
        }
        return null;
    };
})(jQuery);
/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(0)))

/***/ }),

/***/ "./openedx/features/course_experience/static/course_experience/js/WelcomeMessage.js":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
Object.defineProperty(__webpack_exports__, "__esModule", { value: true });
/* WEBPACK VAR INJECTION */(function($) {/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "WelcomeMessage", function() { return WelcomeMessage; });
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0_jquery_cookie__ = __webpack_require__("./common/static/js/vendor/jquery.cookie.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0_jquery_cookie___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_0_jquery_cookie__);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1_gettext__ = __webpack_require__(3);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1_gettext___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_1_gettext__);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_2_common_js_utils_clamp_html__ = __webpack_require__("./common/static/common/js/utils/clamp-html.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_2_common_js_utils_clamp_html___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_2_common_js_utils_clamp_html__);
var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

/* globals $ */
 // eslint-disable-line
 // eslint-disable-line
 // eslint-disable-line

var WelcomeMessage = function () {
  _createClass(WelcomeMessage, null, [{
    key: 'dismissWelcomeMessage',
    // eslint-disable-line import/prefer-default-export

    value: function dismissWelcomeMessage(dismissUrl) {
      $.ajax({
        type: 'POST',
        url: dismissUrl,
        headers: {
          'X-CSRFToken': $.cookie('csrftoken')
        },
        success: function success() {
          $('.welcome-message').hide();
        }
      });
    }
  }]);

  function WelcomeMessage(options) {
    _classCallCheck(this, WelcomeMessage);

    // Dismiss the welcome message if the user clicks dismiss, or auto-dismiss if
    // the user doesn't click dismiss in 7 days from when it was first viewed.

    // Check to see if the welcome message has been displayed at all.
    if ($('.welcome-message').length > 0) {
      // If the welcome message has been viewed.
      if ($.cookie('welcome-message-viewed') === 'True') {
        // If the timer cookie no longer exists, dismiss the welcome message permanently.
        if ($.cookie('welcome-message-timer') !== 'True') {
          WelcomeMessage.dismissWelcomeMessage(options.dismissUrl);
        }
      } else {
        // Set both the viewed cookie and the timer cookie.
        $.cookie('welcome-message-viewed', 'True', { expires: 365 });
        $.cookie('welcome-message-timer', 'True', { expires: 7 });
      }
    }
    $('.dismiss-message button').click(function () {
      return WelcomeMessage.dismissWelcomeMessage(options.dismissUrl);
    });

    // "Show More" support for welcome messages
    var messageContent = document.querySelector('#welcome-message-content');
    var fullText = messageContent.innerHTML;
    if (__webpack_require__.i(__WEBPACK_IMPORTED_MODULE_2_common_js_utils_clamp_html__["clampHtmlByWords"])(messageContent, 100) < 0) {
      var showMoreButton = document.querySelector('#welcome-message-show-more');
      var shortText = messageContent.innerHTML;

      showMoreButton.removeAttribute('hidden');

      showMoreButton.addEventListener('click', function (event) {
        if (showMoreButton.getAttribute('data-state') === 'less') {
          showMoreButton.textContent = __WEBPACK_IMPORTED_MODULE_1_gettext___default()('Show More');
          messageContent.innerHTML = shortText;
          showMoreButton.setAttribute('data-state', 'more');
        } else {
          showMoreButton.textContent = __WEBPACK_IMPORTED_MODULE_1_gettext___default()('Show Less');
          messageContent.innerHTML = fullText;
          showMoreButton.setAttribute('data-state', 'less');
        }
        event.stopImmediatePropagation();
      });
    }
  }

  return WelcomeMessage;
}();
/* WEBPACK VAR INJECTION */}.call(__webpack_exports__, __webpack_require__(0)))

/***/ }),

/***/ 3:
/***/ (function(module, exports) {

(function() { module.exports = window["gettext"]; }());

/***/ })

},["./openedx/features/course_experience/static/course_experience/js/WelcomeMessage.js"])));
//# sourceMappingURL=WelcomeMessage.js.map
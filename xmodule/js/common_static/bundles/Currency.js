(function(e, a) { for(var i in a) e[i] = a[i]; }(window, webpackJsonp([59],{

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

/***/ "./openedx/features/course_experience/static/course_experience/js/currency.js":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
Object.defineProperty(__webpack_exports__, "__esModule", { value: true });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "Currency", function() { return Currency; });
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0_jquery_cookie__ = __webpack_require__("./common/static/js/vendor/jquery.cookie.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0_jquery_cookie___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_0_jquery_cookie__);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1_jquery__ = __webpack_require__(0);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1_jquery___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_1_jquery__);
var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }


 // eslint-disable-line import/extensions

var Currency = function () {
  _createClass(Currency, [{
    key: 'editText',
    // eslint-disable-line import/prefer-default-export

    value: function editText(price) {
      var l10nCookie = this.countryL10nData;
      var lmsregex = /(\$)([\d|.]*)( USD)/g;
      var priceText = price.text();
      var regexMatch = lmsregex.exec(priceText);
      if (regexMatch) {
        var currentPrice = regexMatch[2];
        var dollars = parseFloat(currentPrice);
        var newPrice = dollars * l10nCookie.rate;
        var newPriceString = '' + l10nCookie.symbol + Math.round(newPrice) + ' ' + l10nCookie.code;
        // Change displayed price based on edx-price-l10n cookie currency_data
        price.text(newPriceString);
      }
    }
  }, {
    key: 'setPrice',
    value: function setPrice() {
      var _this = this;

      __WEBPACK_IMPORTED_MODULE_1_jquery___default()('.upgrade-price-string').each(function (i, price) {
        // When the button includes two prices (discounted and previous)
        // we call the method twice, since it modifies one price at a time.
        // Could also be used to modify all prices on any page
        _this.editText(__WEBPACK_IMPORTED_MODULE_1_jquery___default()(price));
      });
    }
  }, {
    key: 'getCountry',
    value: function getCountry() {
      try {
        this.countryL10nData = JSON.parse(__WEBPACK_IMPORTED_MODULE_1_jquery___default.a.cookie('edx-price-l10n'));
      } catch (e) {
        if (e instanceof SyntaxError) {
          // If cookie isn't proper JSON, log but continue. This will show the purchase experience
          // in a non-local currency but will not prevent the user from interacting with the page.
          console.error(e);
          console.error("Ignoring malformed 'edx-price-l10n' cookie.");
        } else {
          throw e;
        }
      }
      if (this.countryL10nData) {
        window.analytics.track('edx.bi.user.track_selection.local_currency_cookie_set');
        this.setPrice();
      }
    }
  }]);

  function Currency() {
    var _this2 = this;

    _classCallCheck(this, Currency);

    __WEBPACK_IMPORTED_MODULE_1_jquery___default()(document).ready(function () {
      _this2.getCountry();
    });
  }

  return Currency;
}();

/***/ })

},["./openedx/features/course_experience/static/course_experience/js/currency.js"])));
//# sourceMappingURL=Currency.js.map
(function(e, a) { for(var i in a) e[i] = a[i]; }(window, webpackJsonp([42],{

/***/ "./cms/static/js/sock.js":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
Object.defineProperty(__webpack_exports__, "__esModule", { value: true });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "toggleSock", function() { return toggleSock; });
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0_domReady__ = __webpack_require__("./common/static/js/vendor/domReady.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0_domReady___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_0_domReady__);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1_jquery__ = __webpack_require__(0);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1_jquery___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_1_jquery__);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_2_jquery_smoothScroll__ = __webpack_require__("./common/static/js/vendor/jquery.smooth-scroll.min.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_2_jquery_smoothScroll___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_2_jquery_smoothScroll__);




'use strict';

var toggleSock = function toggleSock(e) {
    e.preventDefault();

    var $btnShowSockLabel = __WEBPACK_IMPORTED_MODULE_1_jquery__(this).find('.copy-show');
    var $btnHideSockLabel = __WEBPACK_IMPORTED_MODULE_1_jquery__(this).find('.copy-hide');
    var $sock = __WEBPACK_IMPORTED_MODULE_1_jquery__('.wrapper-sock');
    var $sockContent = $sock.find('.wrapper-inner');

    if ($sock.hasClass('is-shown')) {
        $sock.removeClass('is-shown');
        $sockContent.hide('fast');
        $btnHideSockLabel.removeClass('is-shown').addClass('is-hidden');
        $btnShowSockLabel.removeClass('is-hidden').addClass('is-shown');
    } else {
        $sock.addClass('is-shown');
        $sockContent.show('fast');
        $btnHideSockLabel.removeClass('is-hidden').addClass('is-shown');
        $btnShowSockLabel.removeClass('is-shown').addClass('is-hidden');
    }

    __WEBPACK_IMPORTED_MODULE_1_jquery__["smoothScroll"]({
        offset: -200,
        easing: 'swing',
        speed: 1000,
        scrollElement: null,
        scrollTarget: $sock
    });
};

__WEBPACK_IMPORTED_MODULE_0_domReady__(function () {
    // toggling footer additional support
    __WEBPACK_IMPORTED_MODULE_1_jquery__('.cta-show-sock').bind('click', toggleSock);
});



/***/ }),

/***/ "./common/static/js/vendor/domReady.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_RESULT__;/**
 * @license RequireJS domReady 2.0.1 Copyright (c) 2010-2012, The Dojo Foundation All Rights Reserved.
 * Available via the MIT or new BSD license.
 * see: http://github.com/requirejs/domReady for details
 */
/*jslint */
/*global require: false, define: false, requirejs: false,
  window: false, clearInterval: false, document: false,
  self: false, setInterval: false */

!(__WEBPACK_AMD_DEFINE_RESULT__ = function () {
    'use strict';

    var isTop,
        testDiv,
        scrollIntervalId,
        isBrowser = typeof window !== "undefined" && window.document,
        isPageLoaded = !isBrowser,
        doc = isBrowser ? document : null,
        readyCalls = [];

    function runCallbacks(callbacks) {
        var i;
        for (i = 0; i < callbacks.length; i += 1) {
            callbacks[i](doc);
        }
    }

    function callReady() {
        var callbacks = readyCalls;

        if (isPageLoaded) {
            //Call the DOM ready callbacks
            if (callbacks.length) {
                readyCalls = [];
                runCallbacks(callbacks);
            }
        }
    }

    /**
     * Sets the page as loaded.
     */
    function pageLoaded() {
        if (!isPageLoaded) {
            isPageLoaded = true;
            if (scrollIntervalId) {
                clearInterval(scrollIntervalId);
            }

            callReady();
        }
    }

    if (isBrowser) {
        if (document.addEventListener) {
            //Standards. Hooray! Assumption here that if standards based,
            //it knows about DOMContentLoaded.
            document.addEventListener("DOMContentLoaded", pageLoaded, false);
            window.addEventListener("load", pageLoaded, false);
        } else if (window.attachEvent) {
            window.attachEvent("onload", pageLoaded);

            testDiv = document.createElement('div');
            try {
                isTop = window.frameElement === null;
            } catch (e) {}

            //DOMContentLoaded approximation that uses a doScroll, as found by
            //Diego Perini: http://javascript.nwbox.com/IEContentLoaded/,
            //but modified by other contributors, including jdalton
            if (testDiv.doScroll && isTop && window.external) {
                scrollIntervalId = setInterval(function () {
                    try {
                        testDiv.doScroll();
                        pageLoaded();
                    } catch (e) {}
                }, 30);
            }
        }

        //Check if document already complete, and if so, just trigger page load
        //listeners. Latest webkit browsers also use "interactive", and
        //will fire the onDOMContentLoaded before "interactive" but not after
        //entering "interactive" or "complete". More details:
        //http://dev.w3.org/html5/spec/the-end.html#the-end
        //http://stackoverflow.com/questions/3665561/document-readystate-of-interactive-vs-ondomcontentloaded
        //Hmm, this is more complicated on further use, see "firing too early"
        //bug: https://github.com/requirejs/domReady/issues/1
        //so removing the || document.readyState === "interactive" test.
        //There is still a window.onload binding that should get fired if
        //DOMContentLoaded is missed.
        if (document.readyState === "complete") {
            pageLoaded();
        }
    }

    /** START OF PUBLIC API **/

    /**
     * Registers a callback for DOM ready. If DOM is already ready, the
     * callback is called immediately.
     * @param {Function} callback
     */
    function domReady(callback) {
        if (isPageLoaded) {
            callback(doc);
        } else {
            readyCalls.push(callback);
        }
        return domReady;
    }

    domReady.version = '2.0.1';

    /**
     * Loader Plugin API method
     */
    domReady.load = function (name, req, onLoad, config) {
        if (config.isBuild) {
            onLoad(null);
        } else {
            domReady(onLoad);
        }
    };

    /** END OF PUBLIC API **/

    return domReady;
}.call(exports, __webpack_require__, exports, module),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ }),

/***/ "./common/static/js/vendor/jquery.smooth-scroll.min.js":
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(jQuery) {/*!
 * Smooth Scroll - v1.4.10 - 2013-03-02
 * https://github.com/kswedberg/jquery-smooth-scroll
 * Copyright (c) 2013 Karl Swedberg
 * Licensed MIT (https://github.com/kswedberg/jquery-smooth-scroll/blob/master/LICENSE-MIT)
 */
(function (l) {
  function t(l) {
    return l.replace(/(:|\.)/g, "\\$1");
  }var e = "1.4.10",
      o = { exclude: [], excludeWithin: [], offset: 0, direction: "top", scrollElement: null, scrollTarget: null, beforeScroll: function beforeScroll() {}, afterScroll: function afterScroll() {}, easing: "swing", speed: 400, autoCoefficent: 2 },
      r = function r(t) {
    var e = [],
        o = !1,
        r = t.dir && "left" == t.dir ? "scrollLeft" : "scrollTop";return this.each(function () {
      if (this != document && this != window) {
        var t = l(this);t[r]() > 0 ? e.push(this) : (t[r](1), o = t[r]() > 0, o && e.push(this), t[r](0));
      }
    }), e.length || this.each(function () {
      "BODY" === this.nodeName && (e = [this]);
    }), "first" === t.el && e.length > 1 && (e = [e[0]]), e;
  };l.fn.extend({ scrollable: function scrollable(l) {
      var t = r.call(this, { dir: l });return this.pushStack(t);
    }, firstScrollable: function firstScrollable(l) {
      var t = r.call(this, { el: "first", dir: l });return this.pushStack(t);
    }, smoothScroll: function smoothScroll(e) {
      e = e || {};var o = l.extend({}, l.fn.smoothScroll.defaults, e),
          r = l.smoothScroll.filterPath(location.pathname);return this.unbind("click.smoothscroll").bind("click.smoothscroll", function (e) {
        var n = this,
            s = l(this),
            c = o.exclude,
            i = o.excludeWithin,
            a = 0,
            f = 0,
            h = !0,
            u = {},
            d = location.hostname === n.hostname || !n.hostname,
            m = o.scrollTarget || (l.smoothScroll.filterPath(n.pathname) || r) === r,
            p = t(n.hash);if (o.scrollTarget || d && m && p) {
          for (; h && c.length > a;) {
            s.is(t(c[a++])) && (h = !1);
          }for (; h && i.length > f;) {
            s.closest(i[f++]).length && (h = !1);
          }
        } else h = !1;h && (e.preventDefault(), l.extend(u, o, { scrollTarget: o.scrollTarget || p, link: n }), l.smoothScroll(u));
      }), this;
    } }), l.smoothScroll = function (t, e) {
    var o,
        r,
        n,
        s,
        c = 0,
        i = "offset",
        a = "scrollTop",
        f = {},
        h = {};"number" == typeof t ? (o = l.fn.smoothScroll.defaults, n = t) : (o = l.extend({}, l.fn.smoothScroll.defaults, t || {}), o.scrollElement && (i = "position", "static" == o.scrollElement.css("position") && o.scrollElement.css("position", "relative"))), o = l.extend({ link: null }, o), a = "left" == o.direction ? "scrollLeft" : a, o.scrollElement ? (r = o.scrollElement, c = r[a]()) : r = l("html, body").firstScrollable(), o.beforeScroll.call(r, o), n = "number" == typeof t ? t : e || l(o.scrollTarget)[i]() && l(o.scrollTarget)[i]()[o.direction] || 0, f[a] = n + c + o.offset, s = o.speed, "auto" === s && (s = f[a] || r.scrollTop(), s /= o.autoCoefficent), h = { duration: s, easing: o.easing, complete: function complete() {
        o.afterScroll.call(o.link, o);
      } }, o.step && (h.step = o.step), r.length ? r.stop().animate(f, h) : o.afterScroll.call(o.link, o);
  }, l.smoothScroll.version = e, l.smoothScroll.filterPath = function (l) {
    return l.replace(/^\//, "").replace(/(index|default).[a-zA-Z]{3,4}$/, "").replace(/\/$/, "");
  }, l.fn.smoothScroll.defaults = o;
})(jQuery);
/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(0)))

/***/ })

},["./cms/static/js/sock.js"])));
//# sourceMappingURL=sock.js.map
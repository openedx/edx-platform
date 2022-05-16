(function(e, a) { for(var i in a) e[i] = a[i]; }(window, webpackJsonp([57],{

/***/ "./lms/static/completion/js/CompletionOnViewService.js":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
Object.defineProperty(__webpack_exports__, "__esModule", { value: true });
/* WEBPACK VAR INJECTION */(function($) {/* harmony export (immutable) */ __webpack_exports__["markBlocksCompletedOnViewIfNeeded"] = markBlocksCompletedOnViewIfNeeded;
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0__ViewedEvent__ = __webpack_require__("./lms/static/completion/js/ViewedEvent.js");


var completedBlocksKeys = new Set();

function markBlocksCompletedOnViewIfNeeded(runtime, containerElement) {
  var blockElements = $(containerElement).find('.xblock-student_view[data-mark-completed-on-view-after-delay]').get();

  if (blockElements.length > 0) {
    var tracker = new __WEBPACK_IMPORTED_MODULE_0__ViewedEvent__["a" /* ViewedEventTracker */]();

    blockElements.forEach(function (blockElement) {
      var markCompletedOnViewAfterDelay = parseInt(blockElement.dataset.markCompletedOnViewAfterDelay, 10);
      if (markCompletedOnViewAfterDelay >= 0) {
        tracker.addElement(blockElement, markCompletedOnViewAfterDelay);
      }
    });

    tracker.addHandler(function (blockElement, event) {
      var blockKey = blockElement.dataset.usageId;
      if (blockKey && !completedBlocksKeys.has(blockKey)) {
        if (event.elementHasBeenViewed) {
          $.ajax({
            type: 'POST',
            url: runtime.handlerUrl(blockElement, 'publish_completion'),
            data: JSON.stringify({
              completion: 1.0
            })
          }).then(function () {
            completedBlocksKeys.add(blockKey);
            blockElement.dataset.markCompletedOnViewAfterDelay = 0;
          });
        }
      }
    });
  }
}
/* WEBPACK VAR INJECTION */}.call(__webpack_exports__, __webpack_require__(0)))

/***/ }),

/***/ "./lms/static/completion/js/ViewedEvent.js":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
/* unused harmony export ElementViewing */
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "a", function() { return ViewedEventTracker; });
var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

/** Ensure that a function is only run once every `wait` milliseconds */
function throttle(fn, wait) {
  var time = 0;
  function delay() {
    // Do not call the function until at least `wait` seconds after the
    // last time the function was called.
    var now = Date.now();
    if (time + wait < now) {
      time = now;
      fn();
    }
  }
  return delay;
}

var ElementViewing = function () {
  /**
   * A wrapper for an HTMLElement that tracks whether the element has been
   * viewed or not.
   */
  function ElementViewing(el, viewedAfterMs, callback) {
    _classCallCheck(this, ElementViewing);

    this.el = el;
    this.viewedAfterMs = viewedAfterMs;
    this.callback = callback;

    this.topSeen = false;
    this.bottomSeen = false;
    this.seenForMs = 0;
    this.becameVisibleAt = undefined;
    this.hasBeenViewed = false;
  }

  _createClass(ElementViewing, [{
    key: "getBoundingRect",
    value: function getBoundingRect() {
      return this.el.getBoundingClientRect();
    }

    /** This element has become visible on screen.
     *
     * (may be called even when already on screen though)
     */

  }, {
    key: "handleVisible",
    value: function handleVisible() {
      var _this = this;

      if (!this.becameVisibleAt) {
        this.becameVisibleAt = Date.now();
        // We're now visible; after viewedAfterMs, if the top and bottom have been
        // seen, this block will count as viewed.
        setTimeout(function () {
          _this.checkIfViewed();
        }, this.viewedAfterMs - this.seenForMs);
      }
    }
  }, {
    key: "handleNotVisible",
    value: function handleNotVisible() {
      if (this.becameVisibleAt) {
        this.seenForMs = Date.now() - this.becameVisibleAt;
      }
      this.becameVisibleAt = undefined;
    }
  }, {
    key: "markTopSeen",
    value: function markTopSeen() {
      // If this element has been seen for enough time, but the top wasn't visible, it may now be
      // considered viewed.
      this.topSeen = true;
      this.checkIfViewed();
    }
  }, {
    key: "markBottomSeen",
    value: function markBottomSeen() {
      this.bottomSeen = true;
      this.checkIfViewed();
    }
  }, {
    key: "getTotalTimeSeen",
    value: function getTotalTimeSeen() {
      if (this.becameVisibleAt) {
        return this.seenForMs + (Date.now() - this.becameVisibleAt);
      }
      return this.seenForMs;
    }
  }, {
    key: "areViewedCriteriaMet",
    value: function areViewedCriteriaMet() {
      return this.topSeen && this.bottomSeen && this.getTotalTimeSeen() >= this.viewedAfterMs;
    }
  }, {
    key: "checkIfViewed",
    value: function checkIfViewed() {
      // User can provide a "now" value for testing purposes.
      if (this.hasBeenViewed) {
        return;
      }
      if (this.areViewedCriteriaMet()) {
        this.hasBeenViewed = true;
        // Report to the tracker that we have been viewed
        this.callback(this.el, { elementHasBeenViewed: this.hasBeenViewed });
      }
    }
  }]);

  return ElementViewing;
}();

var ViewedEventTracker = function () {
  /**
   * When the top or bottom of an element is first viewed, and the entire
   * element is viewed for a specified amount of time, the callback is called,
   * passing the element that was viewed, and an event object having the
   * following field:
   *
   * *   hasBeenViewed (bool): true if all the conditions for being
   *     considered "viewed" have been met.
   */
  function ViewedEventTracker() {
    _classCallCheck(this, ViewedEventTracker);

    this.elementViewings = new Set();
    this.handlers = [];
    this.registerDomHandlers();
  }

  /** Add an element to track.  */


  _createClass(ViewedEventTracker, [{
    key: "addElement",
    value: function addElement(element, viewedAfterMs) {
      var _this2 = this;

      this.elementViewings.add(new ElementViewing(element, viewedAfterMs, function (el, event) {
        return _this2.callHandlers(el, event);
      }));
      this.updateVisible();
    }

    /** Register a new handler to be called when an element has been viewed.  */

  }, {
    key: "addHandler",
    value: function addHandler(handler) {
      this.handlers.push(handler);
    }

    /** Mark which elements are currently visible.
     *
     *  Also marks when an elements top or bottom has been seen.
     * */

  }, {
    key: "updateVisible",
    value: function updateVisible() {
      this.elementViewings.forEach(function (elv) {
        if (elv.hasBeenViewed) {
          return;
        }

        var now = Date.now(); // Use the same "now" for all calculations
        var rect = elv.getBoundingRect();
        var visible = false;

        if (rect.top > 0 && rect.top < window.innerHeight) {
          elv.markTopSeen(now);
          visible = true;
        }
        if (rect.bottom > 0 && rect.bottom < window.innerHeight) {
          elv.markBottomSeen(now);
          visible = true;
        }
        if (rect.top < 0 && rect.bottom > window.innerHeight) {
          visible = true;
        }

        if (visible) {
          elv.handleVisible(now);
        } else {
          elv.handleNotVisible(now);
        }
      });
    }
  }, {
    key: "registerDomHandlers",
    value: function registerDomHandlers() {
      var _this3 = this;

      window.onscroll = throttle(function () {
        return _this3.updateVisible();
      }, 100);
      window.onresize = throttle(function () {
        return _this3.updateVisible();
      }, 100);
      this.updateVisible();
    }

    /** Call the handlers for all newly-viewed elements and pause tracking
     *  for recently disappeared elements.
     */

  }, {
    key: "callHandlers",
    value: function callHandlers(el, event) {
      this.handlers.forEach(function (handler) {
        handler(el, event);
      });
    }
  }]);

  return ViewedEventTracker;
}();

/***/ })

},["./lms/static/completion/js/CompletionOnViewService.js"])));
//# sourceMappingURL=CompletionOnViewService.js.map
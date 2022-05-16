(function(e, a) { for(var i in a) e[i] = a[i]; }(window, webpackJsonp([43],{

/***/ "./node_modules/edx-ui-toolkit/src/js/utils/constants.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;/**
 * Reusable constants.
 */
(function(define) {
    'use strict';
    !(__WEBPACK_AMD_DEFINE_ARRAY__ = [], __WEBPACK_AMD_DEFINE_RESULT__ = function() {
        /**
         * Reusable constants.
         *
         * ### keys - A mapping of key names to their corresponding identifiers.
         * ### keyCodes - A mapping of key names to their corresponding keyCodes (DEPRECATED).
         *
         * - `constants.keys.tab` - the tab key
         * - `constants.keys.enter` - the enter key
         * - `constants.keys.esc` - the escape key
         * - `constants.keys.space` - the space key
         * - `constants.keys.left` - the left arrow key
         * - `constants.keys.up` - the up arrow key
         * - `constants.keys.right` - the right arrow key
         * - `constants.keys.down` - the down arrow key
         *
         * @class constants
         */
        return {
            keys: {
                tab: 'Tab',
                enter: 'Enter',
                esc: 'Escape',
                space: 'Space',
                left: 'ArrowLeft',
                up: 'ArrowUp',
                right: 'ArrowRight',
                down: 'ArrowDown'
            },
            // NOTE: keyCode is deprecated. Use the `key` or `code` event property if possible.
            // See: https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/keyCode
            keyCodes: {
                tab: 9,
                enter: 13,
                esc: 27,
                space: 32,
                left: 37,
                up: 38,
                right: 39,
                down: 40
            }
        };
    }.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));
}).call(
    this,
    // Pick a define function as follows:
    // 1. Use the default 'define' function if it is available
    // 2. If not, use 'RequireJS.define' if that is available
    // 3. else use the GlobalLoader to install the class into the edx namespace
    // eslint-disable-next-line no-nested-ternary
    __webpack_require__("./node_modules/webpack/buildin/amd-define.js")
);


/***/ }),

/***/ "./openedx/features/course_experience/static/course_experience/js/CourseOutline.js":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
Object.defineProperty(__webpack_exports__, "__esModule", { value: true });
/* WEBPACK VAR INJECTION */(function($) {/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "CourseOutline", function() { return CourseOutline; });
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0_edx_ui_toolkit_js_utils_constants__ = __webpack_require__("./node_modules/edx-ui-toolkit/src/js/utils/constants.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0_edx_ui_toolkit_js_utils_constants___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_0_edx_ui_toolkit_js_utils_constants__);
function _toConsumableArray(arr) { if (Array.isArray(arr)) { for (var i = 0, arr2 = Array(arr.length); i < arr.length; i++) { arr2[i] = arr[i]; } return arr2; } else { return Array.from(arr); } }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

/* globals Logger */



// @TODO: Figure out how to make webpack handle default exports when libraryTarget: 'window'
var CourseOutline = // eslint-disable-line import/prefer-default-export
function CourseOutline() {
  _classCallCheck(this, CourseOutline);

  var focusable = [].concat(_toConsumableArray(document.querySelectorAll('.outline-item.focusable')));

  focusable.forEach(function (el) {
    return el.addEventListener('keydown', function (event) {
      var index = focusable.indexOf(event.target);

      switch (event.key) {// eslint-disable-line default-case
        case __WEBPACK_IMPORTED_MODULE_0_edx_ui_toolkit_js_utils_constants__["keys"].down:
          event.preventDefault();
          focusable[Math.min(index + 1, focusable.length - 1)].focus();
          break;
        case __WEBPACK_IMPORTED_MODULE_0_edx_ui_toolkit_js_utils_constants__["keys"].up:
          // @TODO: Get these from the UI Toolkit
          event.preventDefault();
          focusable[Math.max(index - 1, 0)].focus();
          break;
      }
    });
  });

  [].concat(_toConsumableArray(document.querySelectorAll('a:not([href^="#"])'))).forEach(function (link) {
    return link.addEventListener('click', function (event) {
      Logger.log('edx.ui.lms.link_clicked', {
        current_url: window.location.href,
        target_url: event.currentTarget.href
      });
    });
  });

  function expandSection(sectionToggleButton) {
    var $toggleButtonChevron = $(sectionToggleButton).children('.fa-chevron-right');
    var $contentPanel = $(document.getElementById(sectionToggleButton.getAttribute('aria-controls')));

    $contentPanel.slideDown();
    $contentPanel.removeClass('is-hidden');
    $toggleButtonChevron.addClass('fa-rotate-90');
    sectionToggleButton.setAttribute('aria-expanded', 'true');
  }

  function collapseSection(sectionToggleButton) {
    var $toggleButtonChevron = $(sectionToggleButton).children('.fa-chevron-right');
    var $contentPanel = $(document.getElementById(sectionToggleButton.getAttribute('aria-controls')));

    $contentPanel.slideUp();
    $contentPanel.addClass('is-hidden');
    $toggleButtonChevron.removeClass('fa-rotate-90');
    sectionToggleButton.setAttribute('aria-expanded', 'false');
  }

  [].concat(_toConsumableArray(document.querySelectorAll('.accordion'))).forEach(function (accordion) {
    var sections = Array.prototype.slice.call(accordion.querySelectorAll('.accordion-trigger'));

    sections.forEach(function (section) {
      return section.addEventListener('click', function (event) {
        var sectionToggleButton = event.currentTarget;
        if (sectionToggleButton.classList.contains('accordion-trigger')) {
          var isExpanded = sectionToggleButton.getAttribute('aria-expanded') === 'true';
          if (!isExpanded) {
            expandSection(sectionToggleButton);
          } else if (isExpanded) {
            collapseSection(sectionToggleButton);
          }
          event.stopImmediatePropagation();
        }
      });
    });
  });

  var toggleAllButton = document.querySelector('#expand-collapse-outline-all-button');
  var toggleAllSpan = document.querySelector('#expand-collapse-outline-all-span');
  var extraPaddingClass = 'expand-collapse-outline-all-extra-padding';
  toggleAllButton.addEventListener('click', function (event) {
    var toggleAllExpanded = toggleAllButton.getAttribute('aria-expanded') === 'true';
    var sectionAction = void 0;
    /* globals gettext */
    if (toggleAllExpanded) {
      toggleAllButton.setAttribute('aria-expanded', 'false');
      sectionAction = collapseSection;
      toggleAllSpan.classList.add(extraPaddingClass);
      toggleAllSpan.innerText = gettext('Expand All');
    } else {
      toggleAllButton.setAttribute('aria-expanded', 'true');
      sectionAction = expandSection;
      toggleAllSpan.classList.remove(extraPaddingClass);
      toggleAllSpan.innerText = gettext('Collapse All');
    }
    var sections = Array.prototype.slice.call(document.querySelectorAll('.accordion-trigger'));
    sections.forEach(function (sectionToggleButton) {
      sectionAction(sectionToggleButton);
    });
    event.stopImmediatePropagation();
  });

  var urlHash = window.location.hash;

  if (urlHash !== '') {
    var button = document.getElementById(urlHash.substr(1, urlHash.length));
    if (button.classList.contains('subsection-text')) {
      var parentLi = button.closest('.section');
      var parentButton = parentLi.querySelector('.section-name');
      expandSection(parentButton);
    }
    expandSection(button);
  }
};
/* WEBPACK VAR INJECTION */}.call(__webpack_exports__, __webpack_require__(0)))

/***/ })

},["./openedx/features/course_experience/static/course_experience/js/CourseOutline.js"])));
//# sourceMappingURL=CourseOutline.js.map
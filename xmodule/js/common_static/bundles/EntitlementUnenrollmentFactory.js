(function(e, a) { for(var i in a) e[i] = a[i]; }(window, webpackJsonp([56],{

/***/ "./lms/static/js/learner_dashboard/entitlement_unenrollment_factory.js":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
Object.defineProperty(__webpack_exports__, "__esModule", { value: true });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "EntitlementUnenrollmentFactory", function() { return EntitlementUnenrollmentFactory; });
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0__views_entitlement_unenrollment_view__ = __webpack_require__("./lms/static/js/learner_dashboard/views/entitlement_unenrollment_view.js");


function EntitlementUnenrollmentFactory(options) {
  return new __WEBPACK_IMPORTED_MODULE_0__views_entitlement_unenrollment_view__["a" /* default */](options);
}

 // eslint-disable-line import/prefer-default-export

/***/ }),

/***/ "./lms/static/js/learner_dashboard/views/entitlement_unenrollment_view.js":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
/* WEBPACK VAR INJECTION */(function($) {/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0_backbone__ = __webpack_require__(2);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0_backbone___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_0_backbone__);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1_edx_ui_toolkit_js_utils_html_utils__ = __webpack_require__("./node_modules/edx-ui-toolkit/src/js/utils/html-utils.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1_edx_ui_toolkit_js_utils_html_utils___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_1_edx_ui_toolkit_js_utils_html_utils__);
var _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; };

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _possibleConstructorReturn(self, call) { if (!self) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return call && (typeof call === "object" || typeof call === "function") ? call : self; }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function, not " + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass; }

/* globals gettext */





var EntitlementUnenrollmentView = function (_Backbone$View) {
  _inherits(EntitlementUnenrollmentView, _Backbone$View);

  function EntitlementUnenrollmentView(options) {
    _classCallCheck(this, EntitlementUnenrollmentView);

    var defaults = {
      el: '.js-entitlement-unenrollment-modal'
    };
    return _possibleConstructorReturn(this, (EntitlementUnenrollmentView.__proto__ || Object.getPrototypeOf(EntitlementUnenrollmentView)).call(this, _extends({}, defaults, options)));
  }

  _createClass(EntitlementUnenrollmentView, [{
    key: 'initialize',
    value: function initialize(options) {
      var view = this;

      this.closeButtonSelector = '.js-entitlement-unenrollment-modal .js-entitlement-unenrollment-modal-close-btn';
      this.headerTextSelector = '.js-entitlement-unenrollment-modal .js-entitlement-unenrollment-modal-header-text';
      this.errorTextSelector = '.js-entitlement-unenrollment-modal .js-entitlement-unenrollment-modal-error-text';
      this.submitButtonSelector = '.js-entitlement-unenrollment-modal .js-entitlement-unenrollment-modal-submit';
      this.triggerSelector = '.js-entitlement-action-unenroll';
      this.mainPageSelector = '#dashboard-main';
      this.genericErrorMsg = gettext('Your unenrollment request could not be processed. Please try again later.');
      this.modalId = '#' + this.$el.attr('id');

      this.dashboardPath = options.dashboardPath;
      this.signInPath = options.signInPath;
      this.browseCourses = options.browseCourses;
      this.isEdx = options.isEdx;

      this.$submitButton = $(this.submitButtonSelector);
      this.$closeButton = $(this.closeButtonSelector);
      this.$headerText = $(this.headerTextSelector);
      this.$errorText = $(this.errorTextSelector);

      this.$submitButton.on('click', this.handleSubmit.bind(this));

      $(this.triggerSelector).each(function setUpTrigger() {
        var $trigger = $(this);

        $trigger.on('click', view.handleTrigger.bind(view));

        // From accessibility_tools.js
        if (window.accessible_modal) {
          window.accessible_modal('#' + $trigger.attr('id'), view.closeButtonSelector, '#' + view.$el.attr('id'), view.mainPageSelector);
        }
      });
    }
  }, {
    key: 'handleTrigger',
    value: function handleTrigger(event) {
      var $trigger = $(event.target);
      var courseName = $trigger.data('courseName');
      var courseNumber = $trigger.data('courseNumber');
      var apiEndpoint = $trigger.data('entitlementApiEndpoint');

      this.$previouslyFocusedElement = $trigger;

      this.resetModal();
      this.setHeaderText(courseName, courseNumber);
      this.setSubmitData(apiEndpoint);
      this.$el.css('position', 'fixed');
    }
  }, {
    key: 'handleSubmit',
    value: function handleSubmit() {
      var apiEndpoint = this.$submitButton.data('entitlementApiEndpoint');

      if (apiEndpoint === undefined) {
        this.setError(this.genericErrorMsg);
        return;
      }

      this.$submitButton.prop('disabled', true);
      $.ajax({
        url: apiEndpoint,
        method: 'DELETE',
        complete: this.onComplete.bind(this)
      });
    }
  }, {
    key: 'resetModal',
    value: function resetModal() {
      this.$submitButton.removeData();
      this.$submitButton.prop('disabled', false);
      this.$headerText.empty();
      this.$errorText.removeClass('entitlement-unenrollment-modal-error-text-visible');
      this.$errorText.empty();
    }
  }, {
    key: 'setError',
    value: function setError(message) {
      this.$submitButton.prop('disabled', true);
      this.$errorText.empty();
      __WEBPACK_IMPORTED_MODULE_1_edx_ui_toolkit_js_utils_html_utils___default.a.setHtml(this.$errorText, message);
      this.$errorText.addClass('entitlement-unenrollment-modal-error-text-visible');
    }
  }, {
    key: 'setHeaderText',
    value: function setHeaderText(courseName, courseNumber) {
      this.$headerText.empty();
      __WEBPACK_IMPORTED_MODULE_1_edx_ui_toolkit_js_utils_html_utils___default.a.setHtml(this.$headerText, __WEBPACK_IMPORTED_MODULE_1_edx_ui_toolkit_js_utils_html_utils___default.a.interpolateHtml(gettext('Are you sure you want to unenroll from {courseName} ({courseNumber})? You will be refunded the amount you paid.'), // eslint-disable-line max-len
      {
        courseName: courseName,
        courseNumber: courseNumber
      }));
    }
  }, {
    key: 'setSubmitData',
    value: function setSubmitData(apiEndpoint) {
      this.$submitButton.removeData();
      this.$submitButton.data('entitlementApiEndpoint', apiEndpoint);
    }
  }, {
    key: 'switchToSlideOne',
    value: function switchToSlideOne() {
      this.$('.entitlement-unenrollment-modal-inner-wrapper header').addClass('hidden');
      this.$('.entitlement-unenrollment-modal-submit-wrapper').addClass('hidden');
      this.$('.slide1').removeClass('hidden');
      this.$('.entitlement-unenrollment-modal-inner-wrapper').prevObject.addClass('entitlement-unenrollment-modal-long-survey');

      // From accessibility_tools.js
      window.trapFocusForAccessibleModal(this.$previouslyFocusedElement, window.focusableElementsString, this.closeButtonSelector, this.modalId, this.mainPageSelector);
    }
  }, {
    key: 'switchToSlideTwo',
    value: function switchToSlideTwo() {
      var price = this.$(".reasons_survey input[name='priceEntitlementUnenrollment']:checked").val();
      var dissastisfied = this.$(".reasons_survey input[name='dissastisfiedEntitlementUnenrollment']:checked").val();
      var difficult = this.$(".reasons_survey input[name='difficultEntitlementUnenrollment']:checked").val();
      var time = this.$(".reasons_survey input[name='timeEntitlementUnenrollment']:checked").val();
      var unavailable = this.$(".reasons_survey input[name='unavailableEntitlementUnenrollment']:checked").val();
      var email = this.$(".reasons_survey input[name='emailEntitlementUnenrollment']:checked").val();

      if (price || dissastisfied || difficult || time || unavailable || email) {
        var results = { price: price, dissastisfied: dissastisfied, difficult: difficult, time: time, unavailable: unavailable, email: email };

        window.analytics.track('entitlement_unenrollment_reason.selected', {
          category: 'user-engagement',
          label: JSON.stringify(results),
          displayName: 'v1'
        });
      }
      this.$('.slide1').addClass('hidden');
      this.$('.slide2').removeClass('hidden');
      this.$('.entitlement-unenrollment-modal-inner-wrapper').prevObject.removeClass('entitlement-unenrollment-modal-long-survey');

      // From accessibility_tools.js
      window.trapFocusForAccessibleModal(this.$previouslyFocusedElement, window.focusableElementsString, this.closeButtonSelector, this.modalId, this.mainPageSelector);
    }
  }, {
    key: 'onComplete',
    value: function onComplete(xhr) {
      var status = xhr.status;
      var message = xhr.responseJSON && xhr.responseJSON.detail;

      if (status === 204) {
        if (this.isEdx) {
          this.switchToSlideOne();
          this.$('.reasons_survey:first .submit-reasons').click(this.switchToSlideTwo.bind(this));
        } else {
          EntitlementUnenrollmentView.redirectTo(this.dashboardPath);
        }
      } else if (status === 401 && message === 'Authentication credentials were not provided.') {
        EntitlementUnenrollmentView.redirectTo(this.signInPath + '?next=' + encodeURIComponent(this.dashboardPath));
      } else {
        this.setError(this.genericErrorMsg);
      }
    }
  }], [{
    key: 'redirectTo',
    value: function redirectTo(path) {
      window.location.href = path;
    }
  }]);

  return EntitlementUnenrollmentView;
}(__WEBPACK_IMPORTED_MODULE_0_backbone___default.a.View);

/* harmony default export */ __webpack_exports__["a"] = (EntitlementUnenrollmentView);
/* WEBPACK VAR INJECTION */}.call(__webpack_exports__, __webpack_require__(0)))

/***/ })

},["./lms/static/js/learner_dashboard/entitlement_unenrollment_factory.js"])));
//# sourceMappingURL=EntitlementUnenrollmentFactory.js.map
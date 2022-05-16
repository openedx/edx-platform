(function(e, a) { for(var i in a) e[i] = a[i]; }(window, webpackJsonp([55],{

/***/ "./lms/static/js/learner_dashboard/unenrollment_factory.js":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
Object.defineProperty(__webpack_exports__, "__esModule", { value: true });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "UnenrollmentFactory", function() { return UnenrollmentFactory; });
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0__views_unenroll_view__ = __webpack_require__("./lms/static/js/learner_dashboard/views/unenroll_view.js");


function UnenrollmentFactory(options) {
  return new __WEBPACK_IMPORTED_MODULE_0__views_unenroll_view__["a" /* default */](options);
}

 // eslint-disable-line import/prefer-default-export

/***/ }),

/***/ "./lms/static/js/learner_dashboard/views/unenroll_view.js":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
/* WEBPACK VAR INJECTION */(function($) {/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0_backbone__ = __webpack_require__(2);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0_backbone___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_0_backbone__);
var _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; };

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _possibleConstructorReturn(self, call) { if (!self) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return call && (typeof call === "object" || typeof call === "function") ? call : self; }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function, not " + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass; }

/* globals gettext */



var UnenrollView = function (_Backbone$View) {
  _inherits(UnenrollView, _Backbone$View);

  function UnenrollView(options) {
    _classCallCheck(this, UnenrollView);

    var defaults = {
      el: '.unenroll-modal'
    };
    return _possibleConstructorReturn(this, (UnenrollView.__proto__ || Object.getPrototypeOf(UnenrollView)).call(this, _extends({}, defaults, options)));
  }

  _createClass(UnenrollView, [{
    key: 'handleTrigger',
    value: function handleTrigger(triggerElement) {
      this.$previouslyFocusedElement = triggerElement;
    }
  }, {
    key: 'switchToSlideOne',
    value: function switchToSlideOne() {
      // Randomize survey option order
      var survey = document.querySelector('.options');
      for (var i = survey.children.length - 1; i >= 0; i -= 1) {
        survey.appendChild(survey.children[Math.trunc(Math.random() * i)]);
      }
      this.$('.inner-wrapper header').hide();
      this.$('#unenroll_form').hide();
      this.$('.slide1').removeClass('hidden');

      if (window.trapFocusForAccessibleModal) {
        window.trapFocusForAccessibleModal(this.$previouslyFocusedElement, window.focusableElementsString, this.closeButtonSelector, this.modalId, this.mainPageSelector);
      }
    }
  }, {
    key: 'switchToSlideTwo',
    value: function switchToSlideTwo() {
      var reason = this.$(".reasons_survey input[name='reason']:checked").attr('val');
      var courserunKey = $('#unenroll_course_id').val() + $('#unenroll_course_number').val();
      if (reason === 'Other') {
        reason = this.$('.other_text').val();
      }
      if (reason) {
        window.analytics.track('unenrollment_reason.selected', {
          category: 'user-engagement',
          label: reason,
          displayName: 'v1',
          course_id: courserunKey
        });
      }
      this.$('.slide1').addClass('hidden');
      this.$('.survey_course_name').text(this.$('#unenroll_course_name').text());
      this.$('.slide2').removeClass('hidden');
      this.$('.reasons_survey .return_to_dashboard').attr('href', this.urls.dashboard);
      this.$('.reasons_survey .browse_courses').attr('href', this.urls.browseCourses);

      if (window.trapFocusForAccessibleModal) {
        window.trapFocusForAccessibleModal(this.$previouslyFocusedElement, window.focusableElementsString, this.closeButtonSelector, this.modalId, this.mainPageSelector);
      }
    }
  }, {
    key: 'unenrollComplete',
    value: function unenrollComplete(event, xhr) {
      if (xhr.status === 200) {
        if (!this.isEdx) {
          location.href = this.urls.dashboard;
        } else {
          this.switchToSlideOne();
          this.$('.reasons_survey:first .submit_reasons').click(this.switchToSlideTwo.bind(this));
        }
      } else if (xhr.status === 403) {
        location.href = this.urls.signInUser + '?course_id=' + encodeURIComponent($('#unenroll_course_id').val()) + '&enrollment_action=unenroll';
      } else {
        $('#unenroll_error').text(gettext('Unable to determine whether we should give you a refund because' + ' of System Error. Please try again later.')).stop().css('display', 'block');
      }
    }
  }, {
    key: 'startSubmit',
    value: function startSubmit() {
      this.$('.submit').prop('disabled', true);
    }
  }, {
    key: 'initialize',
    value: function initialize(options) {
      var view = this;
      this.urls = options.urls;
      this.isEdx = options.isEdx;

      this.closeButtonSelector = '.unenroll-modal .close-modal';
      this.$closeButton = $(this.closeButtonSelector);
      this.modalId = '#' + this.$el.attr('id');
      this.mainPageSelector = '#dashboard-main';

      this.triggerSelector = '.action-unenroll';
      $(this.triggerSelector).each(function (index, element) {
        $(element).on('click', view.handleTrigger.bind($(element)));
      });

      this.$('.submit .submit-button').on('click', this.startSubmit.bind(this));
      $('#unenroll_form').on('ajax:complete', this.unenrollComplete.bind(this));
    }
  }]);

  return UnenrollView;
}(__WEBPACK_IMPORTED_MODULE_0_backbone___default.a.View);

/* harmony default export */ __webpack_exports__["a"] = (UnenrollView);
/* WEBPACK VAR INJECTION */}.call(__webpack_exports__, __webpack_require__(0)))

/***/ })

},["./lms/static/js/learner_dashboard/unenrollment_factory.js"])));
//# sourceMappingURL=UnenrollmentFactory.js.map
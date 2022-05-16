(function(e, a) { for(var i in a) e[i] = a[i]; }(window, webpackJsonp([64],{

/***/ "./openedx/features/course_experience/static/course_experience/js/CourseHome.js":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
Object.defineProperty(__webpack_exports__, "__esModule", { value: true });
/* WEBPACK VAR INJECTION */(function($) {/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "CourseHome", function() { return CourseHome; });
var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

/* globals gettext, Logger */

var CourseHome = function () {
  // eslint-disable-line import/prefer-default-export
  function CourseHome(options) {
    var _this = this;

    _classCallCheck(this, CourseHome);

    this.courseRunKey = options.courseRunKey;
    this.msgStateStorageKey = 'course_experience.upgrade_msg.' + this.courseRunKey + '.collapsed';

    // Logging for 'Resume Course' or 'Start Course' button click
    var $resumeCourseLink = $(options.resumeCourseLink);
    $resumeCourseLink.on('click', function (event) {
      var eventType = $resumeCourseLink.find('span').data('action-type');
      Logger.log('edx.course.home.resume_course.clicked', {
        event_type: eventType,
        url: event.currentTarget.href
      });
    });

    // Logging for course tool click events
    var $courseToolLink = $(options.courseToolLink);
    $courseToolLink.on('click', function (event) {
      var courseToolName = event.srcElement.dataset['analytics-id']; // eslint-disable-line dot-notation
      Logger.log('edx.course.tool.accessed', {
        tool_name: courseToolName
      });
    });

    // Course goal editing elements
    var $goalSection = $('.section-goals');
    var $editGoalIcon = $('.section-goals .edit-icon');
    var $currentGoalText = $('.section-goals .goal');
    var $goalSelect = $('.section-goals .edit-goal-select');
    var $responseIndicator = $('.section-goals .response-icon');
    var $responseMessageSr = $('.section-goals .sr-update-response-msg');
    var $goalUpdateTitle = $('.section-goals .title:not("label")');
    var $goalUpdateLabel = $('.section-goals label.title');

    // Switch to editing mode when the goal section is clicked
    $goalSection.on('click', function (event) {
      if (!$(event.target).hasClass('edit-goal-select')) {
        $goalSelect.toggle();
        $currentGoalText.toggle();
        $goalUpdateTitle.toggle();
        $goalUpdateLabel.toggle();
        $responseIndicator.removeClass().addClass('response-icon');
        $goalSelect.focus();
      }
    });

    // Trigger click event on enter press for accessibility purposes
    $(document.body).on('keyup', '.section-goals .edit-icon', function (event) {
      if (event.which === 13) {
        $(event.target).trigger('click');
      }
    });

    // Send an ajax request to update the course goal
    $goalSelect.on('blur change', function (event) {
      $currentGoalText.show();
      $goalUpdateTitle.show();
      $goalUpdateLabel.hide();
      $goalSelect.hide();
      // No need to update in the case of a blur event
      if (event.type === 'blur') return;
      var newGoalKey = $(event.target).val();
      $responseIndicator.removeClass().addClass('response-icon fa fa-spinner fa-spin');
      $.ajax({
        method: 'POST',
        url: options.goalApiUrl,
        headers: { 'X-CSRFToken': $.cookie('csrftoken') },
        data: {
          goal_key: newGoalKey,
          course_key: options.courseId,
          user: options.username
        },
        dataType: 'json',
        success: function success(data) {
          $currentGoalText.find('.text').text(data.goal_text);
          $responseMessageSr.text(gettext('You have successfully updated your goal.'));
          $responseIndicator.removeClass().addClass('response-icon fa fa-check');
        },
        error: function error() {
          $responseIndicator.removeClass().addClass('response-icon fa fa-close');
          $responseMessageSr.text(gettext('There was an error updating your goal.'));
        },
        complete: function complete() {
          // Only show response icon indicator for 3 seconds.
          setTimeout(function () {
            $responseIndicator.removeClass().addClass('response-icon');
          }, 3000);
          $editGoalIcon.focus();
        }
      });
    });

    // Dismissibility for in course messages
    $(document.body).on('click', '.course-message .dismiss', function (event) {
      $(event.target).closest('.course-message').hide();
    });

    // Allow dismiss on enter press for accessibility purposes
    $(document.body).on('keyup', '.course-message .dismiss', function (event) {
      if (event.which === 13) {
        $(event.target).trigger('click');
      }
    });

    $(document).ready(function () {
      _this.configureUpgradeMessage();
      _this.configureUpgradeAnalytics();
    });
  }

  _createClass(CourseHome, [{
    key: 'configureUpgradeAnalytics',


    // Promotion analytics for upgrade messages on course home.
    // eslint-disable-next-line class-methods-use-this
    value: function configureUpgradeAnalytics() {
      $('.btn-upgrade').each(function (index, button) {
        var promotionEventProperties = {
          promotion_id: 'courseware_verified_certificate_upsell',
          creative: $(button).data('creative'),
          name: 'In-Course Verification Prompt',
          position: $(button).data('position')
        };
        CourseHome.fireSegmentEvent('Promotion Viewed', promotionEventProperties);
        $(button).click(function () {
          CourseHome.fireSegmentEvent('Promotion Clicked', promotionEventProperties);
        });
      });
    }
  }, {
    key: 'configureUpgradeMessage',
    value: function configureUpgradeMessage() {
      var logEventProperties = { courseRunKey: this.courseRunKey };

      Logger.log('edx.bi.course.upgrade.sidebarupsell.displayed', logEventProperties);
      $('.section-upgrade .btn-upgrade').click(function () {
        Logger.log('edx.bi.course.upgrade.sidebarupsell.clicked', logEventProperties);
        Logger.log('edx.course.enrollment.upgrade.clicked', { location: 'sidebar-message' });
      });
      $('.promo-learn-more').click(function () {
        $('.action-toggle-verification-sock').click();
        $('.action-toggle-verification-sock')[0].scrollIntoView({ behavior: 'smooth', alignToTop: true });
      });
    }
  }], [{
    key: 'fireSegmentEvent',
    value: function fireSegmentEvent(event, properties) {
      /* istanbul ignore next */
      if (!window.analytics) {
        return;
      }

      window.analytics.track(event, properties);
    }
  }]);

  return CourseHome;
}();
/* WEBPACK VAR INJECTION */}.call(__webpack_exports__, __webpack_require__(0)))

/***/ })

},["./openedx/features/course_experience/static/course_experience/js/CourseHome.js"])));
//# sourceMappingURL=CourseHome.js.map
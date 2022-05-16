(function(e, a) { for(var i in a) e[i] = a[i]; }(window, webpackJsonp([62],{

/***/ "./openedx/features/course_experience/static/course_experience/js/Enrollment.js":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
Object.defineProperty(__webpack_exports__, "__esModule", { value: true });
/* WEBPACK VAR INJECTION */(function($) {/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "CourseEnrollment", function() { return CourseEnrollment; });
var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

/*
 * Course Enrollment on the Course Home page
 */
var CourseEnrollment = function () {
  _createClass(CourseEnrollment, null, [{
    key: 'redirect',
    // eslint-disable-line import/prefer-default-export
    /**
     * Redirect to a URL.  Mainly useful for mocking out in tests.
     * @param  {string} url The URL to redirect to.
     */
    value: function redirect(url) {
      window.location.href = url;
    }
  }, {
    key: 'refresh',
    value: function refresh() {
      window.location.reload(false);
    }
  }, {
    key: 'createEnrollment',
    value: function createEnrollment(courseId) {
      var data = JSON.stringify({
        course_details: { course_id: courseId }
      });
      var enrollmentAPI = '/api/enrollment/v1/enrollment';
      var trackSelection = '/course_modes/choose/';

      return function () {
        return $.ajax({
          type: 'POST',
          url: enrollmentAPI,
          data: data,
          contentType: 'application/json'
        }).done(function () {
          window.analytics.track('edx.bi.user.course-home.enrollment');
          CourseEnrollment.refresh();
        }).fail(function () {
          // If the simple enrollment we attempted failed, go to the track selection page,
          // which is better for handling more complex enrollment situations.
          CourseEnrollment.redirect(trackSelection + courseId);
        });
      };
    }
  }]);

  function CourseEnrollment(buttonClass, courseId) {
    _classCallCheck(this, CourseEnrollment);

    $(buttonClass).click(CourseEnrollment.createEnrollment(courseId));
  }

  return CourseEnrollment;
}();
/* WEBPACK VAR INJECTION */}.call(__webpack_exports__, __webpack_require__(0)))

/***/ })

},["./openedx/features/course_experience/static/course_experience/js/Enrollment.js"])));
//# sourceMappingURL=Enrollment.js.map
(function(e, a) { for(var i in a) e[i] = a[i]; }(window, webpackJsonp([61],{

/***/ "./cms/static/js/factories/context_course.js":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
Object.defineProperty(__webpack_exports__, "__esModule", { value: true });
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0_js_models_course__ = __webpack_require__("./cms/static/js/models/course.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0_js_models_course___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_0_js_models_course__);
/* harmony reexport (module object) */ __webpack_require__.d(__webpack_exports__, "ContextCourse", function() { return __WEBPACK_IMPORTED_MODULE_0_js_models_course__; });




/***/ }),

/***/ "./cms/static/js/models/course.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(2)], __WEBPACK_AMD_DEFINE_RESULT__ = function (Backbone) {
    var Course = Backbone.Model.extend({
        defaults: {
            name: ''
        },
        validate: function validate(attrs, options) {
            if (!attrs.name) {
                return gettext('You must specify a name');
            }
        }
    });
    return Course;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ })

},["./cms/static/js/factories/context_course.js"])));
//# sourceMappingURL=context_course.js.map
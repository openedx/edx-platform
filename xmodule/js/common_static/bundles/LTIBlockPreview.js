(function(e, a) { for(var i in a) e[i] = a[i]; }(window, webpackJsonp([45],{

/***/ "./common/static/xmodule/modules/js/001-550e26b7e4efbc0c68a580f6dbecf66c.js":
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function($) {/*** IMPORTS FROM imports-loader ***/
(function () {

    (function () {
        'use strict';
        /**
         * This function will process all the attributes from the DOM element passed, taking all of
         * the configuration attributes. It uses the request-username and request-email
         * to prompt the user to decide if they want to share their personal information
         * with the third party application connecting through LTI.
         * @constructor
         * @param {jQuery} element DOM element with the lti container.
         */

        this.LTI = function (element) {
            var dataAttrs = $(element).find('.lti').data(),
                askToSendUsername = dataAttrs.askToSendUsername === 'True',
                askToSendEmail = dataAttrs.askToSendEmail === 'True';

            // When the lti button is clicked, provide users the option to
            // accept or reject sending their information to a third party
            $(element).on('click', '.link_lti_new_window', function () {
                if (askToSendUsername && askToSendEmail) {
                    return confirm(gettext('Click OK to have your username and e-mail address sent to a 3rd party application.\n\nClick Cancel to return to this page without sending your information.'));
                } else if (askToSendUsername) {
                    return confirm(gettext('Click OK to have your username sent to a 3rd party application.\n\nClick Cancel to return to this page without sending your information.'));
                } else if (askToSendEmail) {
                    return confirm(gettext('Click OK to have your e-mail address sent to a 3rd party application.\n\nClick Cancel to return to this page without sending your information.'));
                } else {
                    return true;
                }
            });
        };
    }).call(this);
}).call(window);
/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(0)))

/***/ }),

/***/ 17:
/***/ (function(module, exports, __webpack_require__) {

__webpack_require__("./common/static/xmodule/modules/js/000-b82f6c436159f6bc7ca2513e29e82503.js");
module.exports = __webpack_require__("./common/static/xmodule/modules/js/001-550e26b7e4efbc0c68a580f6dbecf66c.js");


/***/ })

},[17])));
//# sourceMappingURL=LTIBlockPreview.js.map
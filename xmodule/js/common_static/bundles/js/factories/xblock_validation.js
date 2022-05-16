(function(e, a) { for(var i in a) e[i] = a[i]; }(window, webpackJsonp([21],{

/***/ "./cms/static/js/factories/xblock_validation.js":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
Object.defineProperty(__webpack_exports__, "__esModule", { value: true });
/* harmony export (immutable) */ __webpack_exports__["default"] = XBlockValidationFactory;
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "XBlockValidationFactory", function() { return XBlockValidationFactory; });
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0_js_views_xblock_validation__ = __webpack_require__("./cms/static/js/views/xblock_validation.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0_js_views_xblock_validation___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_0_js_views_xblock_validation__);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1_js_models_xblock_validation__ = __webpack_require__("./cms/static/js/models/xblock_validation.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1_js_models_xblock_validation___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_1_js_models_xblock_validation__);




'use strict';
function XBlockValidationFactory(validationMessages, hasEditingUrl, isRoot, isUnit, validationEle) {
    var model, response;

    if (hasEditingUrl && !isRoot) {
        validationMessages.showSummaryOnly = true;
    }
    response = validationMessages;
    response.isUnit = isUnit;

    model = new __WEBPACK_IMPORTED_MODULE_1_js_models_xblock_validation__(response, { parse: true });

    if (!model.get('empty')) {
        new __WEBPACK_IMPORTED_MODULE_0_js_views_xblock_validation__({ el: validationEle, model: model, root: isRoot }).render();
    }
};



/***/ }),

/***/ "./cms/static/js/models/xblock_validation.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(2), __webpack_require__(3), __webpack_require__(1)], __WEBPACK_AMD_DEFINE_RESULT__ = function (Backbone, gettext, _) {
    /**
     * Model for xblock validation messages as displayed in Studio.
     */
    var XBlockValidationModel = Backbone.Model.extend({
        defaults: {
            summary: {},
            messages: [],
            empty: true,
            xblock_id: null
        },

        WARNING: 'warning',
        ERROR: 'error',
        NOT_CONFIGURED: 'not-configured',

        parse: function parse(response) {
            if (!response.empty) {
                var summary = 'summary' in response ? response.summary : {};
                var messages = 'messages' in response ? response.messages : [];
                if (!summary.text) {
                    if (response.isUnit) {
                        summary.text = gettext('This unit has validation issues.');
                    } else {
                        summary.text = gettext('This component has validation issues.');
                    }
                }
                if (!summary.type) {
                    summary.type = this.WARNING;
                    // Possible types are ERROR, WARNING, and NOT_CONFIGURED. NOT_CONFIGURED is treated as a warning.
                    _.find(messages, function (message) {
                        if (message.type === this.ERROR) {
                            summary.type = this.ERROR;
                            return true;
                        }
                        return false;
                    }, this);
                }
                response.summary = summary;
                if (response.showSummaryOnly) {
                    messages = [];
                }
                response.messages = messages;
            }

            return response;
        }
    });
    return XBlockValidationModel;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ }),

/***/ "./cms/static/js/utils/handle_iframe_binding.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(0)], __WEBPACK_AMD_DEFINE_RESULT__ = function ($) {
    var iframeBinding = function iframeBinding(e) {
        var target_element = null;
        if (typeof e === 'undefined') {
            target_element = $('iframe, embed');
        } else {
            if (typeof e.nodeName !== 'undefined') {
                target_element = $(e).find('iframe, embed');
            } else {
                target_element = e.$('iframe, embed');
            }
        }
        modifyTagContent(target_element);
    };

    var modifyTagContent = function modifyTagContent(target_element) {
        target_element.each(function () {
            if ($(this).prop('tagName') === 'IFRAME') {
                var ifr_source = $(this).attr('src');

                // Modify iframe src only if it is not empty
                if (ifr_source) {
                    var wmode = 'wmode=transparent';
                    if (ifr_source.indexOf('?') !== -1) {
                        var getQString = ifr_source.split('?');
                        if (getQString[1].search('wmode=transparent') === -1) {
                            var oldString = getQString[1];
                            var newString = getQString[0];
                            $(this).attr('src', newString + '?' + wmode + '&' + oldString);
                        }
                    }
                    // The TinyMCE editor is hosted in an iframe, and before the iframe is
                    // removed we execute this code. To avoid throwing an error when setting the
                    // attr, check that the source doesn't start with the value specified by TinyMCE ('javascript:""').
                    else if (ifr_source.lastIndexOf('javascript:', 0) !== 0) {
                            $(this).attr('src', ifr_source + '?' + wmode);
                        }
                }
            } else {
                $(this).attr('wmode', 'transparent');
            }
        });
    };

    // Modify iframe/embed tags in provided html string
    // Use this method when provided data is just html sting not dom element
    // This method will only modify iframe (add wmode=transparent in url querystring) and embed (add wmode=transparent as attribute)
    // tags in html string so both tags will attach to dom and don't create z-index problem for other popups
    // Note: embed tags should be modified before rendering as they are static objects as compared to iframes
    // Note: this method can modify unintended html (invalid tags) while converting to dom object
    var iframeBindingHtml = function iframeBindingHtml(html_string) {
        if (html_string) {
            var target_element = null;
            var temp_content = document.createElement('div');
            $(temp_content).html(html_string);
            target_element = $(temp_content).find('iframe, embed');
            if (target_element.length > 0) {
                modifyTagContent(target_element);
                html_string = $(temp_content).html();
            }
        }
        return html_string;
    };

    return {
        iframeBinding: iframeBinding,
        iframeBindingHtml: iframeBindingHtml
    };
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ }),

/***/ "./cms/static/js/utils/templates.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(0), __webpack_require__(1)], __WEBPACK_AMD_DEFINE_RESULT__ = function ($, _) {
    /**
     * Loads the named template from the page, or logs an error if it fails.
     * @param name The name of the template.
     * @returns The loaded template.
     */
    var loadTemplate = function loadTemplate(name) {
        var templateSelector = '#' + name + '-tpl',
            templateText = $(templateSelector).text();
        if (!templateText) {
            console.error('Failed to load ' + name + ' template');
        }
        return _.template(templateText);
    };

    return {
        loadTemplate: loadTemplate
    };
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ }),

/***/ "./cms/static/js/views/baseview.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(0), __webpack_require__(1), __webpack_require__(2), __webpack_require__(3), __webpack_require__("./cms/static/js/utils/handle_iframe_binding.js"), __webpack_require__("./cms/static/js/utils/templates.js"), __webpack_require__("./common/static/common/js/components/utils/view_utils.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function ($, _, Backbone, gettext, IframeUtils, TemplateUtils, ViewUtils) {
    /*
     This view is extended from backbone to provide useful functionality for all Studio views.
     This functionality includes:
     - automatic expand and collapse of elements with the 'ui-toggle-expansion' class specified
     - additional control of rendering by overriding 'beforeRender' or 'afterRender'
      Note: the default 'afterRender' function calls a utility function 'iframeBinding' which modifies
     iframe src urls on a page so that they are rendered as part of the DOM.
     */

    var BaseView = Backbone.View.extend({
        events: {
            'click .ui-toggle-expansion': 'toggleExpandCollapse'
        },

        options: {
            // UX is moving towards using 'is-collapsed' in preference over 'collapsed',
            // but use the old scheme as the default so that existing code doesn't need
            // to be rewritten.
            collapsedClass: 'collapsed'
        },

        // override the constructor function
        constructor: function constructor(options) {
            _.bindAll(this, 'beforeRender', 'render', 'afterRender');

            // Merge passed options and view's options property and
            // attach to the view's options property
            if (this.options) {
                options = _.extend({}, _.result(this, 'options'), options);
            }

            // trunc is not available in IE, and it provides polyfill for it.
            // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Math/trunc
            if (!Math.trunc) {
                Math.trunc = function (v) {
                    v = +v; // eslint-disable-line no-param-reassign
                    return v - v % 1 || (!isFinite(v) || v === 0 ? v : v < 0 ? -0 : 0);
                };
            }
            this.options = options;

            var _this = this;
            // xss-lint: disable=javascript-jquery-insertion
            this.render = _.wrap(this.render, function (render, options) {
                _this.beforeRender();
                render(options);
                _this.afterRender();
                return _this;
            });

            // call Backbone's own constructor
            Backbone.View.prototype.constructor.apply(this, arguments);
        },

        beforeRender: function beforeRender() {},

        render: function render() {
            return this;
        },

        afterRender: function afterRender() {
            IframeUtils.iframeBinding(this);
        },

        toggleExpandCollapse: function toggleExpandCollapse(event) {
            var $target = $(event.target);
            // Don't propagate the event as it is possible that two views will both contain
            // this element, e.g. clicking on the element of a child view container in a parent.
            event.stopPropagation();
            event.preventDefault();
            ViewUtils.toggleExpandCollapse($target, this.options.collapsedClass);
        },

        /**
         * Loads the named template from the page, or logs an error if it fails.
         * @param name The name of the template.
         * @returns The loaded template.
         */
        loadTemplate: function loadTemplate(name) {
            return TemplateUtils.loadTemplate(name);
        }
    });

    return BaseView;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ }),

/***/ "./cms/static/js/views/xblock_validation.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(0), __webpack_require__(1), __webpack_require__("./cms/static/js/views/baseview.js"), __webpack_require__(3), __webpack_require__("./node_modules/edx-ui-toolkit/src/js/utils/html-utils.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function ($, _, BaseView, gettext, HtmlUtils) {
    'use strict';
    /**
     * View for xblock validation messages as displayed in Studio.
     */

    var XBlockValidationView = BaseView.extend({

        // Takes XBlockValidationModel as a model
        initialize: function initialize(options) {
            BaseView.prototype.initialize.call(this);
            this.template = this.loadTemplate('xblock-validation-messages');
            this.root = options.root;
        },

        render: function render() {
            var attributes = {
                validation: this.model,
                additionalClasses: this.getAdditionalClasses(),
                getIcon: this.getIcon.bind(this),
                getDisplayName: this.getDisplayName.bind(this)
            };
            this.$el.html(HtmlUtils.HTML(this.template(attributes)).toString());
            return this;
        },

        /**
         * Returns the icon css class based on the message type.
         * @param messageType
         * @returns string representation of css class that will render the correct icon, or null if unknown type
         */
        getIcon: function getIcon(messageType) {
            if (messageType === this.model.ERROR) {
                return 'fa-exclamation-circle';
            } else if (messageType === this.model.WARNING || messageType === this.model.NOT_CONFIGURED) {
                return 'fa-exclamation-triangle';
            }
            return null;
        },

        /**
         * Returns a display name for a message (useful for screen readers), based on the message type.
         * @param messageType
         * @returns string display name (translated)
         */
        getDisplayName: function getDisplayName(messageType) {
            if (messageType === this.model.WARNING || messageType === this.model.NOT_CONFIGURED) {
                // Translators: This message will be added to the front of messages of type warning,
                // e.g. "Warning: this component has not been configured yet".
                return gettext('Warning');
            } else if (messageType === this.model.ERROR) {
                // Translators: This message will be added to the front of messages of type error,
                // e.g. "Error: required field is missing".
                return gettext('Error');
            }
            return null;
        },

        /**
         * Returns additional css classes that can be added to HTML containing the validation messages.
         * Useful for rendering NOT_CONFIGURED in a special way.
         *
         * @returns string of additional css classes (or empty string)
         */
        getAdditionalClasses: function getAdditionalClasses() {
            if (this.root && this.model.get('summary').type === this.model.NOT_CONFIGURED && this.model.get('messages').length === 0) {
                return 'no-container-content';
            }
            return '';
        }
    });

    return XBlockValidationView;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ }),

/***/ "./common/static/common/js/components/utils/view_utils.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";
var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;/**
 * Provides useful utilities for views.
 */



/* RequireJS
define(['jquery', 'underscore', 'gettext', 'common/js/components/views/feedback_notification',
    'common/js/components/views/feedback_prompt', 'edx-ui-toolkit/js/utils/html-utils'],
    function($, _, gettext, NotificationView, PromptView, HtmlUtils) {
/* End RequireJS */
/* Webpack */

!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(0), __webpack_require__(1), __webpack_require__(3), __webpack_require__("./common/static/common/js/components/views/feedback_notification.js"), __webpack_require__("./common/static/common/js/components/views/feedback_prompt.js"), __webpack_require__("./node_modules/scriptjs/dist/script.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function ($, _, gettext, NotificationView, PromptView, $script) {
    /* End Webpack */

    var toggleExpandCollapse, showLoadingIndicator, hideLoadingIndicator, confirmThenRunOperation, runOperationShowingMessage, showErrorMeassage, withDisabledElement, disableElementWhileRunning, getScrollOffset, setScrollOffset, setScrollTop, redirect, reload, hasChangedAttributes, deleteNotificationHandler, validateRequiredField, validateURLItemEncoding, validateTotalKeyLength, checkTotalKeyLengthViolations, loadJavaScript;

    // see https://openedx.atlassian.net/browse/TNL-889 for what is it and why it's 65
    var MAX_SUM_KEY_LENGTH = 65;

    /**
     * Toggles the expanded state of the current element.
     */
    toggleExpandCollapse = function toggleExpandCollapse(target, collapsedClass) {
        // Support the old 'collapsed' option until fully switched over to is-collapsed
        var collapsed = collapsedClass || 'collapsed';
        target.closest('.expand-collapse').toggleClass('expand collapse');
        target.closest('.is-collapsible, .window').toggleClass(collapsed);
        target.closest('.is-collapsible').children('article').slideToggle();
    };

    /**
     * Show the page's loading indicator.
     */
    showLoadingIndicator = function showLoadingIndicator() {
        $('.ui-loading').show();
    };

    /**
     * Hide the page's loading indicator.
     */
    hideLoadingIndicator = function hideLoadingIndicator() {
        $('.ui-loading').hide();
    };

    /**
     * Confirms with the user whether to run an operation or not, and then runs it if desired.
     */
    confirmThenRunOperation = function confirmThenRunOperation(title, message, actionLabel, operation, onCancelCallback) {
        return new PromptView.Warning({
            title: title,
            message: message,
            actions: {
                primary: {
                    text: actionLabel,
                    click: function click(prompt) {
                        prompt.hide();
                        operation();
                    }
                },
                secondary: {
                    text: gettext('Cancel'),
                    click: function click(prompt) {
                        if (onCancelCallback) {
                            onCancelCallback();
                        }
                        return prompt.hide();
                    }
                }
            }
        }).show();
    };

    /**
     * Shows a progress message for the duration of an asynchronous operation.
     * Note: this does not remove the notification upon failure because an error
     * will be shown that shouldn't be removed.
     * @param message The message to show.
     * @param operation A function that returns a promise representing the operation.
     */
    runOperationShowingMessage = function runOperationShowingMessage(message, operation) {
        var notificationView;
        notificationView = new NotificationView.Mini({
            title: gettext(message)
        });
        notificationView.show();
        return operation().done(function () {
            notificationView.hide();
        });
    };

    /**
     * Shows an error notification message for a specifc period of time.
     * @param heading The heading of notification.
     * @param message The message to show.
     * @param timeInterval The time interval to hide the notification.
     */
    showErrorMeassage = function showErrorMeassage(heading, message, timeInterval) {
        var errorNotificationView = new NotificationView.Error({
            title: gettext(heading),
            message: gettext(message)
        });
        errorNotificationView.show();

        setTimeout(function () {
            errorNotificationView.hide();
        }, timeInterval);
    };
    /**
     * Wraps a Backbone event callback to disable the event's target element.
     *
     * This paradigm is designed to be used in Backbone event maps where
     * multiple events firing simultaneously is not desired.
     *
     * @param functionName the function to execute, as a string.
     * The function must return a jQuery promise and be able to take an event
     */
    withDisabledElement = function withDisabledElement(functionName) {
        return function (event) {
            var view = this;
            disableElementWhileRunning($(event.currentTarget), function () {
                // call view.functionName(event), with view as the current this
                return view[functionName].apply(view, [event]);
            });
        };
    };

    /**
     * Disables a given element when a given operation is running.
     * @param {jQuery} element the element to be disabled.
     * @param operation the operation during whose duration the
     * element should be disabled. The operation should return
     * a JQuery promise.
     */
    disableElementWhileRunning = function disableElementWhileRunning(element, operation) {
        element.addClass('is-disabled').attr('aria-disabled', true);
        return operation().always(function () {
            element.removeClass('is-disabled').attr('aria-disabled', false);
        });
    };

    /**
     * Returns a handler that removes a notification, both dismissing it and deleting it from the database.
     * @param callback function to call when deletion succeeds
     */
    deleteNotificationHandler = function deleteNotificationHandler(callback) {
        return function (event) {
            event.preventDefault();
            $.ajax({
                url: $(this).data('dismiss-link'),
                type: 'DELETE',
                success: callback
            });
        };
    };

    /**
     * Performs an animated scroll so that the window has the specified scroll top.
     * @param scrollTop The desired scroll top for the window.
     */
    setScrollTop = function setScrollTop(scrollTop) {
        $('html, body').animate({
            scrollTop: scrollTop
        }, 500);
    };

    /**
     * Returns the relative position that the element is scrolled from the top of the view port.
     * @param element The element in question.
     */
    getScrollOffset = function getScrollOffset(element) {
        var elementTop = element.offset().top;
        return elementTop - $(window).scrollTop();
    };

    /**
     * Scrolls the window so that the element is scrolled down to the specified relative position
     * from the top of the view port.
     * @param element The element in question.
     * @param offset The amount by which the element should be scrolled from the top of the view port.
     */
    setScrollOffset = function setScrollOffset(element, offset) {
        var elementTop = element.offset().top,
            newScrollTop = elementTop - offset;
        setScrollTop(newScrollTop);
    };

    /**
     * Redirects to the specified URL. This is broken out as its own function for unit testing.
     */
    redirect = function redirect(url) {
        window.location = url;
    };

    /**
     * Reloads the page. This is broken out as its own function for unit testing.
     */
    reload = function reload() {
        window.location.reload();
    };

    /**
     * Returns true if a model has changes to at least one of the specified attributes.
     * @param model The model in question.
     * @param attributes The list of attributes to be compared.
     * @returns {boolean} Returns true if attribute changes are found.
     */
    hasChangedAttributes = function hasChangedAttributes(model, attributes) {
        var i,
            changedAttributes = model.changedAttributes();
        if (!changedAttributes) {
            return false;
        }
        for (i = 0; i < attributes.length; i++) {
            if (_.has(changedAttributes, attributes[i])) {
                return true;
            }
        }
        return false;
    };

    /**
     * Helper method for course/library creation - verifies a required field is not blank.
     */
    validateRequiredField = function validateRequiredField(msg) {
        return msg.length === 0 ? gettext('Required field.') : '';
    };

    /**
     * Helper method for course/library creation.
     * Check that a course (org, number, run) doesn't use any special characters
     */
    validateURLItemEncoding = function validateURLItemEncoding(item, allowUnicode) {
        var required = validateRequiredField(item);
        if (required) {
            return required;
        }
        if (allowUnicode) {
            if (/\s/g.test(item)) {
                return gettext('Please do not use any spaces in this field.');
            }
        } else {
            if (item !== encodeURIComponent(item) || item.match(/[!'()*]/)) {
                return gettext('Please do not use any spaces or special characters in this field.');
            }
        }
        return '';
    };

    // Ensure that sum length of key field values <= ${MAX_SUM_KEY_LENGTH} chars.
    validateTotalKeyLength = function validateTotalKeyLength(keyFieldSelectors) {
        var totalLength = _.reduce(keyFieldSelectors, function (sum, ele) {
            return sum + $(ele).val().length;
        }, 0);
        return totalLength <= MAX_SUM_KEY_LENGTH;
    };

    checkTotalKeyLengthViolations = function checkTotalKeyLengthViolations(selectors, classes, keyFieldSelectors, messageTpl) {
        var tempHtml;
        if (!validateTotalKeyLength(keyFieldSelectors)) {
            $(selectors.errorWrapper).addClass(classes.shown).removeClass(classes.hiding);
            tempHtml = HtmlUtils.joinHtml(HtmlUtils.HTML('<p>'), HtmlUtils.template(messageTpl)({ limit: MAX_SUM_KEY_LENGTH }), HtmlUtils.HTML('</p>'));
            HtmlUtils.setHtml($(selectors.errorMessage), tempHtml);
            $(selectors.save).addClass(classes.disabled);
        } else {
            $(selectors.errorWrapper).removeClass(classes.shown).addClass(classes.hiding);
        }
    };

    /**
     * Dynamically loads the specified JavaScript file.
     * @param url The URL to a JavaScript file.
     * @returns {Promise} A promise indicating when the URL has been loaded.
     */
    loadJavaScript = function loadJavaScript(url) {
        var deferred = $.Deferred();
        /* RequireJS
        require([url],
            function() {
                deferred.resolve();
            },
            function() {
                deferred.reject();
            });
        /* End RequireJS */
        /* Webpack */
        $script(url, url, function () {
            deferred.resolve();
        });
        /* End Webpack */
        return deferred.promise();
    };

    return {
        toggleExpandCollapse: toggleExpandCollapse,
        showLoadingIndicator: showLoadingIndicator,
        hideLoadingIndicator: hideLoadingIndicator,
        confirmThenRunOperation: confirmThenRunOperation,
        runOperationShowingMessage: runOperationShowingMessage,
        showErrorMeassage: showErrorMeassage,
        withDisabledElement: withDisabledElement,
        disableElementWhileRunning: disableElementWhileRunning,
        deleteNotificationHandler: deleteNotificationHandler,
        setScrollTop: setScrollTop,
        getScrollOffset: getScrollOffset,
        setScrollOffset: setScrollOffset,
        redirect: redirect,
        reload: reload,
        hasChangedAttributes: hasChangedAttributes,
        validateRequiredField: validateRequiredField,
        validateURLItemEncoding: validateURLItemEncoding,
        validateTotalKeyLength: validateTotalKeyLength,
        checkTotalKeyLengthViolations: checkTotalKeyLengthViolations,
        loadJavaScript: loadJavaScript
    };
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ }),

/***/ "./common/static/common/js/components/views/feedback.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";
var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;


!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(0), __webpack_require__(1), __webpack_require__("./common/static/common/js/vendor/underscore.string.js"), __webpack_require__(2), __webpack_require__("./node_modules/edx-ui-toolkit/src/js/utils/html-utils.js"), __webpack_require__("./common/static/common/templates/components/system-feedback.underscore")], __WEBPACK_AMD_DEFINE_RESULT__ = function ($, _, str, Backbone, HtmlUtils, systemFeedbackTemplate) {
    var tabbableElements = ["a[href]:not([tabindex='-1'])", "area[href]:not([tabindex='-1'])", "input:not([disabled]):not([tabindex='-1'])", "select:not([disabled]):not([tabindex='-1'])", "textarea:not([disabled]):not([tabindex='-1'])", "button:not([disabled]):not([tabindex='-1'])", "iframe:not([tabindex='-1'])", "[tabindex]:not([tabindex='-1'])", "[contentEditable=true]:not([tabindex='-1'])"];
    var SystemFeedback = Backbone.View.extend({
        options: {
            title: '',
            message: '',
            intent: null, // "warning", "confirmation", "error", "announcement", "step-required", etc
            type: null, // "alert", "notification", or "prompt": set by subclass
            shown: true, // is this view currently being shown?
            icon: true, // should we render an icon related to the message intent?
            closeIcon: true, // should we render a close button in the top right corner?
            minShown: 0, // ms after this view has been shown before it can be hidden
            maxShown: Infinity, // ms after this view has been shown before it will be automatically hidden
            outFocusElement: null // element to send focus to on hide

            /* Could also have an "actions" hash: here is an example demonstrating
                the expected structure. For each action, by default the framework
                will call preventDefault on the click event before the function is
                run; to make it not do that, just pass `preventDefault: false` in
                the action object.
             actions: {
                primary: {
                    "text": "Save",
                    "class": "action-save",
                    "click": function(view) {
                        // do something when Save is clicked
                    }
                },
                secondary: [
                    {
                        "text": "Cancel",
                        "class": "action-cancel",
                        "click": function(view) {}
                    }, {
                        "text": "Discard Changes",
                        "class": "action-discard",
                        "click": function(view) {}
                    }
                ]
            }
            */
        },

        initialize: function initialize(options) {
            this.options = _.extend({}, this.options, options);
            if (!this.options.type) {
                throw 'SystemFeedback: type required (given ' + // eslint-disable-line no-throw-literal
                JSON.stringify(this.options) + ')';
            }
            if (!this.options.intent) {
                throw 'SystemFeedback: intent required (given ' + // eslint-disable-line no-throw-literal
                JSON.stringify(this.options) + ')';
            }
            this.setElement($('#page-' + this.options.type));
            // handle single "secondary" action
            if (this.options.actions && this.options.actions.secondary && !_.isArray(this.options.actions.secondary)) {
                this.options.actions.secondary = [this.options.actions.secondary];
            }
            return this;
        },

        inFocus: function inFocus(wrapperElementSelector) {
            var wrapper = wrapperElementSelector || '.wrapper',
                tabbables;
            this.options.outFocusElement = this.options.outFocusElement || document.activeElement;

            // Set focus to the container.
            this.$(wrapper).first().focus();

            // Make tabs within the prompt loop rather than setting focus
            // back to the main content of the page.
            tabbables = this.$(tabbableElements.join());
            tabbables.on('keydown', function (event) {
                // On tab backward from the first tabbable item in the prompt
                if (event.which === 9 && event.shiftKey && event.target === tabbables.first()[0]) {
                    event.preventDefault();
                    tabbables.last().focus();
                } else if (event.which === 9 && !event.shiftKey && event.target === tabbables.last()[0]) {
                    // On tab forward from the last tabbable item in the prompt
                    event.preventDefault();
                    tabbables.first().focus();
                }
            });

            return this;
        },

        outFocus: function outFocus() {
            this.$(tabbableElements.join()).off('keydown');
            if (this.options.outFocusElement) {
                this.options.outFocusElement.focus();
            }
            return this;
        },

        // public API: show() and hide()
        show: function show() {
            clearTimeout(this.hideTimeout);
            this.options.shown = true;
            this.shownAt = new Date();
            this.render();
            if ($.isNumeric(this.options.maxShown)) {
                this.hideTimeout = setTimeout(_.bind(this.hide, this), this.options.maxShown);
            }
            return this;
        },

        hide: function hide() {
            if (this.shownAt && $.isNumeric(this.options.minShown) && this.options.minShown > new Date() - this.shownAt) {
                clearTimeout(this.hideTimeout);
                this.hideTimeout = setTimeout(_.bind(this.hide, this), this.options.minShown - (new Date() - this.shownAt));
            } else {
                this.options.shown = false;
                delete this.shownAt;
                this.render();
            }
            return this;
        },

        // the rest of the API should be considered semi-private
        events: {
            'click .action-close': 'hide',
            'click .action-primary': 'primaryClick',
            'click .action-secondary': 'secondaryClick'
        },

        render: function render() {
            // there can be only one active view of a given type at a time: only
            // one alert, only one notification, only one prompt. Therefore, we'll
            // use a singleton approach.
            var singleton = SystemFeedback['active_' + this.options.type];
            if (singleton && singleton !== this) {
                singleton.stopListening();
                singleton.undelegateEvents();
            }
            HtmlUtils.setHtml(this.$el, HtmlUtils.template(systemFeedbackTemplate)(this.options));
            SystemFeedback['active_' + this.options.type] = this;
            return this;
        },

        primaryClick: function primaryClick(event) {
            var actions, primary;
            actions = this.options.actions;
            if (!actions) {
                return;
            }
            primary = actions.primary;
            if (!primary) {
                return;
            }
            if (primary.preventDefault !== false) {
                event.preventDefault();
            }
            if (primary.click) {
                primary.click.call(event.target, this, event);
            }
        },

        secondaryClick: function secondaryClick(event) {
            var actions, secondaryList, secondary, i;
            actions = this.options.actions;
            if (!actions) {
                return;
            }
            secondaryList = actions.secondary;
            if (!secondaryList) {
                return;
            }
            // which secondary action was clicked?
            i = 0; // default to the first secondary action (easier for testing)
            if (event && event.target) {
                i = _.indexOf(this.$('.action-secondary'), event.target);
            }
            secondary = secondaryList[i];
            if (secondary.preventDefault !== false) {
                event.preventDefault();
            }
            if (secondary.click) {
                secondary.click.call(event.target, this, event);
            }
        }
    });
    return SystemFeedback;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ }),

/***/ "./common/static/common/js/components/views/feedback_notification.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";
var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;


!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(0), __webpack_require__(1), __webpack_require__("./common/static/common/js/vendor/underscore.string.js"), __webpack_require__("./common/static/common/js/components/views/feedback.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function ($, _, str, SystemFeedbackView) {
    var Notification = SystemFeedbackView.extend({
        options: $.extend({}, SystemFeedbackView.prototype.options, {
            type: 'notification',
            closeIcon: false
        })
    });

    // create Notification.Warning, Notification.Confirmation, etc
    var capitalCamel, intents, miniOptions;
    capitalCamel = _.compose(str.capitalize, str.camelize);
    intents = ['warning', 'error', 'confirmation', 'announcement', 'step-required', 'help', 'mini'];
    _.each(intents, function (intent) {
        var subclass;
        subclass = Notification.extend({
            options: $.extend({}, Notification.prototype.options, {
                intent: intent
            })
        });
        Notification[capitalCamel(intent)] = subclass;
    });

    // set more sensible defaults for Notification.Mini views
    miniOptions = Notification.Mini.prototype.options;
    miniOptions.minShown = 1250;
    miniOptions.closeIcon = false;

    return Notification;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ }),

/***/ "./common/static/common/js/components/views/feedback_prompt.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";
var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;


!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(0), __webpack_require__(1), __webpack_require__("./common/static/common/js/vendor/underscore.string.js"), __webpack_require__("./common/static/common/js/components/views/feedback.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function ($, _, str, SystemFeedbackView) {
    var Prompt = SystemFeedbackView.extend({
        options: $.extend({}, SystemFeedbackView.prototype.options, {
            type: 'prompt',
            closeIcon: false,
            icon: false
        }),
        render: function render() {
            if (!window.$body) {
                window.$body = $(document.body);
            }
            if (this.options.shown) {
                $body.addClass('prompt-is-shown');
            } else {
                $body.removeClass('prompt-is-shown');
            }
            // super() in Javascript has awkward syntax :(
            return SystemFeedbackView.prototype.render.apply(this, arguments);
        },
        show: function show() {
            SystemFeedbackView.prototype.show.apply(this, arguments);
            return this.inFocus();
        },

        hide: function hide() {
            SystemFeedbackView.prototype.hide.apply(this, arguments);
            return this.outFocus();
        }
    });

    // create Prompt.Warning, Prompt.Confirmation, etc
    var capitalCamel, intents;
    capitalCamel = _.compose(str.capitalize, str.camelize);
    intents = ['warning', 'error', 'confirmation', 'announcement', 'step-required', 'help', 'mini'];
    _.each(intents, function (intent) {
        var subclass;
        subclass = Prompt.extend({
            options: $.extend({}, Prompt.prototype.options, {
                intent: intent
            })
        });
        Prompt[capitalCamel(intent)] = subclass;
    });

    return Prompt;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ }),

/***/ "./common/static/common/js/vendor/underscore.string.js":
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(global) {var __WEBPACK_AMD_DEFINE_FACTORY__, __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;var require;var require;var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; };

/*
* Underscore.string
* (c) 2010 Esa-Matti Suuronen <esa-matti aet suuronen dot org>
* Underscore.string is freely distributable under the terms of the MIT license.
* Documentation: https://github.com/epeli/underscore.string
* Some code is borrowed from MooTools and Alexandru Marasteanu.
* Version '3.3.4'
* @preserve
*/

(function (f) {
  if (( false ? "undefined" : _typeof(exports)) === "object" && typeof module !== "undefined") {
    module.exports = f();
  } else if (true) {
    !(__WEBPACK_AMD_DEFINE_ARRAY__ = [], __WEBPACK_AMD_DEFINE_FACTORY__ = (f),
				__WEBPACK_AMD_DEFINE_RESULT__ = (typeof __WEBPACK_AMD_DEFINE_FACTORY__ === 'function' ?
				(__WEBPACK_AMD_DEFINE_FACTORY__.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__)) : __WEBPACK_AMD_DEFINE_FACTORY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));
  } else {
    var g;if (typeof window !== "undefined") {
      g = window;
    } else if (typeof global !== "undefined") {
      g = global;
    } else if (typeof self !== "undefined") {
      g = self;
    } else {
      g = this;
    }g.s = f();
  }
})(function () {
  var define, module, exports;return function e(t, n, r) {
    function s(o, u) {
      if (!n[o]) {
        if (!t[o]) {
          var a = typeof require == "function" && require;if (!u && a) return require(o, !0);if (i) return i(o, !0);var f = new Error("Cannot find module '" + o + "'");throw f.code = "MODULE_NOT_FOUND", f;
        }var l = n[o] = { exports: {} };t[o][0].call(l.exports, function (e) {
          var n = t[o][1][e];return s(n ? n : e);
        }, l, l.exports, e, t, n, r);
      }return n[o].exports;
    }var i = typeof require == "function" && require;for (var o = 0; o < r.length; o++) {
      s(r[o]);
    }return s;
  }({ 1: [function (require, module, exports) {
      var trim = require('./trim');
      var decap = require('./decapitalize');

      module.exports = function camelize(str, decapitalize) {
        str = trim(str).replace(/[-_\s]+(.)?/g, function (match, c) {
          return c ? c.toUpperCase() : '';
        });

        if (decapitalize === true) {
          return decap(str);
        } else {
          return str;
        }
      };
    }, { "./decapitalize": 10, "./trim": 65 }], 2: [function (require, module, exports) {
      var makeString = require('./helper/makeString');

      module.exports = function capitalize(str, lowercaseRest) {
        str = makeString(str);
        var remainingChars = !lowercaseRest ? str.slice(1) : str.slice(1).toLowerCase();

        return str.charAt(0).toUpperCase() + remainingChars;
      };
    }, { "./helper/makeString": 20 }], 3: [function (require, module, exports) {
      var makeString = require('./helper/makeString');

      module.exports = function chars(str) {
        return makeString(str).split('');
      };
    }, { "./helper/makeString": 20 }], 4: [function (require, module, exports) {
      module.exports = function chop(str, step) {
        if (str == null) return [];
        str = String(str);
        step = ~~step;
        return step > 0 ? str.match(new RegExp('.{1,' + step + '}', 'g')) : [str];
      };
    }, {}], 5: [function (require, module, exports) {
      var capitalize = require('./capitalize');
      var camelize = require('./camelize');
      var makeString = require('./helper/makeString');

      module.exports = function classify(str) {
        str = makeString(str);
        return capitalize(camelize(str.replace(/[\W_]/g, ' ')).replace(/\s/g, ''));
      };
    }, { "./camelize": 1, "./capitalize": 2, "./helper/makeString": 20 }], 6: [function (require, module, exports) {
      var trim = require('./trim');

      module.exports = function clean(str) {
        return trim(str).replace(/\s\s+/g, ' ');
      };
    }, { "./trim": 65 }], 7: [function (require, module, exports) {

      var makeString = require('./helper/makeString');

      var from = 'ąàáäâãåæăćčĉęèéëêĝĥìíïîĵłľńňòóöőôõðøśșşšŝťțţŭùúüűûñÿýçżźž',
          to = 'aaaaaaaaaccceeeeeghiiiijllnnoooooooossssstttuuuuuunyyczzz';

      from += from.toUpperCase();
      to += to.toUpperCase();

      to = to.split('');

      // for tokens requireing multitoken output
      from += 'ß';
      to.push('ss');

      module.exports = function cleanDiacritics(str) {
        return makeString(str).replace(/.{1}/g, function (c) {
          var index = from.indexOf(c);
          return index === -1 ? c : to[index];
        });
      };
    }, { "./helper/makeString": 20 }], 8: [function (require, module, exports) {
      var makeString = require('./helper/makeString');

      module.exports = function (str, substr) {
        str = makeString(str);
        substr = makeString(substr);

        if (str.length === 0 || substr.length === 0) return 0;

        return str.split(substr).length - 1;
      };
    }, { "./helper/makeString": 20 }], 9: [function (require, module, exports) {
      var trim = require('./trim');

      module.exports = function dasherize(str) {
        return trim(str).replace(/([A-Z])/g, '-$1').replace(/[-_\s]+/g, '-').toLowerCase();
      };
    }, { "./trim": 65 }], 10: [function (require, module, exports) {
      var makeString = require('./helper/makeString');

      module.exports = function decapitalize(str) {
        str = makeString(str);
        return str.charAt(0).toLowerCase() + str.slice(1);
      };
    }, { "./helper/makeString": 20 }], 11: [function (require, module, exports) {
      var makeString = require('./helper/makeString');

      function getIndent(str) {
        var matches = str.match(/^[\s\\t]*/gm);
        var indent = matches[0].length;

        for (var i = 1; i < matches.length; i++) {
          indent = Math.min(matches[i].length, indent);
        }

        return indent;
      }

      module.exports = function dedent(str, pattern) {
        str = makeString(str);
        var indent = getIndent(str);
        var reg;

        if (indent === 0) return str;

        if (typeof pattern === 'string') {
          reg = new RegExp('^' + pattern, 'gm');
        } else {
          reg = new RegExp('^[ \\t]{' + indent + '}', 'gm');
        }

        return str.replace(reg, '');
      };
    }, { "./helper/makeString": 20 }], 12: [function (require, module, exports) {
      var makeString = require('./helper/makeString');
      var toPositive = require('./helper/toPositive');

      module.exports = function endsWith(str, ends, position) {
        str = makeString(str);
        ends = '' + ends;
        if (typeof position == 'undefined') {
          position = str.length - ends.length;
        } else {
          position = Math.min(toPositive(position), str.length) - ends.length;
        }
        return position >= 0 && str.indexOf(ends, position) === position;
      };
    }, { "./helper/makeString": 20, "./helper/toPositive": 22 }], 13: [function (require, module, exports) {
      var makeString = require('./helper/makeString');
      var escapeChars = require('./helper/escapeChars');

      var regexString = '[';
      for (var key in escapeChars) {
        regexString += key;
      }
      regexString += ']';

      var regex = new RegExp(regexString, 'g');

      module.exports = function escapeHTML(str) {

        return makeString(str).replace(regex, function (m) {
          return '&' + escapeChars[m] + ';';
        });
      };
    }, { "./helper/escapeChars": 17, "./helper/makeString": 20 }], 14: [function (require, module, exports) {
      module.exports = function () {
        var result = {};

        for (var prop in this) {
          if (!this.hasOwnProperty(prop) || prop.match(/^(?:include|contains|reverse|join|map|wrap)$/)) continue;
          result[prop] = this[prop];
        }

        return result;
      };
    }, {}], 15: [function (require, module, exports) {
      var makeString = require('./makeString');

      module.exports = function adjacent(str, direction) {
        str = makeString(str);
        if (str.length === 0) {
          return '';
        }
        return str.slice(0, -1) + String.fromCharCode(str.charCodeAt(str.length - 1) + direction);
      };
    }, { "./makeString": 20 }], 16: [function (require, module, exports) {
      var escapeRegExp = require('./escapeRegExp');

      module.exports = function defaultToWhiteSpace(characters) {
        if (characters == null) return '\\s';else if (characters.source) return characters.source;else return '[' + escapeRegExp(characters) + ']';
      };
    }, { "./escapeRegExp": 18 }], 17: [function (require, module, exports) {
      /* We're explicitly defining the list of entities we want to escape.
      nbsp is an HTML entity, but we don't want to escape all space characters in a string, hence its omission in this map.
      
      */
      var escapeChars = {
        '¢': 'cent',
        '£': 'pound',
        '¥': 'yen',
        '€': 'euro',
        '©': 'copy',
        '®': 'reg',
        '<': 'lt',
        '>': 'gt',
        '"': 'quot',
        '&': 'amp',
        '\'': '#39'
      };

      module.exports = escapeChars;
    }, {}], 18: [function (require, module, exports) {
      var makeString = require('./makeString');

      module.exports = function escapeRegExp(str) {
        return makeString(str).replace(/([.*+?^=!:${}()|[\]\/\\])/g, '\\$1');
      };
    }, { "./makeString": 20 }], 19: [function (require, module, exports) {
      /*
      We're explicitly defining the list of entities that might see in escape HTML strings
      */
      var htmlEntities = {
        nbsp: ' ',
        cent: '¢',
        pound: '£',
        yen: '¥',
        euro: '€',
        copy: '©',
        reg: '®',
        lt: '<',
        gt: '>',
        quot: '"',
        amp: '&',
        apos: '\''
      };

      module.exports = htmlEntities;
    }, {}], 20: [function (require, module, exports) {
      /**
       * Ensure some object is a coerced to a string
       **/
      module.exports = function makeString(object) {
        if (object == null) return '';
        return '' + object;
      };
    }, {}], 21: [function (require, module, exports) {
      module.exports = function strRepeat(str, qty) {
        if (qty < 1) return '';
        var result = '';
        while (qty > 0) {
          if (qty & 1) result += str;
          qty >>= 1, str += str;
        }
        return result;
      };
    }, {}], 22: [function (require, module, exports) {
      module.exports = function toPositive(number) {
        return number < 0 ? 0 : +number || 0;
      };
    }, {}], 23: [function (require, module, exports) {
      var capitalize = require('./capitalize');
      var underscored = require('./underscored');
      var trim = require('./trim');

      module.exports = function humanize(str) {
        return capitalize(trim(underscored(str).replace(/_id$/, '').replace(/_/g, ' ')));
      };
    }, { "./capitalize": 2, "./trim": 65, "./underscored": 67 }], 24: [function (require, module, exports) {
      var makeString = require('./helper/makeString');

      module.exports = function include(str, needle) {
        if (needle === '') return true;
        return makeString(str).indexOf(needle) !== -1;
      };
    }, { "./helper/makeString": 20 }], 25: [function (require, module, exports) {
      /*
      * Underscore.string
      * (c) 2010 Esa-Matti Suuronen <esa-matti aet suuronen dot org>
      * Underscore.string is freely distributable under the terms of the MIT license.
      * Documentation: https://github.com/epeli/underscore.string
      * Some code is borrowed from MooTools and Alexandru Marasteanu.
      * Version '3.3.4'
      * @preserve
      */

      'use strict';

      function s(value) {
        /* jshint validthis: true */
        if (!(this instanceof s)) return new s(value);
        this._wrapped = value;
      }

      s.VERSION = '3.3.4';

      s.isBlank = require('./isBlank');
      s.stripTags = require('./stripTags');
      s.capitalize = require('./capitalize');
      s.decapitalize = require('./decapitalize');
      s.chop = require('./chop');
      s.trim = require('./trim');
      s.clean = require('./clean');
      s.cleanDiacritics = require('./cleanDiacritics');
      s.count = require('./count');
      s.chars = require('./chars');
      s.swapCase = require('./swapCase');
      s.escapeHTML = require('./escapeHTML');
      s.unescapeHTML = require('./unescapeHTML');
      s.splice = require('./splice');
      s.insert = require('./insert');
      s.replaceAll = require('./replaceAll');
      s.include = require('./include');
      s.join = require('./join');
      s.lines = require('./lines');
      s.dedent = require('./dedent');
      s.reverse = require('./reverse');
      s.startsWith = require('./startsWith');
      s.endsWith = require('./endsWith');
      s.pred = require('./pred');
      s.succ = require('./succ');
      s.titleize = require('./titleize');
      s.camelize = require('./camelize');
      s.underscored = require('./underscored');
      s.dasherize = require('./dasherize');
      s.classify = require('./classify');
      s.humanize = require('./humanize');
      s.ltrim = require('./ltrim');
      s.rtrim = require('./rtrim');
      s.truncate = require('./truncate');
      s.prune = require('./prune');
      s.words = require('./words');
      s.pad = require('./pad');
      s.lpad = require('./lpad');
      s.rpad = require('./rpad');
      s.lrpad = require('./lrpad');
      s.sprintf = require('./sprintf');
      s.vsprintf = require('./vsprintf');
      s.toNumber = require('./toNumber');
      s.numberFormat = require('./numberFormat');
      s.strRight = require('./strRight');
      s.strRightBack = require('./strRightBack');
      s.strLeft = require('./strLeft');
      s.strLeftBack = require('./strLeftBack');
      s.toSentence = require('./toSentence');
      s.toSentenceSerial = require('./toSentenceSerial');
      s.slugify = require('./slugify');
      s.surround = require('./surround');
      s.quote = require('./quote');
      s.unquote = require('./unquote');
      s.repeat = require('./repeat');
      s.naturalCmp = require('./naturalCmp');
      s.levenshtein = require('./levenshtein');
      s.toBoolean = require('./toBoolean');
      s.exports = require('./exports');
      s.escapeRegExp = require('./helper/escapeRegExp');
      s.wrap = require('./wrap');
      s.map = require('./map');

      // Aliases
      s.strip = s.trim;
      s.lstrip = s.ltrim;
      s.rstrip = s.rtrim;
      s.center = s.lrpad;
      s.rjust = s.lpad;
      s.ljust = s.rpad;
      s.contains = s.include;
      s.q = s.quote;
      s.toBool = s.toBoolean;
      s.camelcase = s.camelize;
      s.mapChars = s.map;

      // Implement chaining
      s.prototype = {
        value: function value() {
          return this._wrapped;
        }
      };

      function fn2method(key, fn) {
        if (typeof fn !== 'function') return;
        s.prototype[key] = function () {
          var args = [this._wrapped].concat(Array.prototype.slice.call(arguments));
          var res = fn.apply(null, args);
          // if the result is non-string stop the chain and return the value
          return typeof res === 'string' ? new s(res) : res;
        };
      }

      // Copy functions to instance methods for chaining
      for (var key in s) {
        fn2method(key, s[key]);
      }fn2method('tap', function tap(string, fn) {
        return fn(string);
      });

      function prototype2method(methodName) {
        fn2method(methodName, function (context) {
          var args = Array.prototype.slice.call(arguments, 1);
          return String.prototype[methodName].apply(context, args);
        });
      }

      var prototypeMethods = ['toUpperCase', 'toLowerCase', 'split', 'replace', 'slice', 'substring', 'substr', 'concat'];

      for (var method in prototypeMethods) {
        prototype2method(prototypeMethods[method]);
      }module.exports = s;
    }, { "./camelize": 1, "./capitalize": 2, "./chars": 3, "./chop": 4, "./classify": 5, "./clean": 6, "./cleanDiacritics": 7, "./count": 8, "./dasherize": 9, "./decapitalize": 10, "./dedent": 11, "./endsWith": 12, "./escapeHTML": 13, "./exports": 14, "./helper/escapeRegExp": 18, "./humanize": 23, "./include": 24, "./insert": 26, "./isBlank": 27, "./join": 28, "./levenshtein": 29, "./lines": 30, "./lpad": 31, "./lrpad": 32, "./ltrim": 33, "./map": 34, "./naturalCmp": 35, "./numberFormat": 38, "./pad": 39, "./pred": 40, "./prune": 41, "./quote": 42, "./repeat": 43, "./replaceAll": 44, "./reverse": 45, "./rpad": 46, "./rtrim": 47, "./slugify": 48, "./splice": 49, "./sprintf": 50, "./startsWith": 51, "./strLeft": 52, "./strLeftBack": 53, "./strRight": 54, "./strRightBack": 55, "./stripTags": 56, "./succ": 57, "./surround": 58, "./swapCase": 59, "./titleize": 60, "./toBoolean": 61, "./toNumber": 62, "./toSentence": 63, "./toSentenceSerial": 64, "./trim": 65, "./truncate": 66, "./underscored": 67, "./unescapeHTML": 68, "./unquote": 69, "./vsprintf": 70, "./words": 71, "./wrap": 72 }], 26: [function (require, module, exports) {
      var splice = require('./splice');

      module.exports = function insert(str, i, substr) {
        return splice(str, i, 0, substr);
      };
    }, { "./splice": 49 }], 27: [function (require, module, exports) {
      var makeString = require('./helper/makeString');

      module.exports = function isBlank(str) {
        return (/^\s*$/.test(makeString(str))
        );
      };
    }, { "./helper/makeString": 20 }], 28: [function (require, module, exports) {
      var makeString = require('./helper/makeString');
      var slice = [].slice;

      module.exports = function join() {
        var args = slice.call(arguments),
            separator = args.shift();

        return args.join(makeString(separator));
      };
    }, { "./helper/makeString": 20 }], 29: [function (require, module, exports) {
      var makeString = require('./helper/makeString');

      /**
       * Based on the implementation here: https://github.com/hiddentao/fast-levenshtein
       */
      module.exports = function levenshtein(str1, str2) {
        'use strict';

        str1 = makeString(str1);
        str2 = makeString(str2);

        // Short cut cases  
        if (str1 === str2) return 0;
        if (!str1 || !str2) return Math.max(str1.length, str2.length);

        // two rows
        var prevRow = new Array(str2.length + 1);

        // initialise previous row
        for (var i = 0; i < prevRow.length; ++i) {
          prevRow[i] = i;
        }

        // calculate current row distance from previous row
        for (i = 0; i < str1.length; ++i) {
          var nextCol = i + 1;

          for (var j = 0; j < str2.length; ++j) {
            var curCol = nextCol;

            // substution
            nextCol = prevRow[j] + (str1.charAt(i) === str2.charAt(j) ? 0 : 1);
            // insertion
            var tmp = curCol + 1;
            if (nextCol > tmp) {
              nextCol = tmp;
            }
            // deletion
            tmp = prevRow[j + 1] + 1;
            if (nextCol > tmp) {
              nextCol = tmp;
            }

            // copy current col value into previous (in preparation for next iteration)
            prevRow[j] = curCol;
          }

          // copy last col value into previous (in preparation for next iteration)
          prevRow[j] = nextCol;
        }

        return nextCol;
      };
    }, { "./helper/makeString": 20 }], 30: [function (require, module, exports) {
      module.exports = function lines(str) {
        if (str == null) return [];
        return String(str).split(/\r\n?|\n/);
      };
    }, {}], 31: [function (require, module, exports) {
      var pad = require('./pad');

      module.exports = function lpad(str, length, padStr) {
        return pad(str, length, padStr);
      };
    }, { "./pad": 39 }], 32: [function (require, module, exports) {
      var pad = require('./pad');

      module.exports = function lrpad(str, length, padStr) {
        return pad(str, length, padStr, 'both');
      };
    }, { "./pad": 39 }], 33: [function (require, module, exports) {
      var makeString = require('./helper/makeString');
      var defaultToWhiteSpace = require('./helper/defaultToWhiteSpace');
      var nativeTrimLeft = String.prototype.trimLeft;

      module.exports = function ltrim(str, characters) {
        str = makeString(str);
        if (!characters && nativeTrimLeft) return nativeTrimLeft.call(str);
        characters = defaultToWhiteSpace(characters);
        return str.replace(new RegExp('^' + characters + '+'), '');
      };
    }, { "./helper/defaultToWhiteSpace": 16, "./helper/makeString": 20 }], 34: [function (require, module, exports) {
      var makeString = require('./helper/makeString');

      module.exports = function (str, callback) {
        str = makeString(str);

        if (str.length === 0 || typeof callback !== 'function') return str;

        return str.replace(/./g, callback);
      };
    }, { "./helper/makeString": 20 }], 35: [function (require, module, exports) {
      module.exports = function naturalCmp(str1, str2) {
        if (str1 == str2) return 0;
        if (!str1) return -1;
        if (!str2) return 1;

        var cmpRegex = /(\.\d+|\d+|\D+)/g,
            tokens1 = String(str1).match(cmpRegex),
            tokens2 = String(str2).match(cmpRegex),
            count = Math.min(tokens1.length, tokens2.length);

        for (var i = 0; i < count; i++) {
          var a = tokens1[i],
              b = tokens2[i];

          if (a !== b) {
            var num1 = +a;
            var num2 = +b;
            if (num1 === num1 && num2 === num2) {
              return num1 > num2 ? 1 : -1;
            }
            return a < b ? -1 : 1;
          }
        }

        if (tokens1.length != tokens2.length) return tokens1.length - tokens2.length;

        return str1 < str2 ? -1 : 1;
      };
    }, {}], 36: [function (require, module, exports) {
      (function (window) {
        var re = {
          not_string: /[^s]/,
          number: /[diefg]/,
          json: /[j]/,
          not_json: /[^j]/,
          text: /^[^\x25]+/,
          modulo: /^\x25{2}/,
          placeholder: /^\x25(?:([1-9]\d*)\$|\(([^\)]+)\))?(\+)?(0|'[^$])?(-)?(\d+)?(?:\.(\d+))?([b-gijosuxX])/,
          key: /^([a-z_][a-z_\d]*)/i,
          key_access: /^\.([a-z_][a-z_\d]*)/i,
          index_access: /^\[(\d+)\]/,
          sign: /^[\+\-]/
        };

        function sprintf() {
          var key = arguments[0],
              cache = sprintf.cache;
          if (!(cache[key] && cache.hasOwnProperty(key))) {
            cache[key] = sprintf.parse(key);
          }
          return sprintf.format.call(null, cache[key], arguments);
        }

        sprintf.format = function (parse_tree, argv) {
          var cursor = 1,
              tree_length = parse_tree.length,
              node_type = "",
              arg,
              output = [],
              i,
              k,
              match,
              pad,
              pad_character,
              pad_length,
              is_positive = true,
              sign = "";
          for (i = 0; i < tree_length; i++) {
            node_type = get_type(parse_tree[i]);
            if (node_type === "string") {
              output[output.length] = parse_tree[i];
            } else if (node_type === "array") {
              match = parse_tree[i]; // convenience purposes only
              if (match[2]) {
                // keyword argument
                arg = argv[cursor];
                for (k = 0; k < match[2].length; k++) {
                  if (!arg.hasOwnProperty(match[2][k])) {
                    throw new Error(sprintf("[sprintf] property '%s' does not exist", match[2][k]));
                  }
                  arg = arg[match[2][k]];
                }
              } else if (match[1]) {
                // positional argument (explicit)
                arg = argv[match[1]];
              } else {
                // positional argument (implicit)
                arg = argv[cursor++];
              }

              if (get_type(arg) == "function") {
                arg = arg();
              }

              if (re.not_string.test(match[8]) && re.not_json.test(match[8]) && get_type(arg) != "number" && isNaN(arg)) {
                throw new TypeError(sprintf("[sprintf] expecting number but found %s", get_type(arg)));
              }

              if (re.number.test(match[8])) {
                is_positive = arg >= 0;
              }

              switch (match[8]) {
                case "b":
                  arg = arg.toString(2);
                  break;
                case "c":
                  arg = String.fromCharCode(arg);
                  break;
                case "d":
                case "i":
                  arg = parseInt(arg, 10);
                  break;
                case "j":
                  arg = JSON.stringify(arg, null, match[6] ? parseInt(match[6]) : 0);
                  break;
                case "e":
                  arg = match[7] ? arg.toExponential(match[7]) : arg.toExponential();
                  break;
                case "f":
                  arg = match[7] ? parseFloat(arg).toFixed(match[7]) : parseFloat(arg);
                  break;
                case "g":
                  arg = match[7] ? parseFloat(arg).toPrecision(match[7]) : parseFloat(arg);
                  break;
                case "o":
                  arg = arg.toString(8);
                  break;
                case "s":
                  arg = (arg = String(arg)) && match[7] ? arg.substring(0, match[7]) : arg;
                  break;
                case "u":
                  arg = arg >>> 0;
                  break;
                case "x":
                  arg = arg.toString(16);
                  break;
                case "X":
                  arg = arg.toString(16).toUpperCase();
                  break;
              }
              if (re.json.test(match[8])) {
                output[output.length] = arg;
              } else {
                if (re.number.test(match[8]) && (!is_positive || match[3])) {
                  sign = is_positive ? "+" : "-";
                  arg = arg.toString().replace(re.sign, "");
                } else {
                  sign = "";
                }
                pad_character = match[4] ? match[4] === "0" ? "0" : match[4].charAt(1) : " ";
                pad_length = match[6] - (sign + arg).length;
                pad = match[6] ? pad_length > 0 ? str_repeat(pad_character, pad_length) : "" : "";
                output[output.length] = match[5] ? sign + arg + pad : pad_character === "0" ? sign + pad + arg : pad + sign + arg;
              }
            }
          }
          return output.join("");
        };

        sprintf.cache = {};

        sprintf.parse = function (fmt) {
          var _fmt = fmt,
              match = [],
              parse_tree = [],
              arg_names = 0;
          while (_fmt) {
            if ((match = re.text.exec(_fmt)) !== null) {
              parse_tree[parse_tree.length] = match[0];
            } else if ((match = re.modulo.exec(_fmt)) !== null) {
              parse_tree[parse_tree.length] = "%";
            } else if ((match = re.placeholder.exec(_fmt)) !== null) {
              if (match[2]) {
                arg_names |= 1;
                var field_list = [],
                    replacement_field = match[2],
                    field_match = [];
                if ((field_match = re.key.exec(replacement_field)) !== null) {
                  field_list[field_list.length] = field_match[1];
                  while ((replacement_field = replacement_field.substring(field_match[0].length)) !== "") {
                    if ((field_match = re.key_access.exec(replacement_field)) !== null) {
                      field_list[field_list.length] = field_match[1];
                    } else if ((field_match = re.index_access.exec(replacement_field)) !== null) {
                      field_list[field_list.length] = field_match[1];
                    } else {
                      throw new SyntaxError("[sprintf] failed to parse named argument key");
                    }
                  }
                } else {
                  throw new SyntaxError("[sprintf] failed to parse named argument key");
                }
                match[2] = field_list;
              } else {
                arg_names |= 2;
              }
              if (arg_names === 3) {
                throw new Error("[sprintf] mixing positional and named placeholders is not (yet) supported");
              }
              parse_tree[parse_tree.length] = match;
            } else {
              throw new SyntaxError("[sprintf] unexpected placeholder");
            }
            _fmt = _fmt.substring(match[0].length);
          }
          return parse_tree;
        };

        var vsprintf = function vsprintf(fmt, argv, _argv) {
          _argv = (argv || []).slice(0);
          _argv.splice(0, 0, fmt);
          return sprintf.apply(null, _argv);
        };

        /**
         * helpers
         */
        function get_type(variable) {
          return Object.prototype.toString.call(variable).slice(8, -1).toLowerCase();
        }

        function str_repeat(input, multiplier) {
          return Array(multiplier + 1).join(input);
        }

        /**
         * export to either browser or node.js
         */
        if (typeof exports !== "undefined") {
          exports.sprintf = sprintf;
          exports.vsprintf = vsprintf;
        } else {
          window.sprintf = sprintf;
          window.vsprintf = vsprintf;

          if (typeof define === "function" && define.amd) {
            define(function () {
              return {
                sprintf: sprintf,
                vsprintf: vsprintf
              };
            });
          }
        }
      })(typeof window === "undefined" ? this : window);
    }, {}], 37: [function (require, module, exports) {
      (function (global) {

        /**
         * Module exports.
         */

        module.exports = deprecate;

        /**
         * Mark that a method should not be used.
         * Returns a modified function which warns once by default.
         *
         * If `localStorage.noDeprecation = true` is set, then it is a no-op.
         *
         * If `localStorage.throwDeprecation = true` is set, then deprecated functions
         * will throw an Error when invoked.
         *
         * If `localStorage.traceDeprecation = true` is set, then deprecated functions
         * will invoke `console.trace()` instead of `console.error()`.
         *
         * @param {Function} fn - the function to deprecate
         * @param {String} msg - the string to print to the console when `fn` is invoked
         * @returns {Function} a new "deprecated" version of `fn`
         * @api public
         */

        function deprecate(fn, msg) {
          if (config('noDeprecation')) {
            return fn;
          }

          var warned = false;
          function deprecated() {
            if (!warned) {
              if (config('throwDeprecation')) {
                throw new Error(msg);
              } else if (config('traceDeprecation')) {
                console.trace(msg);
              } else {
                console.warn(msg);
              }
              warned = true;
            }
            return fn.apply(this, arguments);
          }

          return deprecated;
        }

        /**
         * Checks `localStorage` for boolean values for the given `name`.
         *
         * @param {String} name
         * @returns {Boolean}
         * @api private
         */

        function config(name) {
          // accessing global.localStorage can trigger a DOMException in sandboxed iframes
          try {
            if (!global.localStorage) return false;
          } catch (_) {
            return false;
          }
          var val = global.localStorage[name];
          if (null == val) return false;
          return String(val).toLowerCase() === 'true';
        }
      }).call(this, typeof global !== "undefined" ? global : typeof self !== "undefined" ? self : typeof window !== "undefined" ? window : {});
    }, {}], 38: [function (require, module, exports) {
      module.exports = function numberFormat(number, dec, dsep, tsep) {
        if (isNaN(number) || number == null) return '';

        number = number.toFixed(~~dec);
        tsep = typeof tsep == 'string' ? tsep : ',';

        var parts = number.split('.'),
            fnums = parts[0],
            decimals = parts[1] ? (dsep || '.') + parts[1] : '';

        return fnums.replace(/(\d)(?=(?:\d{3})+$)/g, '$1' + tsep) + decimals;
      };
    }, {}], 39: [function (require, module, exports) {
      var makeString = require('./helper/makeString');
      var strRepeat = require('./helper/strRepeat');

      module.exports = function pad(str, length, padStr, type) {
        str = makeString(str);
        length = ~~length;

        var padlen = 0;

        if (!padStr) padStr = ' ';else if (padStr.length > 1) padStr = padStr.charAt(0);

        switch (type) {
          case 'right':
            padlen = length - str.length;
            return str + strRepeat(padStr, padlen);
          case 'both':
            padlen = length - str.length;
            return strRepeat(padStr, Math.ceil(padlen / 2)) + str + strRepeat(padStr, Math.floor(padlen / 2));
          default:
            // 'left'
            padlen = length - str.length;
            return strRepeat(padStr, padlen) + str;
        }
      };
    }, { "./helper/makeString": 20, "./helper/strRepeat": 21 }], 40: [function (require, module, exports) {
      var adjacent = require('./helper/adjacent');

      module.exports = function succ(str) {
        return adjacent(str, -1);
      };
    }, { "./helper/adjacent": 15 }], 41: [function (require, module, exports) {
      /**
       * _s.prune: a more elegant version of truncate
       * prune extra chars, never leaving a half-chopped word.
       * @author github.com/rwz
       */
      var makeString = require('./helper/makeString');
      var rtrim = require('./rtrim');

      module.exports = function prune(str, length, pruneStr) {
        str = makeString(str);
        length = ~~length;
        pruneStr = pruneStr != null ? String(pruneStr) : '...';

        if (str.length <= length) return str;

        var tmpl = function tmpl(c) {
          return c.toUpperCase() !== c.toLowerCase() ? 'A' : ' ';
        },
            template = str.slice(0, length + 1).replace(/.(?=\W*\w*$)/g, tmpl); // 'Hello, world' -> 'HellAA AAAAA'

        if (template.slice(template.length - 2).match(/\w\w/)) template = template.replace(/\s*\S+$/, '');else template = rtrim(template.slice(0, template.length - 1));

        return (template + pruneStr).length > str.length ? str : str.slice(0, template.length) + pruneStr;
      };
    }, { "./helper/makeString": 20, "./rtrim": 47 }], 42: [function (require, module, exports) {
      var surround = require('./surround');

      module.exports = function quote(str, quoteChar) {
        return surround(str, quoteChar || '"');
      };
    }, { "./surround": 58 }], 43: [function (require, module, exports) {
      var makeString = require('./helper/makeString');
      var strRepeat = require('./helper/strRepeat');

      module.exports = function repeat(str, qty, separator) {
        str = makeString(str);

        qty = ~~qty;

        // using faster implementation if separator is not needed;
        if (separator == null) return strRepeat(str, qty);

        // this one is about 300x slower in Google Chrome
        /*eslint no-empty: 0*/
        for (var repeat = []; qty > 0; repeat[--qty] = str) {}
        return repeat.join(separator);
      };
    }, { "./helper/makeString": 20, "./helper/strRepeat": 21 }], 44: [function (require, module, exports) {
      var makeString = require('./helper/makeString');

      module.exports = function replaceAll(str, find, replace, ignorecase) {
        var flags = ignorecase === true ? 'gi' : 'g';
        var reg = new RegExp(find, flags);

        return makeString(str).replace(reg, replace);
      };
    }, { "./helper/makeString": 20 }], 45: [function (require, module, exports) {
      var chars = require('./chars');

      module.exports = function reverse(str) {
        return chars(str).reverse().join('');
      };
    }, { "./chars": 3 }], 46: [function (require, module, exports) {
      var pad = require('./pad');

      module.exports = function rpad(str, length, padStr) {
        return pad(str, length, padStr, 'right');
      };
    }, { "./pad": 39 }], 47: [function (require, module, exports) {
      var makeString = require('./helper/makeString');
      var defaultToWhiteSpace = require('./helper/defaultToWhiteSpace');
      var nativeTrimRight = String.prototype.trimRight;

      module.exports = function rtrim(str, characters) {
        str = makeString(str);
        if (!characters && nativeTrimRight) return nativeTrimRight.call(str);
        characters = defaultToWhiteSpace(characters);
        return str.replace(new RegExp(characters + '+$'), '');
      };
    }, { "./helper/defaultToWhiteSpace": 16, "./helper/makeString": 20 }], 48: [function (require, module, exports) {
      var trim = require('./trim');
      var dasherize = require('./dasherize');
      var cleanDiacritics = require('./cleanDiacritics');

      module.exports = function slugify(str) {
        return trim(dasherize(cleanDiacritics(str).replace(/[^\w\s-]/g, '-').toLowerCase()), '-');
      };
    }, { "./cleanDiacritics": 7, "./dasherize": 9, "./trim": 65 }], 49: [function (require, module, exports) {
      var chars = require('./chars');

      module.exports = function splice(str, i, howmany, substr) {
        var arr = chars(str);
        arr.splice(~~i, ~~howmany, substr);
        return arr.join('');
      };
    }, { "./chars": 3 }], 50: [function (require, module, exports) {
      var deprecate = require('util-deprecate');

      module.exports = deprecate(require('sprintf-js').sprintf, 'sprintf() will be removed in the next major release, use the sprintf-js package instead.');
    }, { "sprintf-js": 36, "util-deprecate": 37 }], 51: [function (require, module, exports) {
      var makeString = require('./helper/makeString');
      var toPositive = require('./helper/toPositive');

      module.exports = function startsWith(str, starts, position) {
        str = makeString(str);
        starts = '' + starts;
        position = position == null ? 0 : Math.min(toPositive(position), str.length);
        return str.lastIndexOf(starts, position) === position;
      };
    }, { "./helper/makeString": 20, "./helper/toPositive": 22 }], 52: [function (require, module, exports) {
      var makeString = require('./helper/makeString');

      module.exports = function strLeft(str, sep) {
        str = makeString(str);
        sep = makeString(sep);
        var pos = !sep ? -1 : str.indexOf(sep);
        return ~pos ? str.slice(0, pos) : str;
      };
    }, { "./helper/makeString": 20 }], 53: [function (require, module, exports) {
      var makeString = require('./helper/makeString');

      module.exports = function strLeftBack(str, sep) {
        str = makeString(str);
        sep = makeString(sep);
        var pos = str.lastIndexOf(sep);
        return ~pos ? str.slice(0, pos) : str;
      };
    }, { "./helper/makeString": 20 }], 54: [function (require, module, exports) {
      var makeString = require('./helper/makeString');

      module.exports = function strRight(str, sep) {
        str = makeString(str);
        sep = makeString(sep);
        var pos = !sep ? -1 : str.indexOf(sep);
        return ~pos ? str.slice(pos + sep.length, str.length) : str;
      };
    }, { "./helper/makeString": 20 }], 55: [function (require, module, exports) {
      var makeString = require('./helper/makeString');

      module.exports = function strRightBack(str, sep) {
        str = makeString(str);
        sep = makeString(sep);
        var pos = !sep ? -1 : str.lastIndexOf(sep);
        return ~pos ? str.slice(pos + sep.length, str.length) : str;
      };
    }, { "./helper/makeString": 20 }], 56: [function (require, module, exports) {
      var makeString = require('./helper/makeString');

      module.exports = function stripTags(str) {
        return makeString(str).replace(/<\/?[^>]+>/g, '');
      };
    }, { "./helper/makeString": 20 }], 57: [function (require, module, exports) {
      var adjacent = require('./helper/adjacent');

      module.exports = function succ(str) {
        return adjacent(str, 1);
      };
    }, { "./helper/adjacent": 15 }], 58: [function (require, module, exports) {
      module.exports = function surround(str, wrapper) {
        return [wrapper, str, wrapper].join('');
      };
    }, {}], 59: [function (require, module, exports) {
      var makeString = require('./helper/makeString');

      module.exports = function swapCase(str) {
        return makeString(str).replace(/\S/g, function (c) {
          return c === c.toUpperCase() ? c.toLowerCase() : c.toUpperCase();
        });
      };
    }, { "./helper/makeString": 20 }], 60: [function (require, module, exports) {
      var makeString = require('./helper/makeString');

      module.exports = function titleize(str) {
        return makeString(str).toLowerCase().replace(/(?:^|\s|-)\S/g, function (c) {
          return c.toUpperCase();
        });
      };
    }, { "./helper/makeString": 20 }], 61: [function (require, module, exports) {
      var trim = require('./trim');

      function boolMatch(s, matchers) {
        var i,
            matcher,
            down = s.toLowerCase();
        matchers = [].concat(matchers);
        for (i = 0; i < matchers.length; i += 1) {
          matcher = matchers[i];
          if (!matcher) continue;
          if (matcher.test && matcher.test(s)) return true;
          if (matcher.toLowerCase() === down) return true;
        }
      }

      module.exports = function toBoolean(str, trueValues, falseValues) {
        if (typeof str === 'number') str = '' + str;
        if (typeof str !== 'string') return !!str;
        str = trim(str);
        if (boolMatch(str, trueValues || ['true', '1'])) return true;
        if (boolMatch(str, falseValues || ['false', '0'])) return false;
      };
    }, { "./trim": 65 }], 62: [function (require, module, exports) {
      module.exports = function toNumber(num, precision) {
        if (num == null) return 0;
        var factor = Math.pow(10, isFinite(precision) ? precision : 0);
        return Math.round(num * factor) / factor;
      };
    }, {}], 63: [function (require, module, exports) {
      var rtrim = require('./rtrim');

      module.exports = function toSentence(array, separator, lastSeparator, serial) {
        separator = separator || ', ';
        lastSeparator = lastSeparator || ' and ';
        var a = array.slice(),
            lastMember = a.pop();

        if (array.length > 2 && serial) lastSeparator = rtrim(separator) + lastSeparator;

        return a.length ? a.join(separator) + lastSeparator + lastMember : lastMember;
      };
    }, { "./rtrim": 47 }], 64: [function (require, module, exports) {
      var toSentence = require('./toSentence');

      module.exports = function toSentenceSerial(array, sep, lastSep) {
        return toSentence(array, sep, lastSep, true);
      };
    }, { "./toSentence": 63 }], 65: [function (require, module, exports) {
      var makeString = require('./helper/makeString');
      var defaultToWhiteSpace = require('./helper/defaultToWhiteSpace');
      var nativeTrim = String.prototype.trim;

      module.exports = function trim(str, characters) {
        str = makeString(str);
        if (!characters && nativeTrim) return nativeTrim.call(str);
        characters = defaultToWhiteSpace(characters);
        return str.replace(new RegExp('^' + characters + '+|' + characters + '+$', 'g'), '');
      };
    }, { "./helper/defaultToWhiteSpace": 16, "./helper/makeString": 20 }], 66: [function (require, module, exports) {
      var makeString = require('./helper/makeString');

      module.exports = function truncate(str, length, truncateStr) {
        str = makeString(str);
        truncateStr = truncateStr || '...';
        length = ~~length;
        return str.length > length ? str.slice(0, length) + truncateStr : str;
      };
    }, { "./helper/makeString": 20 }], 67: [function (require, module, exports) {
      var trim = require('./trim');

      module.exports = function underscored(str) {
        return trim(str).replace(/([a-z\d])([A-Z]+)/g, '$1_$2').replace(/[-\s]+/g, '_').toLowerCase();
      };
    }, { "./trim": 65 }], 68: [function (require, module, exports) {
      var makeString = require('./helper/makeString');
      var htmlEntities = require('./helper/htmlEntities');

      module.exports = function unescapeHTML(str) {
        return makeString(str).replace(/\&([^;]+);/g, function (entity, entityCode) {
          var match;

          if (entityCode in htmlEntities) {
            return htmlEntities[entityCode];
            /*eslint no-cond-assign: 0*/
          } else if (match = entityCode.match(/^#x([\da-fA-F]+)$/)) {
            return String.fromCharCode(parseInt(match[1], 16));
            /*eslint no-cond-assign: 0*/
          } else if (match = entityCode.match(/^#(\d+)$/)) {
            return String.fromCharCode(~~match[1]);
          } else {
            return entity;
          }
        });
      };
    }, { "./helper/htmlEntities": 19, "./helper/makeString": 20 }], 69: [function (require, module, exports) {
      module.exports = function unquote(str, quoteChar) {
        quoteChar = quoteChar || '"';
        if (str[0] === quoteChar && str[str.length - 1] === quoteChar) return str.slice(1, str.length - 1);else return str;
      };
    }, {}], 70: [function (require, module, exports) {
      var deprecate = require('util-deprecate');

      module.exports = deprecate(require('sprintf-js').vsprintf, 'vsprintf() will be removed in the next major release, use the sprintf-js package instead.');
    }, { "sprintf-js": 36, "util-deprecate": 37 }], 71: [function (require, module, exports) {
      var isBlank = require('./isBlank');
      var trim = require('./trim');

      module.exports = function words(str, delimiter) {
        if (isBlank(str)) return [];
        return trim(str, delimiter).split(delimiter || /\s+/);
      };
    }, { "./isBlank": 27, "./trim": 65 }], 72: [function (require, module, exports) {
      // Wrap
      // wraps a string by a certain width

      var makeString = require('./helper/makeString');

      module.exports = function wrap(str, options) {
        str = makeString(str);

        options = options || {};

        var width = options.width || 75;
        var seperator = options.seperator || '\n';
        var cut = options.cut || false;
        var preserveSpaces = options.preserveSpaces || false;
        var trailingSpaces = options.trailingSpaces || false;

        var result;

        if (width <= 0) {
          return str;
        } else if (!cut) {

          var words = str.split(' ');
          var current_column = 0;
          result = '';

          while (words.length > 0) {

            // if adding a space and the next word would cause this line to be longer than width...
            if (1 + words[0].length + current_column > width) {
              //start a new line if this line is not already empty
              if (current_column > 0) {
                // add a space at the end of the line is preserveSpaces is true
                if (preserveSpaces) {
                  result += ' ';
                  current_column++;
                }
                // fill the rest of the line with spaces if trailingSpaces option is true
                else if (trailingSpaces) {
                    while (current_column < width) {
                      result += ' ';
                      current_column++;
                    }
                  }
                //start new line
                result += seperator;
                current_column = 0;
              }
            }

            // if not at the begining of the line, add a space in front of the word
            if (current_column > 0) {
              result += ' ';
              current_column++;
            }

            // tack on the next word, update current column, a pop words array
            result += words[0];
            current_column += words[0].length;
            words.shift();
          }

          // fill the rest of the line with spaces if trailingSpaces option is true
          if (trailingSpaces) {
            while (current_column < width) {
              result += ' ';
              current_column++;
            }
          }

          return result;
        } else {

          var index = 0;
          result = '';

          // walk through each character and add seperators where appropriate
          while (index < str.length) {
            if (index % width == 0 && index > 0) {
              result += seperator;
            }
            result += str.charAt(index);
            index++;
          }

          // fill the rest of the line with spaces if trailingSpaces option is true
          if (trailingSpaces) {
            while (index % width > 0) {
              result += ' ';
              index++;
            }
          }

          return result;
        }
      };
    }, { "./helper/makeString": 20 }] }, {}, [25])(25);
});
/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__("./node_modules/webpack/buildin/global.js")))

/***/ }),

/***/ "./common/static/common/templates/components/system-feedback.underscore":
/***/ (function(module, exports) {

module.exports = "<div class=\"wrapper wrapper-<%- type %> wrapper-<%- type %>-<%- intent %>\n            <% if(obj.shown) { %>is-shown<% } else { %>is-hiding<% } %>\n            <% if(_.contains(['help', 'mini'], intent)) { %>wrapper-<%- type %>-status<% } %>\"\n     id=\"<%- type %>-<%- intent %>\"\n     aria-hidden=\"<% if(obj.shown) { %>false<% } else { %>true<% } %>\"\n     aria-labelledby=\"<%- type %>-<%- intent %>-title\"\n     tabindex=\"-1\"\n     <% if (obj.message) { %>aria-describedby=\"<%- type %>-<%- intent %>-description\" <% } %>\n     <% if (obj.actions) { %>role=\"dialog\"<% } %>\n  >\n  <div class=\"<%- type %> <%- intent %> <% if(obj.actions) { %>has-actions<% } %>\">\n    <% if(obj.icon) { %>\n      <% var iconClass = {\"warning\": \"warning\", \"confirmation\": \"check\", \"error\": \"warning\", \"announcement\": \"bullhorn\", \"step-required\": \"exclamation-circle\", \"help\": \"question\", \"mini\": \"cog\"} %>\n      <span class=\"feedback-symbol fa fa-<%- iconClass[intent] %>\" aria-hidden=\"true\"></span>\n    <% } %>\n\n    <div class=\"copy\">\n      <h2 class=\"title title-3\" id=\"<%- type %>-<%- intent %>-title\"><%- title %></h2>\n      <% if(obj.message) { %><p class=\"message\" id=\"<%- type %>-<%- intent %>-description\"><%- message %></p><% } %>\n    </div>\n\n    <% if(obj.actions) { %>\n    <nav class=\"nav-actions\">\n      <ul>\n        <% if(actions.primary) { %>\n        <li class=\"nav-item\">\n          <button class=\"action-primary <%- actions.primary.class %>\"><%- actions.primary.text %></button>\n        </li>\n        <% } %>\n        <% if(actions.secondary) {\n             _.each(actions.secondary, function(secondary) { %>\n        <li class=\"nav-item\">\n          <button class=\"action-secondary <%- secondary.class %>\"><%- secondary.text %></button>\n        </li>\n        <%   });\n           } %>\n      </ul>\n    </nav>\n    <% } %>\n\n    <% if(obj.closeIcon) { %>\n    <a href=\"#\" rel=\"view\" class=\"action action-close action-<%- type %>-close\">\n      <span class=\"icon fa fa-times-circle\" aria-hidden=\"true\"></span>\n      <span class=\"label\">close <%- type %></span>\n    </a>\n    <% } %>\n  </div>\n</div>\n"

/***/ }),

/***/ "./node_modules/scriptjs/dist/script.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_FACTORY__, __WEBPACK_AMD_DEFINE_RESULT__;/*!
  * $script.js JS loader & dependency manager
  * https://github.com/ded/script.js
  * (c) Dustin Diaz 2014 | License MIT
  */

(function (name, definition) {
  if (typeof module != 'undefined' && module.exports) module.exports = definition()
  else if (true) !(__WEBPACK_AMD_DEFINE_FACTORY__ = (definition),
				__WEBPACK_AMD_DEFINE_RESULT__ = (typeof __WEBPACK_AMD_DEFINE_FACTORY__ === 'function' ?
				(__WEBPACK_AMD_DEFINE_FACTORY__.call(exports, __webpack_require__, exports, module)) :
				__WEBPACK_AMD_DEFINE_FACTORY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__))
  else this[name] = definition()
})('$script', function () {
  var doc = document
    , head = doc.getElementsByTagName('head')[0]
    , s = 'string'
    , f = false
    , push = 'push'
    , readyState = 'readyState'
    , onreadystatechange = 'onreadystatechange'
    , list = {}
    , ids = {}
    , delay = {}
    , scripts = {}
    , scriptpath
    , urlArgs

  function every(ar, fn) {
    for (var i = 0, j = ar.length; i < j; ++i) if (!fn(ar[i])) return f
    return 1
  }
  function each(ar, fn) {
    every(ar, function (el) {
      return !fn(el)
    })
  }

  function $script(paths, idOrDone, optDone) {
    paths = paths[push] ? paths : [paths]
    var idOrDoneIsDone = idOrDone && idOrDone.call
      , done = idOrDoneIsDone ? idOrDone : optDone
      , id = idOrDoneIsDone ? paths.join('') : idOrDone
      , queue = paths.length
    function loopFn(item) {
      return item.call ? item() : list[item]
    }
    function callback() {
      if (!--queue) {
        list[id] = 1
        done && done()
        for (var dset in delay) {
          every(dset.split('|'), loopFn) && !each(delay[dset], loopFn) && (delay[dset] = [])
        }
      }
    }
    setTimeout(function () {
      each(paths, function loading(path, force) {
        if (path === null) return callback()
        
        if (!force && !/^https?:\/\//.test(path) && scriptpath) {
          path = (path.indexOf('.js') === -1) ? scriptpath + path + '.js' : scriptpath + path;
        }
        
        if (scripts[path]) {
          if (id) ids[id] = 1
          return (scripts[path] == 2) ? callback() : setTimeout(function () { loading(path, true) }, 0)
        }

        scripts[path] = 1
        if (id) ids[id] = 1
        create(path, callback)
      })
    }, 0)
    return $script
  }

  function create(path, fn) {
    var el = doc.createElement('script'), loaded
    el.onload = el.onerror = el[onreadystatechange] = function () {
      if ((el[readyState] && !(/^c|loade/.test(el[readyState]))) || loaded) return;
      el.onload = el[onreadystatechange] = null
      loaded = 1
      scripts[path] = 2
      fn()
    }
    el.async = 1
    el.src = urlArgs ? path + (path.indexOf('?') === -1 ? '?' : '&') + urlArgs : path;
    head.insertBefore(el, head.lastChild)
  }

  $script.get = create

  $script.order = function (scripts, id, done) {
    (function callback(s) {
      s = scripts.shift()
      !scripts.length ? $script(s, id, done) : $script(s, callback)
    }())
  }

  $script.path = function (p) {
    scriptpath = p
  }
  $script.urlArgs = function (str) {
    urlArgs = str;
  }
  $script.ready = function (deps, ready, req) {
    deps = deps[push] ? deps : [deps]
    var missing = [];
    !each(deps, function (dep) {
      list[dep] || missing[push](dep);
    }) && every(deps, function (dep) {return list[dep]}) ?
      ready() : !function (key) {
      delay[key] = delay[key] || []
      delay[key][push](ready)
      req && req(missing)
    }(deps.join('|'))
    return $script
  }

  $script.done = function (idOrDone) {
    $script([null], idOrDone)
  }

  return $script
});


/***/ }),

/***/ 3:
/***/ (function(module, exports) {

(function() { module.exports = window["gettext"]; }());

/***/ })

},["./cms/static/js/factories/xblock_validation.js"])));
//# sourceMappingURL=xblock_validation.js.map
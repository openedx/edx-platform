(function(e, a) { for(var i in a) e[i] = a[i]; }(window, webpackJsonp([11],{

/***/ "./cms/static/cms/js/main.js":
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(AjaxPrefix, jQuery) {var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;/* globals AjaxPrefix */

!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__("./common/static/js/vendor/domReady.js"), __webpack_require__(0), __webpack_require__(1), __webpack_require__("./common/static/common/js/vendor/underscore.string.js"), __webpack_require__(2), __webpack_require__(3), __webpack_require__("./common/static/common/js/components/views/feedback_notification.js"), __webpack_require__("./common/static/js/src/ajax_prefix.js"), __webpack_require__("./common/static/js/src/ajax_prefix.js"), __webpack_require__("./common/static/js/vendor/jquery.cookie.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function (domReady, $, _, str, Backbone, gettext, NotificationView) {
    'use strict';

    var main, sendJSON;
    main = function main() {
        AjaxPrefix.addAjaxPrefix(jQuery, function () {
            return $("meta[name='path_prefix']").attr('content');
        });
        window.CMS = window.CMS || {};
        window.CMS.URL = window.CMS.URL || {};
        window.onTouchBasedDevice = function () {
            return navigator.userAgent.match(/iPhone|iPod|iPad|Android/i);
        };
        _.extend(window.CMS, Backbone.Events);
        Backbone.emulateHTTP = true;
        $.ajaxSetup({
            headers: {
                'X-CSRFToken': $.cookie('csrftoken')
            },
            dataType: 'json',
            content: {
                script: false
            }
        });
        $(document).ajaxError(function (event, jqXHR, ajaxSettings) {
            var msg,
                contentType,
                message = gettext('This may be happening because of an error with our server or your internet connection. Try refreshing the page or making sure you are online.'); // eslint-disable-line max-len
            if (ajaxSettings.notifyOnError === false) {
                return;
            }
            contentType = jqXHR.getResponseHeader('content-type');
            if (contentType && contentType.indexOf('json') > -1 && jqXHR.responseText) {
                message = JSON.parse(jqXHR.responseText).error;
            }
            msg = new NotificationView.Error({
                title: gettext("Studio's having trouble saving your work"),
                message: message
            });
            console.log('Studio AJAX Error', { // eslint-disable-line no-console
                url: event.currentTarget.URL,
                response: jqXHR.responseText,
                status: jqXHR.status
            });
            return msg.show();
        });
        sendJSON = function sendJSON(url, data, callback, type) {
            // eslint-disable-line no-param-reassign
            if ($.isFunction(data)) {
                callback = data;
                data = undefined;
            }
            return $.ajax({
                url: url,
                type: type,
                contentType: 'application/json; charset=utf-8',
                dataType: 'json',
                data: JSON.stringify(data),
                success: callback,
                global: data ? data.global : true // Trigger global AJAX error handler or not
            });
        };
        $.postJSON = function (url, data, callback) {
            // eslint-disable-line no-param-reassign
            return sendJSON(url, data, callback, 'POST');
        };
        $.patchJSON = function (url, data, callback) {
            // eslint-disable-line no-param-reassign
            return sendJSON(url, data, callback, 'PATCH');
        };
        return domReady(function () {
            if (window.onTouchBasedDevice()) {
                return $('body').addClass('touch-based-device');
            }
            return null;
        });
    };
    main();
    return main;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));
/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__("./common/static/js/src/ajax_prefix.js"), __webpack_require__(0)))

/***/ }),

/***/ "./cms/static/js/base.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__("./common/static/js/vendor/domReady.js"), __webpack_require__(0), __webpack_require__(1), __webpack_require__(3), __webpack_require__("./common/static/common/js/components/views/feedback_notification.js"), __webpack_require__("./common/static/common/js/components/views/feedback_prompt.js"), __webpack_require__("./cms/static/js/utils/date_utils.js"), __webpack_require__("./cms/static/js/utils/module.js"), __webpack_require__("./cms/static/js/utils/handle_iframe_binding.js"), __webpack_require__("./node_modules/edx-ui-toolkit/src/js/dropdown-menu/dropdown-menu-view.js"), __webpack_require__("./common/static/js/vendor/jquery-ui.min.js"), __webpack_require__("./common/static/js/vendor/jquery.leanModal.js"), __webpack_require__("./common/static/js/vendor/jquery.form.js"), __webpack_require__("./common/static/js/vendor/jquery.smooth-scroll.min.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function (domReady, $, _, gettext, NotificationView, PromptView, DateUtils, ModuleUtils, IframeUtils, DropdownMenuView) {
    'use strict';

    var $body;

    function smoothScrollLink(e) {
        e.preventDefault();

        $.smoothScroll({
            offset: -200,
            easing: 'swing',
            speed: 1000,
            scrollElement: null,
            scrollTarget: $(this).attr('href')
        });
    }

    function hideNotification(e) {
        e.preventDefault();
        $(this).closest('.wrapper-notification').removeClass('is-shown').addClass('is-hiding').attr('aria-hidden', 'true');
    }

    function hideAlert(e) {
        e.preventDefault();
        $(this).closest('.wrapper-alert').removeClass('is-shown');
    }

    domReady(function () {
        var dropdownMenuView;

        $body = $('body');

        $body.on('click', '.embeddable-xml-input', function () {
            $(this).select();
        });

        $body.addClass('js');

        // alerts/notifications - manual close
        $('.action-alert-close, .alert.has-actions .nav-actions a').bind('click', hideAlert);
        $('.action-notification-close').bind('click', hideNotification);

        // nav - dropdown related
        $body.click(function () {
            $('.nav-dd .nav-item .wrapper-nav-sub').removeClass('is-shown');
            $('.nav-dd .nav-item .title').removeClass('is-selected');
        });

        $('.nav-dd .nav-item, .filterable-column .nav-item').click(function (e) {
            var $subnav = $(this).find('.wrapper-nav-sub'),
                $title = $(this).find('.title');

            if ($subnav.hasClass('is-shown')) {
                $subnav.removeClass('is-shown');
                $title.removeClass('is-selected');
            } else {
                $('.nav-dd .nav-item .title').removeClass('is-selected');
                $('.nav-dd .nav-item .wrapper-nav-sub').removeClass('is-shown');
                $title.addClass('is-selected');
                $subnav.addClass('is-shown');
                // if propagation is not stopped, the event will bubble up to the
                // body element, which will close the dropdown.
                e.stopPropagation();
            }
        });

        // general link management - new window/tab
        $('a[rel="external"]:not([title])').attr('title', gettext('This link will open in a new browser window/tab'));
        $('a[rel="external"]').attr({
            rel: 'noopener external',
            target: '_blank'
        });

        // general link management - lean modal window
        $('a[rel="modal"]').attr('title', gettext('This link will open in a modal window')).leanModal({
            overlay: 0.50,
            closeButton: '.action-modal-close'
        });
        $('.action-modal-close').click(function (e) {
            e.preventDefault();
        });

        // general link management - smooth scrolling page links
        $('a[rel*="view"][href^="#"]').bind('click', smoothScrollLink);

        IframeUtils.iframeBinding();

        // disable ajax caching in IE so that backbone fetches work
        if ($.browser.msie) {
            $.ajaxSetup({ cache: false });
        }

        // Initiate the edx tool kit dropdown menu
        if ($('.js-header-user-menu').length) {
            dropdownMenuView = new DropdownMenuView({
                el: '.js-header-user-menu'
            });
            dropdownMenuView.postRender();
        }

        window.studioNavMenuActive = true;
    });
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__)); // end require()

/***/ }),

/***/ "./cms/static/js/collections/chapter.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(2), __webpack_require__("./cms/static/js/models/chapter.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function (Backbone, ChapterModel) {
    var ChapterCollection = Backbone.Collection.extend({
        model: ChapterModel,
        comparator: 'order',
        nextOrder: function nextOrder() {
            if (!this.length) return 1;
            return this.last().get('order') + 1;
        },
        isEmpty: function isEmpty() {
            return this.length === 0 || this.every(function (m) {
                return m.isEmpty();
            });
        }
    });
    return ChapterCollection;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ }),

/***/ "./cms/static/js/collections/textbook.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(2), __webpack_require__("./cms/static/js/models/textbook.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function (Backbone, TextbookModel) {
    var TextbookCollection = Backbone.Collection.extend({
        model: TextbookModel,
        url: function url() {
            return CMS.URL.TEXTBOOKS;
        }
    });
    return TextbookCollection;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ }),

/***/ "./cms/static/js/factories/base.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;// We can't convert this to an es6 module until all factories that use it have been converted out
// of RequireJS
!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__("./cms/static/js/base.js"), __webpack_require__("./cms/static/cms/js/main.js"), __webpack_require__("./common/static/js/src/logger.js"), __webpack_require__("./common/static/js/vendor/timepicker/datepair.js"), __webpack_require__("./common/static/js/src/accessibility_tools.js"), __webpack_require__("./common/static/js/src/ie_shim.js"), __webpack_require__("./common/static/js/src/tooltip_manager.js"), __webpack_require__("./common/static/js/src/lang_edx.js"), __webpack_require__("./cms/static/js/models/course.js"), __webpack_require__("./common/static/js/src/jquery_extend_patch.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function () {
    'use strict';
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ }),

/***/ "./cms/static/js/factories/textbooks.js":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
Object.defineProperty(__webpack_exports__, "__esModule", { value: true });
/* WEBPACK VAR INJECTION */(function($) {/* harmony export (immutable) */ __webpack_exports__["default"] = TextbooksFactory;
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "TextbooksFactory", function() { return TextbooksFactory; });
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0_gettext__ = __webpack_require__(3);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0_gettext___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_0_gettext__);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1_js_models_section__ = __webpack_require__("./cms/static/js/models/section.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1_js_models_section___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_1_js_models_section__);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_2_js_collections_textbook__ = __webpack_require__("./cms/static/js/collections/textbook.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_2_js_collections_textbook___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_2_js_collections_textbook__);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_3_js_views_list_textbooks__ = __webpack_require__("./cms/static/js/views/list_textbooks.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_3_js_views_list_textbooks___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_3_js_views_list_textbooks__);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_4__base__ = __webpack_require__("./cms/static/js/factories/base.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_4__base___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_4__base__);






'use strict';
function TextbooksFactory(textbooksJson) {
    var textbooks = new __WEBPACK_IMPORTED_MODULE_2_js_collections_textbook__(textbooksJson, { parse: true }),
        tbView = new __WEBPACK_IMPORTED_MODULE_3_js_views_list_textbooks__({ collection: textbooks });

    $('.content-primary').append(tbView.render().el);
    $('.nav-actions .new-button').click(function (event) {
        tbView.addOne(event);
    });
    $(window).on('beforeunload', function () {
        var dirty = textbooks.find(function (textbook) {
            return textbook.isDirty();
        });
        if (dirty) {
            return __WEBPACK_IMPORTED_MODULE_0_gettext__('You have unsaved changes. Do you really want to leave this page?');
        }
    });
};


/* WEBPACK VAR INJECTION */}.call(__webpack_exports__, __webpack_require__(0)))

/***/ }),

/***/ "./cms/static/js/models/chapter.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(2), __webpack_require__(3), __webpack_require__("./node_modules/backbone-associations/backbone-associations-min.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function (Backbone, gettext) {
    var Chapter = Backbone.AssociatedModel.extend({
        defaults: function defaults() {
            return {
                name: '',
                asset_path: '',
                order: this.collection ? this.collection.nextOrder() : 1
            };
        },
        isEmpty: function isEmpty() {
            return !this.get('name') && !this.get('asset_path');
        },
        parse: function parse(response) {
            if ('title' in response && !('name' in response)) {
                response.name = response.title;
                delete response.title;
            }
            if ('url' in response && !('asset_path' in response)) {
                response.asset_path = response.url;
                delete response.url;
            }
            return response;
        },
        toJSON: function toJSON() {
            return {
                title: this.get('name'),
                url: this.get('asset_path')
            };
        },
        // NOTE: validation functions should return non-internationalized error
        // messages. The messages will be passed through gettext in the template.
        validate: function validate(attrs, options) {
            if (!attrs.name && !attrs.asset_path) {
                return {
                    message: gettext('Chapter name and asset_path are both required'),
                    attributes: { name: true, asset_path: true }
                };
            } else if (!attrs.name) {
                return {
                    message: gettext('Chapter name is required'),
                    attributes: { name: true }
                };
            } else if (!attrs.asset_path) {
                return {
                    message: gettext('asset_path is required'),
                    attributes: { asset_path: true }
                };
            }
        }
    });
    return Chapter;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

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

/***/ }),

/***/ "./cms/static/js/models/section.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(2), __webpack_require__(3), __webpack_require__("./common/static/common/js/components/views/feedback_notification.js"), __webpack_require__("./cms/static/js/utils/module.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function (Backbone, gettext, NotificationView, ModuleUtils) {
    var Section = Backbone.Model.extend({
        defaults: {
            name: ''
        },
        validate: function validate(attrs, options) {
            if (!attrs.name) {
                return gettext('You must specify a name');
            }
        },
        urlRoot: ModuleUtils.urlRoot,
        toJSON: function toJSON() {
            return {
                metadata: {
                    display_name: this.get('name')
                }
            };
        },
        initialize: function initialize() {
            this.listenTo(this, 'request', this.showNotification);
            this.listenTo(this, 'sync', this.hideNotification);
        },
        showNotification: function showNotification() {
            if (!this.msg) {
                this.msg = new NotificationView.Mini({
                    title: gettext('Saving')
                });
            }
            this.msg.show();
        },
        hideNotification: function hideNotification() {
            if (!this.msg) {
                return;
            }
            this.msg.hide();
        }
    });
    return Section;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ }),

/***/ "./cms/static/js/models/textbook.js":
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function($) {var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(2), __webpack_require__(1), __webpack_require__(3), __webpack_require__("./cms/static/js/models/chapter.js"), __webpack_require__("./cms/static/js/collections/chapter.js"), __webpack_require__("./node_modules/backbone-associations/backbone-associations-min.js"), __webpack_require__("./cms/static/cms/js/main.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function (Backbone, _, gettext, ChapterModel, ChapterCollection) {
    var Textbook = Backbone.AssociatedModel.extend({
        defaults: function defaults() {
            return {
                name: '',
                chapters: new ChapterCollection([{}]),
                showChapters: false,
                editing: false
            };
        },
        relations: [{
            type: Backbone.Many,
            key: 'chapters',
            relatedModel: ChapterModel,
            collectionType: ChapterCollection
        }],
        initialize: function initialize() {
            this.setOriginalAttributes();
            return this;
        },
        setOriginalAttributes: function setOriginalAttributes() {
            this._originalAttributes = this.parse(this.toJSON());
        },
        reset: function reset() {
            this.set(this._originalAttributes, { parse: true });
        },
        isDirty: function isDirty() {
            return !_.isEqual(this._originalAttributes, this.parse(this.toJSON()));
        },
        isEmpty: function isEmpty() {
            return !this.get('name') && this.get('chapters').isEmpty();
        },
        urlRoot: function urlRoot() {
            return CMS.URL.TEXTBOOKS;
        },
        parse: function parse(response) {
            var ret = $.extend(true, {}, response);
            if ('tab_title' in ret && !('name' in ret)) {
                ret.name = ret.tab_title;
                delete ret.tab_title;
            }
            if ('url' in ret && !('chapters' in ret)) {
                ret.chapters = { url: ret.url };
                delete ret.url;
            }
            _.each(ret.chapters, function (chapter, i) {
                chapter.order = chapter.order || i + 1;
            });
            return ret;
        },
        toJSON: function toJSON() {
            return {
                tab_title: this.get('name'),
                chapters: this.get('chapters').toJSON()
            };
        },
        // NOTE: validation functions should return non-internationalized error
        // messages. The messages will be passed through gettext in the template.
        validate: function validate(attrs, options) {
            if (!attrs.name) {
                return {
                    message: gettext('Textbook name is required'),
                    attributes: { name: true }
                };
            }
            if (attrs.chapters.length === 0) {
                return {
                    message: gettext('Please add at least one chapter'),
                    attributes: { chapters: true }
                };
            } else {
                // validate all chapters
                var invalidChapters = [];
                attrs.chapters.each(function (chapter) {
                    if (!chapter.isValid()) {
                        invalidChapters.push(chapter);
                    }
                });
                if (!_.isEmpty(invalidChapters)) {
                    return {
                        message: gettext('All chapters must have a name and asset'),
                        attributes: { chapters: invalidChapters }
                    };
                }
            }
        }
    });
    return Textbook;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));
/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(0)))

/***/ }),

/***/ "./cms/static/js/models/uploads.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(2), __webpack_require__(1), __webpack_require__(3)], __WEBPACK_AMD_DEFINE_RESULT__ = function (Backbone, _, gettext) {
    var FileUpload = Backbone.Model.extend({
        defaults: {
            title: '',
            message: '',
            selectedFile: null,
            uploading: false,
            uploadedBytes: 0,
            totalBytes: 0,
            finished: false,
            mimeTypes: [],
            fileFormats: []
        },
        validate: function validate(attrs, options) {
            if (attrs.selectedFile && !this.checkTypeValidity(attrs.selectedFile)) {
                return {
                    message: _.template(gettext('Only <%- fileTypes %> files can be uploaded. Please select a file ending in <%- (fileExtensions) %> to upload.'))( // eslint-disable-line max-len
                    this.formatValidTypes()),
                    attributes: { selectedFile: true }
                };
            }
        },
        // Return a list of this uploader's valid file types
        fileTypes: function fileTypes() {
            var mimeTypes = _.map(this.attributes.mimeTypes, function (type) {
                return type.split('/')[1].toUpperCase();
            }),
                fileFormats = _.map(this.attributes.fileFormats, function (type) {
                return type.toUpperCase();
            });

            return mimeTypes.concat(fileFormats);
        },
        checkTypeValidity: function checkTypeValidity(file) {
            var attrs = this.attributes,
                getRegExp = function getRegExp(formats) {
                // Creates regular expression like: /(?:.+)\.(jpg|png|gif)$/i
                return RegExp('(?:.+)\\.(' + formats.join('|') + ')$', 'i');
            };

            return attrs.mimeTypes.length === 0 && attrs.fileFormats.length === 0 || _.contains(attrs.mimeTypes, file.type) || getRegExp(attrs.fileFormats).test(file.name);
        },
        // Return strings for the valid file types and extensions this
        // uploader accepts, formatted as natural language
        formatValidTypes: function formatValidTypes() {
            var attrs = this.attributes;

            if (attrs.mimeTypes.concat(attrs.fileFormats).length === 1) {
                return {
                    fileTypes: this.fileTypes()[0],
                    fileExtensions: '.' + this.fileTypes()[0].toLowerCase()
                };
            }
            var or = gettext('or');
            var formatTypes = function formatTypes(types) {
                return _.template('<%- initial %> <%- or %> <%- last %>')({
                    initial: _.initial(types).join(', '),
                    or: or,
                    last: _.last(types)
                });
            };
            return {
                fileTypes: formatTypes(this.fileTypes()),
                fileExtensions: formatTypes(_.map(this.fileTypes(), function (type) {
                    return '.' + type.toLowerCase();
                }))
            };
        }
    });

    return FileUpload;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__)); // end define()

/***/ }),

/***/ "./cms/static/js/utils/change_on_enter.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(0)], __WEBPACK_AMD_DEFINE_RESULT__ = function ($) {
    // Trigger "Change" event on "Enter" keyup event
    var triggerChangeEventOnEnter = function triggerChangeEventOnEnter(e) {
        if (e.which == 13) {
            $(this).trigger('change').blur();
        }
    };

    return triggerChangeEventOnEnter;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ }),

/***/ "./cms/static/js/utils/date_utils.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(0), __webpack_require__("./common/static/js/vendor/date.js"), __webpack_require__("./cms/static/js/utils/change_on_enter.js"), __webpack_require__("./common/static/js/vendor/jquery-ui.min.js"), __webpack_require__("./common/static/js/vendor/timepicker/jquery.timepicker.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function ($, date, TriggerChangeEventOnEnter) {
    'use strict';

    function getDate(datepickerInput, timepickerInput) {
        // given a pair of inputs (datepicker and timepicker), return a JS Date
        // object that corresponds to the datetime.js that they represent. Assume
        // UTC timezone, NOT the timezone of the user's browser.
        var selectedDate = null,
            selectedTime = null;
        if (datepickerInput.length > 0) {
            selectedDate = $(datepickerInput).datepicker('getDate');
        }
        if (timepickerInput.length > 0) {
            selectedTime = $(timepickerInput).timepicker('getTime');
        }
        if (selectedDate && selectedTime) {
            return new Date(Date.UTC(selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate(), selectedTime.getHours(), selectedTime.getMinutes()));
        } else if (selectedDate) {
            return new Date(Date.UTC(selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate()));
        } else {
            return null;
        }
    }

    function setDate(datepickerInput, timepickerInput, datetime) {
        // given a pair of inputs (datepicker and timepicker) and the date as an
        // ISO-formatted date string.
        var parsedDatetime = Date.parse(datetime);
        if (parsedDatetime) {
            $(datepickerInput).datepicker('setDate', parsedDatetime);
            if (timepickerInput.length > 0) {
                $(timepickerInput).timepicker('setTime', parsedDatetime);
            }
        }
    }

    function renderDate(dateArg) {
        // Render a localized date from an argument that can be passed to
        // the Date constructor (e.g. another Date or an ISO 8601 string)
        var dateObj = new Date(dateArg);
        return dateObj.toLocaleString([], { timeZone: 'UTC', timeZoneName: 'short' });
    }

    function parseDateFromString(stringDate) {
        if (stringDate && typeof stringDate === 'string') {
            return new Date(stringDate);
        } else {
            return stringDate;
        }
    }

    function convertDateStringsToObjects(obj, dateFields) {
        var i;
        for (i = 0; i < dateFields.length; i++) {
            if (obj[dateFields[i]]) {
                obj[dateFields[i]] = parseDateFromString(obj[dateFields[i]]);
            }
        }
        return obj;
    }

    function setupDatePicker(fieldName, view, index) {
        var cacheModel;
        var div;
        var datefield;
        var timefield;
        var cacheview;
        var setfield;
        var currentDate;
        if (typeof index !== 'undefined' && view.hasOwnProperty('collection')) {
            cacheModel = view.collection.models[index];
            div = view.$el.find('#' + view.collectionSelector(cacheModel.cid));
        } else {
            cacheModel = view.model;
            div = view.$el.find('#' + view.fieldToSelectorMap[fieldName]);
        }
        datefield = $(div).find('input.date');
        timefield = $(div).find('input.time');
        cacheview = view;
        setfield = function setfield(event) {
            var newVal = getDate(datefield, timefield);

            // Setting to null clears the time as well, as date and time are linked.
            // Note also that the validation logic prevents us from clearing the start date
            // (start date is required by the back end).
            cacheview.clearValidationErrors();
            cacheview.setAndValidate(fieldName, newVal || null, event);
        };

        // instrument as date and time pickers
        timefield.timepicker({ timeFormat: 'H:i' });
        datefield.datepicker();

        // Using the change event causes setfield to be triggered twice, but it is necessary
        // to pick up when the date is typed directly in the field.
        datefield.change(setfield).keyup(TriggerChangeEventOnEnter);
        timefield.on('changeTime', setfield);
        timefield.on('input', setfield);

        currentDate = null;
        if (cacheModel) {
            currentDate = cacheModel.get(fieldName);
        }
        // timepicker doesn't let us set null, so check that we have a time
        if (currentDate) {
            setDate(datefield, timefield, currentDate);
        } else {
            // but reset fields either way
            timefield.val('');
            datefield.val('');
        }
    }

    return {
        getDate: getDate,
        setDate: setDate,
        renderDate: renderDate,
        convertDateStringsToObjects: convertDateStringsToObjects,
        parseDateFromString: parseDateFromString,
        setupDatePicker: setupDatePicker
    };
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

/***/ "./cms/static/js/utils/module.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;/**
 * Utilities for modules/xblocks.
 *
 * Returns:
 *
 * urlRoot: the root for creating/updating an xblock.
 * getUpdateUrl: a utility method that returns the xblock update URL, appending
 *               the location if passed in.
 */
!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(1)], __WEBPACK_AMD_DEFINE_RESULT__ = function (_) {
    var urlRoot = '/xblock';

    var getUpdateUrl = function getUpdateUrl(locator) {
        if (_.isUndefined(locator)) {
            return urlRoot + '/';
        } else {
            return urlRoot + '/' + locator;
        }
    };
    return {
        urlRoot: urlRoot,
        getUpdateUrl: getUpdateUrl
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

/***/ "./cms/static/js/views/edit_chapter.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;/* global course */

!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(1), __webpack_require__(0), __webpack_require__(3), __webpack_require__("./node_modules/edx-ui-toolkit/src/js/utils/html-utils.js"), __webpack_require__("./cms/static/js/views/baseview.js"), __webpack_require__("./cms/static/js/models/uploads.js"), __webpack_require__("./cms/static/js/views/uploads.js"), __webpack_require__("./cms/templates/js/edit-chapter.underscore")], __WEBPACK_AMD_DEFINE_RESULT__ = function (_, $, gettext, HtmlUtils, BaseView, FileUploadModel, UploadDialogView, editChapterTemplate) {
    'use strict';

    var EditChapter = BaseView.extend({
        initialize: function initialize() {
            this.template = HtmlUtils.template(editChapterTemplate);
            this.listenTo(this.model, 'change', this.render);
        },
        tagName: 'li',
        className: function className() {
            return 'field-group chapter chapter' + this.model.get('order');
        },
        render: function render() {
            HtmlUtils.setHtml(this.$el, this.template({
                name: this.model.get('name'),
                asset_path: this.model.get('asset_path'),
                order: this.model.get('order'),
                error: this.model.validationError
            }));
            return this;
        },
        events: {
            'change .chapter-name': 'changeName',
            'change .chapter-asset-path': 'changeAssetPath',
            'click .action-close': 'removeChapter',
            'click .action-upload': 'openUploadDialog',
            submit: 'uploadAsset'
        },
        changeName: function changeName(e) {
            if (e && e.preventDefault) {
                e.preventDefault();
            }
            this.model.set({
                name: this.$('.chapter-name').val()
            }, { silent: true });
            return this;
        },
        changeAssetPath: function changeAssetPath(e) {
            if (e && e.preventDefault) {
                e.preventDefault();
            }
            this.model.set({
                asset_path: this.$('.chapter-asset-path').val()
            }, { silent: true });
            return this;
        },
        removeChapter: function removeChapter(e) {
            if (e && e.preventDefault) {
                e.preventDefault();
            }
            this.model.collection.remove(this.model);
            return this.remove();
        },
        openUploadDialog: function openUploadDialog(e) {
            if (e && e.preventDefault) {
                e.preventDefault();
            }
            this.model.set({
                name: this.$('input.chapter-name').val(),
                asset_path: this.$('input.chapter-asset-path').val()
            });
            var msg = new FileUploadModel({
                title: _.template(gettext('Upload a new PDF to “<%- name %>”'))({ name: course.get('name') }),
                message: gettext('Please select a PDF file to upload.'),
                mimeTypes: ['application/pdf']
            });
            var that = this;
            var view = new UploadDialogView({
                model: msg,
                onSuccess: function onSuccess(response) {
                    var options = {};
                    if (!that.model.get('name')) {
                        options.name = response.asset.displayname;
                    }
                    options.asset_path = response.asset.portable_url;
                    that.model.set(options);
                }
            });
            view.show();
        }
    });

    return EditChapter;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ }),

/***/ "./cms/static/js/views/edit_textbook.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__("./cms/static/js/views/baseview.js"), __webpack_require__(1), __webpack_require__(0), __webpack_require__("./cms/static/js/views/edit_chapter.js"), __webpack_require__("./common/static/common/js/components/views/feedback_notification.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function (BaseView, _, $, EditChapterView, NotificationView) {
    var EditTextbook = BaseView.extend({
        initialize: function initialize() {
            this.template = this.loadTemplate('edit-textbook');
            this.listenTo(this.model, 'invalid', this.render);
            var chapters = this.model.get('chapters');
            this.listenTo(chapters, 'add', this.addOne);
            this.listenTo(chapters, 'reset', this.addAll);
        },
        tagName: 'section',
        className: 'textbook',
        render: function render() {
            this.$el.html(this.template({ // xss-lint: disable=javascript-jquery-html
                name: this.model.get('name'),
                error: this.model.validationError
            }));
            this.addAll();
            return this;
        },
        events: {
            'change input[name=textbook-name]': 'setName',
            submit: 'setAndClose',
            'click .action-cancel': 'cancel',
            'click .action-add-chapter': 'createChapter'
        },
        addOne: function addOne(chapter) {
            var view = new EditChapterView({ model: chapter });
            this.$('ol.chapters').append(view.render().el);
            return this;
        },
        addAll: function addAll() {
            this.model.get('chapters').each(this.addOne, this);
        },
        createChapter: function createChapter(e) {
            if (e && e.preventDefault) {
                e.preventDefault();
            }
            this.setValues();
            this.model.get('chapters').add([{}]);
        },
        setName: function setName(e) {
            if (e && e.preventDefault) {
                e.preventDefault();
            }
            this.model.set('name', this.$('#textbook-name-input').val(), { silent: true });
        },
        setValues: function setValues() {
            this.setName();
            var that = this;
            _.each(this.$('li'), function (li, i) {
                var chapter = that.model.get('chapters').at(i);
                if (!chapter) {
                    return;
                }
                chapter.set({
                    name: $('.chapter-name', li).val(),
                    asset_path: $('.chapter-asset-path', li).val()
                });
            });
            return this;
        },
        setAndClose: function setAndClose(e) {
            if (e && e.preventDefault) {
                e.preventDefault();
            }
            this.setValues();
            if (!this.model.isValid()) {
                return;
            }
            var saving = new NotificationView.Mini({
                title: gettext('Saving')
            }).show();
            var that = this;
            this.model.save({}, {
                success: function success() {
                    that.model.setOriginalAttributes();
                    that.close();
                },
                complete: function complete() {
                    saving.hide();
                }
            });
        },
        cancel: function cancel(e) {
            if (e && e.preventDefault) {
                e.preventDefault();
            }
            this.model.reset();
            return this.close();
        },
        close: function close() {
            var textbooks = this.model.collection;
            this.remove();
            if (this.model.isNew()) {
                // if the textbook has never been saved, remove it
                textbooks.remove(this.model);
            }
            // don't forget to tell the model that it's no longer being edited
            this.model.set('editing', false);
            return this;
        }
    });
    return EditTextbook;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ }),

/***/ "./cms/static/js/views/list_textbooks.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__("./cms/static/js/views/baseview.js"), __webpack_require__(0), __webpack_require__("./cms/static/js/views/edit_textbook.js"), __webpack_require__("./cms/static/js/views/show_textbook.js"), __webpack_require__("./common/static/common/js/components/utils/view_utils.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function (BaseView, $, EditTextbookView, ShowTextbookView, ViewUtils) {
    var ListTextbooks = BaseView.extend({
        initialize: function initialize() {
            this.emptyTemplate = this.loadTemplate('no-textbooks');
            this.listenTo(this.collection, 'change:editing', this.render);
            this.listenTo(this.collection, 'destroy', this.handleDestroy);
        },
        tagName: 'div',
        className: 'textbooks-list',
        render: function render() {
            var textbooks = this.collection;
            if (textbooks.length === 0) {
                this.$el.html(this.emptyTemplate()); // xss-lint: disable=javascript-jquery-html
            } else {
                this.$el.empty();
                var that = this;
                textbooks.each(function (textbook) {
                    var view;
                    if (textbook.get('editing')) {
                        view = new EditTextbookView({ model: textbook });
                    } else {
                        view = new ShowTextbookView({ model: textbook });
                    }
                    that.$el.append(view.render().el);
                });
            }
            return this;
        },
        events: {
            'click .new-button': 'addOne'
        },
        addOne: function addOne(e) {
            var $sectionEl, $inputEl;
            if (e && e.preventDefault) {
                e.preventDefault();
            }
            this.collection.add([{ editing: true }]); // (render() call triggered here)
            this.render();
            // find the outer 'section' tag for the newly added textbook
            $sectionEl = this.$el.find('section:last');
            // scroll to put this at top of viewport
            ViewUtils.setScrollOffset($sectionEl, 0);
            // find the first input element in this section
            $inputEl = $sectionEl.find('input:first');
            // activate the text box (so user can go ahead and start typing straight away)
            $inputEl.focus().select();
        },
        handleDestroy: function handleDestroy(model, collection, options) {
            collection.remove(model);
        }
    });
    return ListTextbooks;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ }),

/***/ "./cms/static/js/views/modals/base_modal.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;/**
 * This is a base modal implementation that provides common utilities.
 *
 * A modal implementation should override the following methods:
 *
 *   getTitle():
 *     returns the title for the modal.
 *   getContentHtml():
 *     returns the HTML content to be shown inside the modal.
 *
 * A modal implementation should also provide the following options:
 *
 *   modalName: A string identifying the modal.
 *   modalType: A string identifying the type of the modal.
 *   modalSize: A string, either 'sm', 'med', or 'lg' indicating the
 *     size of the modal.
 *   viewSpecificClasses: A string of CSS classes to be attached to
 *     the modal window.
 *   addPrimaryActionButton: A boolean indicating whether to include a primary action
 *     button on the modal.
 *   primaryActionButtonType: A string to be used as type for primary action button.
 *   primaryActionButtonTitle: A string to be used as title for primary action button.
 *   showEditorModeButtons: Whether to show editor mode button in the modal header.
 */
!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(0), __webpack_require__(1), __webpack_require__(3), __webpack_require__("./cms/static/js/views/baseview.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function ($, _, gettext, BaseView) {
    var BaseModal = BaseView.extend({
        events: {
            'click .action-cancel': 'cancel'
        },

        options: _.extend({}, BaseView.prototype.options, {
            type: 'prompt',
            closeIcon: false,
            icon: false,
            modalName: 'basic',
            modalType: 'generic',
            modalSize: 'lg',
            title: '',
            modalWindowClass: '.modal-window',
            // A list of class names, separated by space.
            viewSpecificClasses: '',
            addPrimaryActionButton: false,
            primaryActionButtonType: 'save',
            primaryActionButtonTitle: gettext('Save'),
            showEditorModeButtons: true
        }),

        initialize: function initialize() {
            var parent = this.options.parent,
                parentElement = this.options.parentElement;
            this.modalTemplate = this.loadTemplate('basic-modal');
            this.buttonTemplate = this.loadTemplate('modal-button');
            if (parent) {
                parentElement = parent.$el;
            } else if (!parentElement) {
                parentElement = this.$el.closest(this.options.modalWindowClass);
                if (parentElement.length === 0) {
                    parentElement = $('body');
                }
            }
            this.parentElement = parentElement;
        },

        render: function render() {
            // xss-lint: disable=javascript-jquery-html
            this.$el.html(this.modalTemplate({
                name: this.options.modalName,
                type: this.options.modalType,
                size: this.options.modalSize,
                title: this.getTitle(),
                modalSRTitle: this.options.modalSRTitle,
                showEditorModeButtons: this.options.showEditorModeButtons,
                viewSpecificClasses: this.options.viewSpecificClasses
            }));
            this.addActionButtons();
            this.renderContents();
            this.parentElement.append(this.$el);
        },

        getTitle: function getTitle() {
            return this.options.title;
        },

        renderContents: function renderContents() {
            var contentHtml = this.getContentHtml();
            // xss-lint: disable=javascript-jquery-html
            this.$('.modal-content').html(contentHtml);
        },

        /**
         * Returns the content to be shown in the modal.
         */
        getContentHtml: function getContentHtml() {
            return '';
        },

        show: function show(focusModal) {
            var focusModalWindow = focusModal === undefined;
            this.render();
            this.resize();
            $(window).resize(_.bind(this.resize, this));

            // child may want to have its own focus management
            if (focusModalWindow) {
                // after showing and resizing, send focus
                this.$el.find(this.options.modalWindowClass).focus();
            }
        },

        hide: function hide() {
            // Completely remove the modal from the DOM
            this.undelegateEvents();
            this.$el.html('');
        },

        cancel: function cancel(event) {
            if (event) {
                event.preventDefault();
                event.stopPropagation(); // Make sure parent modals don't see the click
            }
            this.hide();
        },

        /**
         * Adds the action buttons to the modal.
         */
        addActionButtons: function addActionButtons() {
            if (this.options.addPrimaryActionButton) {
                this.addActionButton(this.options.primaryActionButtonType, this.options.primaryActionButtonTitle, true);
            }
            this.addActionButton('cancel', gettext('Cancel'));
        },

        /**
         * Adds a new action button to the modal.
         * @param type The type of the action.
         * @param name The action's name.
         * @param isPrimary True if this button is the primary one.
         */
        addActionButton: function addActionButton(type, name, isPrimary) {
            var html = this.buttonTemplate({
                type: type,
                name: name,
                isPrimary: isPrimary
            });
            // xss-lint: disable=javascript-jquery-append
            this.getActionBar().find('ul').append(html);
        },

        /**
         * Returns the action bar that contains the modal's action buttons.
         */
        getActionBar: function getActionBar() {
            return this.$(this.options.modalWindowClass + ' > div > .modal-actions');
        },

        /**
         * Returns the action button of the specified type.
         */
        getActionButton: function getActionButton(type) {
            return this.getActionBar().find('.action-' + type);
        },

        enableActionButton: function enableActionButton(type) {
            this.getActionBar().find('.action-' + type).prop('disabled', false).removeClass('is-disabled');
        },

        disableActionButton: function disableActionButton(type) {
            this.getActionBar().find('.action-' + type).prop('disabled', true).addClass('is-disabled');
        },

        resize: function resize() {
            var top, left, modalWindow, modalWidth, modalHeight, availableWidth, availableHeight, maxWidth, maxHeight;

            modalWindow = this.$el.find(this.options.modalWindowClass);
            availableWidth = $(window).width();
            availableHeight = $(window).height();
            maxWidth = availableWidth * 0.98;
            maxHeight = availableHeight * 0.98;
            modalWidth = Math.min(modalWindow.outerWidth(), maxWidth);
            modalHeight = Math.min(modalWindow.outerHeight(), maxHeight);

            left = (availableWidth - modalWidth) / 2;
            top = (availableHeight - modalHeight) / 2;

            modalWindow.css({
                top: top + $(window).scrollTop(),
                left: left + $(window).scrollLeft()
            });
        }
    });

    return BaseModal;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ }),

/***/ "./cms/static/js/views/show_textbook.js":
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function($) {var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__("./cms/static/js/views/baseview.js"), __webpack_require__(1), __webpack_require__(3), __webpack_require__("./common/static/common/js/components/views/feedback_notification.js"), __webpack_require__("./common/static/common/js/components/views/feedback_prompt.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function (BaseView, _, gettext, NotificationView, PromptView) {
    var ShowTextbook = BaseView.extend({
        initialize: function initialize() {
            this.template = _.template($('#show-textbook-tpl').text());
            this.listenTo(this.model, 'change', this.render);
            this.listenTo(this.model, 'destroy', this.remove);
        },
        tagName: 'section',
        className: 'textbook',
        events: {
            'click .edit': 'editTextbook',
            'click .delete': 'confirmDelete',
            'click .show-chapters': 'showChapters',
            'click .hide-chapters': 'hideChapters'
        },
        render: function render() {
            var attrs = $.extend({}, this.model.attributes);
            attrs.bookindex = this.model.collection.indexOf(this.model);
            attrs.course = window.course.attributes;
            this.$el.html(this.template(attrs)); // xss-lint: disable=javascript-jquery-html
            return this;
        },
        editTextbook: function editTextbook(e) {
            if (e && e.preventDefault) {
                e.preventDefault();
            }
            this.model.set('editing', true);
        },
        confirmDelete: function confirmDelete(e) {
            if (e && e.preventDefault) {
                e.preventDefault();
            }
            var textbook = this.model;
            new PromptView.Warning({
                title: _.template(gettext('Delete “<%- name %>”?'))({ name: textbook.get('name') }),
                message: gettext("Deleting a textbook cannot be undone and once deleted any reference to it in your courseware's navigation will also be removed."),
                actions: {
                    primary: {
                        text: gettext('Delete'),
                        click: function click(view) {
                            view.hide();
                            var delmsg = new NotificationView.Mini({
                                title: gettext('Deleting')
                            }).show();
                            textbook.destroy({
                                complete: function complete() {
                                    delmsg.hide();
                                }
                            });
                        }
                    },
                    secondary: {
                        text: gettext('Cancel'),
                        click: function click(view) {
                            view.hide();
                        }
                    }
                }
            }).show();
        },
        showChapters: function showChapters(e) {
            if (e && e.preventDefault) {
                e.preventDefault();
            }
            this.model.set('showChapters', true);
        },
        hideChapters: function hideChapters(e) {
            if (e && e.preventDefault) {
                e.preventDefault();
            }
            this.model.set('showChapters', false);
        }
    });
    return ShowTextbook;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));
/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(0)))

/***/ }),

/***/ "./cms/static/js/views/uploads.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(0), __webpack_require__(1), __webpack_require__(3), __webpack_require__("./cms/static/js/views/modals/base_modal.js"), __webpack_require__("./node_modules/edx-ui-toolkit/src/js/utils/html-utils.js"), __webpack_require__("./common/static/js/vendor/jquery.form.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function ($, _, gettext, BaseModal, HtmlUtils) {
    'use strict';

    var UploadDialog = BaseModal.extend({
        events: _.extend({}, BaseModal.prototype.events, {
            'change input[type=file]': 'selectFile',
            'click .action-upload': 'upload'
        }),

        options: $.extend({}, BaseModal.prototype.options, {
            modalName: 'assetupload',
            modalSize: 'med',
            successMessageTimeout: 2000, // 2 seconds
            viewSpecificClasses: 'confirm'
        }),

        initialize: function initialize(options) {
            BaseModal.prototype.initialize.call(this);
            this.template = this.loadTemplate('upload-dialog');
            this.listenTo(this.model, 'change', this.renderContents);
            this.options.title = this.model.get('title');
            // `uploadData` can contain extra data that
            // can be POSTed along with the file.
            this.uploadData = _.extend({}, options.uploadData);
        },

        addActionButtons: function addActionButtons() {
            this.addActionButton('upload', gettext('Upload'), true);
            BaseModal.prototype.addActionButtons.call(this);
        },

        renderContents: function renderContents() {
            var isValid = this.model.isValid(),
                selectedFile = this.model.get('selectedFile'),
                oldInput = this.$('input[type=file]');
            BaseModal.prototype.renderContents.call(this);
            // Ideally, we'd like to tell the browser to pre-populate the
            // <input type="file"> with the selectedFile if we have one -- but
            // browser security prohibits that. So instead, we'll swap out the
            // new input (that has no file selected) with the old input (that
            // already has the selectedFile selected). However, we only want to do
            // this if the selected file is valid: if it isn't, we want to render
            // a blank input to prompt the user to upload a different (valid) file.
            if (selectedFile && isValid) {
                $(oldInput).removeClass('error');
                this.$('input[type=file]').replaceWith(HtmlUtils.HTML(oldInput).toString());
                this.$('.action-upload').removeClass('disabled');
            } else {
                this.$('.action-upload').addClass('disabled');
            }
            return this;
        },

        getContentHtml: function getContentHtml() {
            return this.template({
                url: this.options.url || CMS.URL.UPLOAD_ASSET,
                message: this.model.get('message'),
                selectedFile: this.model.get('selectedFile'),
                uploading: this.model.get('uploading'),
                uploadedBytes: this.model.get('uploadedBytes'),
                totalBytes: this.model.get('totalBytes'),
                finished: this.model.get('finished'),
                error: this.model.validationError
            });
        },

        selectFile: function selectFile(e) {
            var selectedFile = e.target.files[0] || null;
            this.model.set({
                selectedFile: selectedFile
            });
            // This change event triggering necessary for FireFox, because the browser don't
            // consider change of File object (file input field) as a change in model.
            if (selectedFile && $.isEmptyObject(this.model.changed)) {
                this.model.trigger('change');
            }
        },

        upload: function upload(e) {
            var uploadAjaxData = _.extend({}, this.uploadData);
            // don't show the generic error notification; we're in a modal,
            // and we're better off modifying it instead.
            uploadAjaxData.notifyOnError = false;

            if (e && e.preventDefault) {
                e.preventDefault();
            }
            this.model.set('uploading', true);
            this.$('form').ajaxSubmit({
                success: _.bind(this.success, this),
                error: _.bind(this.error, this),
                uploadProgress: _.bind(this.progress, this),
                data: uploadAjaxData
            });
        },

        progress: function progress(event, position, total) {
            this.model.set({
                uploadedBytes: position,
                totalBytes: total
            });
        },

        success: function success(response, statusText, xhr, form) {
            this.model.set({
                uploading: false,
                finished: true
            });
            if (this.options.onSuccess) {
                this.options.onSuccess(response, statusText, xhr, form);
            }
            var that = this;
            this.removalTimeout = setTimeout(function () {
                that.hide();
            }, this.options.successMessageTimeout);
        },

        error: function error() {
            this.model.set({
                uploading: false,
                uploadedBytes: 0,
                title: gettext("We're sorry, there was an error")
            });
        }
    });
    return UploadDialog;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__)); // end define()

/***/ }),

/***/ "./cms/templates/js/edit-chapter.underscore":
/***/ (function(module, exports) {

module.exports = "<div class=\"input-wrap field text required field-add-chapter-name chapter<%- order %>-name\n    <% if (error && error.attributes && error.attributes.name) { print('error'); } %>\">\n  <label for=\"chapter<%- order %>-name\"><%- gettext(\"Chapter Name\") %></label>\n  <input id=\"chapter<%- order %>-name\" name=\"chapter<%- order %>-name\" class=\"chapter-name short\" placeholder=\"<%- StringUtils.interpolate(gettext(\"Chapter {order}\"), {order: order}) %>\" value=\"<%- name %>\" type=\"text\">\n  <span class=\"tip tip-stacked\"><%- gettext(\"provide the title/name of the chapter that will be used in navigating\") %></span>\n</div>\n<div class=\"input-wrap field text required field-add-chapter-asset chapter<%- order %>-asset\n    <% if (error && error.attributes && error.attributes.asset_path) { print('error'); } %>\">\n  <label for=\"chapter<%- order %>-asset-path\"><%- gettext(\"Chapter Asset\") %></label>\n  <input id=\"chapter<%- order %>-asset-path\" name=\"chapter<%- order %>-asset-path\" class=\"chapter-asset-path\" placeholder=\"<%- StringUtils.interpolate(gettext(\"path/to/introductionToCookieBaking-CH{order}.pdf\"), {order: order}) %>\" value=\"<%- asset_path %>\" type=\"text\" dir=\"ltr\">\n  <span class=\"tip tip-stacked\"><%- gettext(\"upload a PDF file or provide the path to a Studio asset file\") %></span>\n<button class=\"action action-upload\"><%- gettext(\"Upload PDF\") %></button>\n</div>\n<a href=\"\" class=\"action action-close\"><span class=\"icon fa fa-times-circle\" aria-hidden=\"true\"></span> <span class=\"sr\"><%- gettext(\"delete chapter\") %></span></a>\n"

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

/***/ "./common/static/js/src/accessibility_tools.js":
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function($, __webpack_provided_edx_dot_HtmlUtils) {/*

============================================
License for Application
============================================

This license is governed by United States copyright law, and with respect to matters
of tort, contract, and other causes of action it is governed by North Carolina law,
without regard to North Carolina choice of law provisions.  The forum for any dispute
resolution shall be in Wake County, North Carolina.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list
   of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this
   list of conditions and the following disclaimer in the documentation and/or other
   materials provided with the distribution.

3. The name of the author may not be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

*/

var $focusedElementBeforeModal,
    focusableElementsString = 'a[href], area[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled]), iframe, object, embed, *[tabindex], *[contenteditable]';

var reassignTabIndexesAndAriaHidden = function reassignTabIndexesAndAriaHidden(focusableElementsFilterString, closeButtonId, modalId, mainPageId) {
    // Sets appropriate elements to tab indexable and properly sets aria_hidden on content outside of modal
    // "focusableElementsFilterString" is a string that indicates all elements that should be focusable
    // "closeButtonId" is the selector for the button that closes out the modal.
    // "modalId" is the selector for the modal being managed
    // "mainPageId" is the selector for the main part of the page
    // Returns a list of focusableItems
    var focusableItems;

    $(mainPageId).attr('aria-hidden', 'true');
    $(modalId).attr('aria-hidden', 'false');

    focusableItems = $(modalId).find('*').filter(focusableElementsFilterString).filter(':visible');

    focusableItems.attr('tabindex', '2');
    $(closeButtonId).attr('tabindex', '1').focus();

    return focusableItems;
};

var trapTabFocus = function trapTabFocus(focusableItems, closeButtonId) {
    // Determines last element in modal and traps focus by causing tab
    // to focus on the first modal element (close button)
    // "focusableItems" all elements in the modal that are focusable
    // "closeButtonId" is the selector for the button that closes out the modal.
    // returns the last focusable element in the modal.
    var $last;
    if (focusableItems.length !== 0) {
        $last = focusableItems.last();
    } else {
        $last = $(closeButtonId);
    }

    // tab on last element in modal returns to the first one
    $last.on('keydown', function (e) {
        var keyCode = e.keyCode || e.which;
        // 9 is the js keycode for tab
        if (!e.shiftKey && keyCode === 9) {
            e.preventDefault();
            $(closeButtonId).focus();
        }
    });

    return $last;
};

var trapShiftTabFocus = function trapShiftTabFocus($last, closeButtonId) {
    $(closeButtonId).on('keydown', function (e) {
        var keyCode = e.keyCode || e.which;
        // 9 is the js keycode for tab
        if (e.shiftKey && keyCode === 9) {
            e.preventDefault();
            $last.focus();
        }
    });
};

var bindReturnFocusListener = function bindReturnFocusListener($previouslyFocusedElement, closeButtonId, modalId, mainPageId) {
    // Ensures that on modal close, focus is returned to the element
    // that had focus before the modal was opened.
    $('#lean_overlay, ' + closeButtonId).click(function () {
        $(mainPageId).attr('aria-hidden', 'false');
        $(modalId).attr('aria-hidden', 'true');
        $previouslyFocusedElement.focus();
    });
};

var bindEscapeKeyListener = function bindEscapeKeyListener(modalId, closeButtonId) {
    $(modalId).on('keydown', function (e) {
        var keyCode = e.keyCode || e.which;
        // 27 is the javascript keycode for the ESC key
        if (keyCode === 27) {
            e.preventDefault();
            $(closeButtonId).click();
        }
    });
};

var trapFocusForAccessibleModal = function trapFocusForAccessibleModal($previouslyFocusedElement, focusableElementsFilterString, closeButtonId, modalId, mainPageId) {
    // Re assess the page for which items internal to the modal should be focusable,
    // Should be called after the content of the accessible_modal is changed in order
    // to ensure that the correct elements are accessible.
    var focusableItems, $last;
    focusableItems = reassignTabIndexesAndAriaHidden(focusableElementsFilterString, closeButtonId, modalId, mainPageId);
    $last = trapTabFocus(focusableItems, closeButtonId);
    trapShiftTabFocus($last, closeButtonId);
    bindReturnFocusListener($previouslyFocusedElement, closeButtonId, modalId, mainPageId);
    bindEscapeKeyListener(modalId, closeButtonId);
};

var accessible_modal = function accessible_modal(trigger, closeButtonId, modalId, mainPageId) {
    // Modifies a lean modal to optimize focus management.
    // "trigger" is the selector for the link element that triggers the modal.
    // "closeButtonId" is the selector for the button that closes out the modal.
    // "modalId" is the selector for the modal being managed
    // "mainPageId" is the selector for the main part of the page
    //
    // based on http://accessibility.oit.ncsu.edu/training/aria/modal-window/modal-window.js
    //
    // see http://accessibility.oit.ncsu.edu/blog/2013/09/13/the-incredible-accessible-modal-dialog/
    // for more information on managing modals
    //
    var initialFocus;
    $(trigger).click(function () {
        $focusedElementBeforeModal = $(trigger);

        trapFocusForAccessibleModal($focusedElementBeforeModal, focusableElementsString, closeButtonId, modalId, mainPageId);

        // In IE, focus shifts to iframes when they load.
        // These lines ensure that focus is shifted back to the close button
        // in the case that a modal that contains an iframe is opened in IE.
        // see http://stackoverflow.com/questions/15792620/
        initialFocus = true;
        $(modalId).find('iframe').on('focus', function () {
            if (initialFocus) {
                $(closeButtonId).focus();
                initialFocus = false;
            }
        });
    });
};

// NOTE: This is a gross hack to make the skip links work for Webkit browsers
// see http://stackoverflow.com/questions/6280399/skip-links-not-working-in-chrome/12720183#12720183

// handle things properly for clicks
$('.nav-skip').click(function () {
    var href = $(this).attr('href');
    if (href) {
        $(href).attr('tabIndex', -1).focus();
    }
});
// and for the enter key
$('.nav-skip').keypress(function (e) {
    var href;
    if (e.which === 13) {
        href = $(this).attr('href');
        if (href) {
            $(href).attr('tabIndex', -1).focus();
        }
    }
});

// Creates a window level SR object that can be used for giving audible feedback to screen readers.
$(function () {
    var SRAlert;

    SRAlert = function () {
        function SRAlert() {
            // This initialization sometimes gets done twice, so take to only create a single reader-feedback div.
            var readerFeedbackID = 'reader-feedback',
                $readerFeedbackSelector = $('#' + readerFeedbackID);

            if ($readerFeedbackSelector.length === 0) {
                __webpack_provided_edx_dot_HtmlUtils.append($('body'), __webpack_provided_edx_dot_HtmlUtils.interpolateHtml(__webpack_provided_edx_dot_HtmlUtils.HTML('<div id="{readerFeedbackID}" class="sr" aria-live="polite"></div>'), { readerFeedbackID: readerFeedbackID }));
            }
            this.el = $('#' + readerFeedbackID);
        }

        SRAlert.prototype.clear = function () {
            __webpack_provided_edx_dot_HtmlUtils.setHtml(this.el, '');
        };

        SRAlert.prototype.readElts = function (elts) {
            var texts = [];
            $.each(elts, function (idx, value) {
                texts.push($(value).html());
            });
            return this.readTexts(texts);
        };

        SRAlert.prototype.readText = function (text) {
            return this.readTexts([text]);
        };

        SRAlert.prototype.readTexts = function (texts) {
            var htmlFeedback = __webpack_provided_edx_dot_HtmlUtils.HTML('');
            $.each(texts, function (idx, value) {
                htmlFeedback = __webpack_provided_edx_dot_HtmlUtils.interpolateHtml(__webpack_provided_edx_dot_HtmlUtils.HTML('{previous_feedback}<p>{value}</p>\n'),
                // "value" may be HTML, if an element is being passed
                { previous_feedback: htmlFeedback, value: __webpack_provided_edx_dot_HtmlUtils.HTML(value) });
            });
            __webpack_provided_edx_dot_HtmlUtils.setHtml(this.el, htmlFeedback);
        };

        return SRAlert;
    }();

    window.SR = new SRAlert();
});
/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(0), __webpack_require__("./node_modules/edx-ui-toolkit/src/js/utils/html-utils.js")))

/***/ }),

/***/ "./common/static/js/src/ajax_prefix.js":
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function($) {// Once generated by CoffeeScript 1.9.3, but now lives as pure JS
/* eslint-disable */
(function () {
  this.AjaxPrefix = {
    addAjaxPrefix: function addAjaxPrefix(jQuery, prefix) {
      jQuery.postWithPrefix = function (url, data, callback, type) {
        return $.post("" + prefix() + url, data, callback, type);
      };
      jQuery.getWithPrefix = function (url, data, callback, type) {
        return $.get("" + prefix() + url, data, callback, type);
      };
      return jQuery.ajaxWithPrefix = function (url, settings) {
        if (settings != null) {
          return $.ajax("" + prefix() + url, settings);
        } else {
          settings = url;
          settings.url = "" + prefix() + settings.url;
          return $.ajax(settings);
        }
      };
    }
  };
}).call(this);

/*** EXPORTS FROM exports-loader ***/
module.exports = this.AjaxPrefix;
/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(0)))

/***/ }),

/***/ "./common/static/js/src/ie_shim.js":
/***/ (function(module, exports) {

/*
 * This file is used for keeping compatibility with Internet Explorer.
 * As starting with IE10, the conditional comments are not supported, this file
 * will always be loaded whether the browser is IE or not. Therefore, the code
 * here should not make any assumption and should always detect the execution
 * conditions itself.
 */

// Shim name: Create the attribute of 'window.location.origin'
// IE version: 11 or earlier, 12 or later not tested
// Internet Explorer does not have built-in property 'window.location.origin',
// we need to create one here as some vendor code such as TinyMCE uses this.
if (!window.location.origin) {
  window.location.origin = window.location.protocol + '//' + window.location.hostname + (window.location.port ? ':' + window.location.port : '');
}

/***/ }),

/***/ "./common/static/js/src/jquery_extend_patch.js":
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(jQuery) {var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; };

/*

`extend` function of jquery (jQuery < 3.4.0) is known to have Prototype Pollution vulnerability.
This IIFE is used to rebind `extend` function with its patched implementation.

TODO: Remove this file and all its uses after upgrading to version >= 3.4.0

*/

(function () {

    jQuery.extend = jQuery.fn.extend = function () {
        var options,
            name,
            src,
            copy,
            copyIsArray,
            clone,
            target = arguments[0] || {},
            i = 1,
            length = arguments.length,
            deep = false;

        // Handle a deep copy situation
        if (typeof target === "boolean") {
            deep = target;

            // Skip the boolean and the target
            target = arguments[i] || {};
            i++;
        }

        // Handle case when target is a string or something (possible in deep copy)
        if ((typeof target === "undefined" ? "undefined" : _typeof(target)) !== "object" && !jQuery.isFunction(target)) {
            target = {};
        }

        // Extend jQuery itself if only one argument is passed
        if (i === length) {
            target = this;
            i--;
        }

        for (; i < length; i++) {

            // Only deal with non-null/undefined values
            if ((options = arguments[i]) != null) {

                // Extend the base object
                for (name in options) {
                    copy = options[name];

                    // Prevent Object.prototype pollution
                    // Prevent never-ending loop
                    if (name === "__proto__" || target === copy) {
                        continue;
                    }

                    // Recurse if we're merging plain objects or arrays
                    if (deep && copy && (jQuery.isPlainObject(copy) || (copyIsArray = Array.isArray(copy)))) {
                        src = target[name];

                        // Ensure proper type for the source value
                        if (copyIsArray && !Array.isArray(src)) {
                            clone = [];
                        } else if (!copyIsArray && !jQuery.isPlainObject(src)) {
                            clone = {};
                        } else {
                            clone = src;
                        }
                        copyIsArray = false;

                        // Never move original objects, clone them
                        target[name] = jQuery.extend(deep, clone, copy);

                        // Don't bring in undefined values
                    } else if (copy !== undefined) {
                        target[name] = copy;
                    }
                }
            }
        }

        // Return the modified object
        return target;
    };
})();
/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(0)))

/***/ }),

/***/ "./common/static/js/src/lang_edx.js":
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function($) {var Language = function () {
    'use strict';

    var $settings_language_selector,
        self = null;
    return {
        init: function init() {
            $settings_language_selector = $('#settings-language-value');
            self = this;
            this.listenForLanguagePreferenceChange();
        },

        /**
         * Listener on changing language from selector.
         * Send an ajax request to save user language preferences.
         */
        listenForLanguagePreferenceChange: function listenForLanguagePreferenceChange() {
            $settings_language_selector.change(function (event) {
                var language = this.value,
                    url = $('.url-endpoint').val(),
                    is_user_authenticated = JSON.parse($('.url-endpoint').data('user-is-authenticated'));
                event.preventDefault();
                self.submitAjaxRequest(language, url, function () {
                    if (is_user_authenticated) {
                        // User language preference has been set successfully
                        // Now submit the form in success callback.
                        $('#language-settings-form').submit();
                    } else {
                        self.refresh();
                    }
                });
            });
        },

        /**
         * Send an ajax request to set user language preferences.
         */
        submitAjaxRequest: function submitAjaxRequest(language, url, callback) {
            $.ajax({
                type: 'PATCH',
                data: JSON.stringify({ 'pref-lang': language }),
                url: url,
                dataType: 'json',
                contentType: 'application/merge-patch+json',
                notifyOnError: false,
                beforeSend: function beforeSend(xhr) {
                    xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
                }
            }).done(function () {
                callback();
            }).fail(function () {
                self.refresh();
            });
        },

        /**
         * refresh the page.
         */
        refresh: function refresh() {
            // reloading the page so we can get the latest state of released languages from model
            location.reload();
        }

    };
}();
$(document).ready(function () {
    'use strict';

    Language.init();
});
/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(0)))

/***/ }),

/***/ "./common/static/js/src/logger.js":
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function($) {/*** IMPORTS FROM imports-loader ***/
(function () {

    (function () {
        'use strict';

        var Logger = function () {
            // listeners[event_type][element] -> list of callbacks
            var listeners = {},
                sendRequest,
                has;

            sendRequest = function sendRequest(data, options) {
                var request = $.ajaxWithPrefix ? $.ajaxWithPrefix : $.ajax;

                options = $.extend(true, {
                    url: '/event',
                    type: 'POST',
                    data: data,
                    async: true
                }, options);
                return request(options);
            };

            has = function has(object, propertyName) {
                return {}.hasOwnProperty.call(object, propertyName);
            };

            return {
                /**
                 * Emits an event.
                 *
                 * Note that this method is used by external XBlocks, and the API cannot change without
                 * proper deprecation and notification for external authors.
                 */
                log: function log(eventType, data, element, requestOptions) {
                    var callbacks;

                    if (!element) {
                        // null element in the listener dictionary means any element will do.
                        // null element in the Logger.log call means we don't know the element name.
                        element = null;
                    }
                    // Check to see if we're listening for the event type.
                    if (has(listeners, eventType)) {
                        if (has(listeners[eventType], element)) {
                            // Make the callbacks.
                            callbacks = listeners[eventType][element];
                            $.each(callbacks, function (index, callback) {
                                try {
                                    callback(eventType, data, element);
                                } catch (err) {
                                    console.error({
                                        eventType: eventType,
                                        data: data,
                                        element: element,
                                        error: err
                                    });
                                }
                            });
                        }
                    }
                    // Regardless of whether any callbacks were made, log this event.
                    return sendRequest({
                        event_type: eventType,
                        event: JSON.stringify(data),
                        courserun_key: typeof $$course_id !== 'undefined' ? $$course_id : null,
                        page: window.location.href
                    }, requestOptions);
                },

                /**
                 * Adds a listener. If you want any element to trigger this listener,
                 * do element = null.
                 *
                 * Note that this method is used by external XBlocks, and the API cannot change without
                 * proper deprecation and notification for external authors.
                 */
                listen: function listen(eventType, element, callback) {
                    listeners[eventType] = listeners[eventType] || {};
                    listeners[eventType][element] = listeners[eventType][element] || [];
                    listeners[eventType][element].push(callback);
                },

                /**
                 * Binds `page_close` event.
                 *
                 * Note that this method is used by external XBlocks, and the API cannot change without
                 * proper deprecation and notification for external authors.
                 */
                bind: function bind() {
                    window.onunload = function () {
                        sendRequest({
                            event_type: 'page_close',
                            event: '',
                            page: window.location.href
                        }, { type: 'GET', async: false });
                    };
                }
            };
        }();

        this.Logger = Logger;
        // log_event exists for compatibility reasons and will soon be deprecated.
        this.log_event = Logger.log;
    }).call(this);
}).call(window);
/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(0)))

/***/ }),

/***/ "./common/static/js/src/tooltip_manager.js":
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function($, _) {(function () {
    'use strict';

    var TooltipManager = function TooltipManager(element) {
        this.element = $(element);
        // If tooltip container already exist, use it.
        this.tooltip = $('div.' + this.className.split(/\s+/).join('.'));
        // Otherwise, create new one.
        if (!this.tooltip.length) {
            this.tooltip = $('<div />', {
                class: this.className
            }).appendTo(this.element); // xss-lint: disable=javascript-jquery-insert-into-target
        }

        this.hide();
        _.bindAll(this, 'show', 'hide', 'showTooltip', 'moveTooltip', 'hideTooltip', 'click');
        this.bindEvents();
    };

    TooltipManager.prototype = {
        // Space separated list of class names for the tooltip container.
        className: 'tooltip',
        SELECTOR: '[data-tooltip]',

        bindEvents: function bindEvents() {
            this.element.on({
                'mouseover.TooltipManager': this.showTooltip,
                'mousemove.TooltipManager': this.moveTooltip,
                'mouseout.TooltipManager': this.hideTooltip,
                'click.TooltipManager': this.click
            }, this.SELECTOR);
        },

        getCoords: function getCoords(pageX, pageY) {
            return {
                left: pageX - 0.5 * this.tooltip.outerWidth(),
                top: pageY - (this.tooltip.outerHeight() + 15)
            };
        },

        show: function show() {
            this.tooltip.show().css('opacity', 1);
        },

        hide: function hide() {
            this.tooltip.hide().css('opacity', 0);
        },

        showTooltip: function showTooltip(event) {
            this.prepareTooltip(event.currentTarget, event.pageX, event.pageY);
            if (this.tooltipTimer) {
                clearTimeout(this.tooltipTimer);
            }
            this.tooltipTimer = setTimeout(this.show, 500);
        },

        prepareTooltip: function prepareTooltip(element, pageX, pageY) {
            pageX = typeof pageX !== 'undefined' ? pageX : element.offset().left + element.width() / 2;
            pageY = typeof pageY !== 'undefined' ? pageY : element.offset().top + element.height() / 2;
            var tooltipText = $(element).attr('data-tooltip');
            this.tooltip.text(tooltipText).css(this.getCoords(pageX, pageY));
        },

        // To manually trigger a tooltip to reveal, other than through user mouse movement:
        openTooltip: function openTooltip(element) {
            this.prepareTooltip(element);
            this.show();
            if (this.tooltipTimer) {
                clearTimeout(this.tooltipTimer);
            }
        },

        moveTooltip: function moveTooltip(event) {
            this.tooltip.css(this.getCoords(event.pageX, event.pageY));
        },

        hideTooltip: function hideTooltip() {
            clearTimeout(this.tooltipTimer);
            // Wait for a 50ms before hiding the tooltip to avoid blinking when
            // the item contains nested elements.
            this.tooltipTimer = setTimeout(this.hide, 50);
        },

        click: function click(event) {
            var showOnClick = !!$(event.currentTarget).data('tooltip-show-on-click'); // Default is false
            if (showOnClick) {
                this.show();
                if (this.tooltipTimer) {
                    clearTimeout(this.tooltipTimer);
                }
            } else {
                this.hideTooltip(event);
            }
        },

        destroy: function destroy() {
            this.tooltip.remove();
            // Unbind all delegated event handlers in the ".TooltipManager"
            // namespace.
            this.element.off('.TooltipManager', this.SELECTOR);
        }
    };

    window.TooltipManager = TooltipManager;
    $(document).ready(function () {
        window.globalTooltipManager = new TooltipManager(document.body);
    });
})();
/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(0), __webpack_require__(1)))

/***/ }),

/***/ "./common/static/js/vendor/date.js":
/***/ (function(module, exports) {

/**
 * @version: 1.0 Alpha-1
 * @author: Coolite Inc. http://www.coolite.com/
 * @date: 2008-05-13
 * @copyright: Copyright (c) 2006-2008, Coolite Inc. (http://www.coolite.com/). All rights reserved.
 * @license: Licensed under The MIT License. See license.txt and http://www.datejs.com/license/.
 * @website: http://www.datejs.com/
 */
Date.CultureInfo = { name: "en-US", englishName: "English (United States)", nativeName: "English (United States)", dayNames: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], abbreviatedDayNames: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], shortestDayNames: ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"], firstLetterDayNames: ["S", "M", "T", "W", "T", "F", "S"], monthNames: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], abbreviatedMonthNames: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], amDesignator: "AM", pmDesignator: "PM", firstDayOfWeek: 0, twoDigitYearMax: 2029, dateElementOrder: "mdy", formatPatterns: { shortDate: "M/d/yyyy", longDate: "dddd, MMMM dd, yyyy", shortTime: "h:mm tt", longTime: "h:mm:ss tt", fullDateTime: "dddd, MMMM dd, yyyy h:mm:ss tt", sortableDateTime: "yyyy-MM-ddTHH:mm:ss", universalSortableDateTime: "yyyy-MM-dd HH:mm:ssZ", rfc1123: "ddd, dd MMM yyyy HH:mm:ss GMT", monthDay: "MMMM dd", yearMonth: "MMMM, yyyy" }, regexPatterns: { jan: /^jan(uary)?/i, feb: /^feb(ruary)?/i, mar: /^mar(ch)?/i, apr: /^apr(il)?/i, may: /^may/i, jun: /^jun(e)?/i, jul: /^jul(y)?/i, aug: /^aug(ust)?/i, sep: /^sep(t(ember)?)?/i, oct: /^oct(ober)?/i, nov: /^nov(ember)?/i, dec: /^dec(ember)?/i, sun: /^su(n(day)?)?/i, mon: /^mo(n(day)?)?/i, tue: /^tu(e(s(day)?)?)?/i, wed: /^we(d(nesday)?)?/i, thu: /^th(u(r(s(day)?)?)?)?/i, fri: /^fr(i(day)?)?/i, sat: /^sa(t(urday)?)?/i, future: /^next/i, past: /^last|past|prev(ious)?/i, add: /^(\+|aft(er)?|from|hence)/i, subtract: /^(\-|bef(ore)?|ago)/i, yesterday: /^yes(terday)?/i, today: /^t(od(ay)?)?/i, tomorrow: /^tom(orrow)?/i, now: /^n(ow)?/i, millisecond: /^ms|milli(second)?s?/i, second: /^sec(ond)?s?/i, minute: /^mn|min(ute)?s?/i, hour: /^h(our)?s?/i, week: /^w(eek)?s?/i, month: /^m(onth)?s?/i, day: /^d(ay)?s?/i, year: /^y(ear)?s?/i, shortMeridian: /^(a|p)/i, longMeridian: /^(a\.?m?\.?|p\.?m?\.?)/i, timezone: /^((e(s|d)t|c(s|d)t|m(s|d)t|p(s|d)t)|((gmt)?\s*(\+|\-)\s*\d\d\d\d?)|gmt|utc)/i, ordinalSuffix: /^\s*(st|nd|rd|th)/i, timeContext: /^\s*(\:|a(?!u|p)|p)/i }, timezones: [{ name: "UTC", offset: "-000" }, { name: "GMT", offset: "-000" }, { name: "EST", offset: "-0500" }, { name: "EDT", offset: "-0400" }, { name: "CST", offset: "-0600" }, { name: "CDT", offset: "-0500" }, { name: "MST", offset: "-0700" }, { name: "MDT", offset: "-0600" }, { name: "PST", offset: "-0800" }, { name: "PDT", offset: "-0700" }] };
(function () {
  var $D = Date,
      $P = $D.prototype,
      $C = $D.CultureInfo,
      p = function p(s, l) {
    if (!l) {
      l = 2;
    }
    return ("000" + s).slice(l * -1);
  };$P.clearTime = function () {
    this.setHours(0);this.setMinutes(0);this.setSeconds(0);this.setMilliseconds(0);return this;
  };$P.setTimeToNow = function () {
    var n = new Date();this.setHours(n.getHours());this.setMinutes(n.getMinutes());this.setSeconds(n.getSeconds());this.setMilliseconds(n.getMilliseconds());return this;
  };$D.today = function () {
    return new Date().clearTime();
  };$D.compare = function (date1, date2) {
    if (isNaN(date1) || isNaN(date2)) {
      throw new Error(date1 + " - " + date2);
    } else if (date1 instanceof Date && date2 instanceof Date) {
      return date1 < date2 ? -1 : date1 > date2 ? 1 : 0;
    } else {
      throw new TypeError(date1 + " - " + date2);
    }
  };$D.equals = function (date1, date2) {
    return date1.compareTo(date2) === 0;
  };$D.getDayNumberFromName = function (name) {
    var n = $C.dayNames,
        m = $C.abbreviatedDayNames,
        o = $C.shortestDayNames,
        s = name.toLowerCase();for (var i = 0; i < n.length; i++) {
      if (n[i].toLowerCase() == s || m[i].toLowerCase() == s || o[i].toLowerCase() == s) {
        return i;
      }
    }
    return -1;
  };$D.getMonthNumberFromName = function (name) {
    var n = $C.monthNames,
        m = $C.abbreviatedMonthNames,
        s = name.toLowerCase();for (var i = 0; i < n.length; i++) {
      if (n[i].toLowerCase() == s || m[i].toLowerCase() == s) {
        return i;
      }
    }
    return -1;
  };$D.isLeapYear = function (year) {
    return year % 4 === 0 && year % 100 !== 0 || year % 400 === 0;
  };$D.getDaysInMonth = function (year, month) {
    return [31, $D.isLeapYear(year) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month];
  };$D.getTimezoneAbbreviation = function (offset) {
    var z = $C.timezones,
        p;for (var i = 0; i < z.length; i++) {
      if (z[i].offset === offset) {
        return z[i].name;
      }
    }
    return null;
  };$D.getTimezoneOffset = function (name) {
    var z = $C.timezones,
        p;for (var i = 0; i < z.length; i++) {
      if (z[i].name === name.toUpperCase()) {
        return z[i].offset;
      }
    }
    return null;
  };$P.clone = function () {
    return new Date(this.getTime());
  };$P.compareTo = function (date) {
    return Date.compare(this, date);
  };$P.equals = function (date) {
    return Date.equals(this, date || new Date());
  };$P.between = function (start, end) {
    return this.getTime() >= start.getTime() && this.getTime() <= end.getTime();
  };$P.isAfter = function (date) {
    return this.compareTo(date || new Date()) === 1;
  };$P.isBefore = function (date) {
    return this.compareTo(date || new Date()) === -1;
  };$P.isToday = function () {
    return this.isSameDay(new Date());
  };$P.isSameDay = function (date) {
    return this.clone().clearTime().equals(date.clone().clearTime());
  };$P.addMilliseconds = function (value) {
    this.setMilliseconds(this.getMilliseconds() + value);return this;
  };$P.addSeconds = function (value) {
    return this.addMilliseconds(value * 1000);
  };$P.addMinutes = function (value) {
    return this.addMilliseconds(value * 60000);
  };$P.addHours = function (value) {
    return this.addMilliseconds(value * 3600000);
  };$P.addDays = function (value) {
    this.setDate(this.getDate() + value);return this;
  };$P.addWeeks = function (value) {
    return this.addDays(value * 7);
  };$P.addMonths = function (value) {
    var n = this.getDate();this.setDate(1);this.setMonth(this.getMonth() + value);this.setDate(Math.min(n, $D.getDaysInMonth(this.getFullYear(), this.getMonth())));return this;
  };$P.addYears = function (value) {
    return this.addMonths(value * 12);
  };$P.add = function (config) {
    if (typeof config == "number") {
      this._orient = config;return this;
    }
    var x = config;if (x.milliseconds) {
      this.addMilliseconds(x.milliseconds);
    }
    if (x.seconds) {
      this.addSeconds(x.seconds);
    }
    if (x.minutes) {
      this.addMinutes(x.minutes);
    }
    if (x.hours) {
      this.addHours(x.hours);
    }
    if (x.weeks) {
      this.addWeeks(x.weeks);
    }
    if (x.months) {
      this.addMonths(x.months);
    }
    if (x.years) {
      this.addYears(x.years);
    }
    if (x.days) {
      this.addDays(x.days);
    }
    return this;
  };var $y, $m, $d;$P.getWeek = function () {
    var a, b, c, d, e, f, g, n, s, w;$y = !$y ? this.getFullYear() : $y;$m = !$m ? this.getMonth() + 1 : $m;$d = !$d ? this.getDate() : $d;if ($m <= 2) {
      a = $y - 1;b = (a / 4 | 0) - (a / 100 | 0) + (a / 400 | 0);c = ((a - 1) / 4 | 0) - ((a - 1) / 100 | 0) + ((a - 1) / 400 | 0);s = b - c;e = 0;f = $d - 1 + 31 * ($m - 1);
    } else {
      a = $y;b = (a / 4 | 0) - (a / 100 | 0) + (a / 400 | 0);c = ((a - 1) / 4 | 0) - ((a - 1) / 100 | 0) + ((a - 1) / 400 | 0);s = b - c;e = s + 1;f = $d + (153 * ($m - 3) + 2) / 5 + 58 + s;
    }
    g = (a + b) % 7;d = (f + g - e) % 7;n = f + 3 - d | 0;if (n < 0) {
      w = 53 - ((g - s) / 5 | 0);
    } else if (n > 364 + s) {
      w = 1;
    } else {
      w = (n / 7 | 0) + 1;
    }
    $y = $m = $d = null;return w;
  };$P.getISOWeek = function () {
    $y = this.getUTCFullYear();$m = this.getUTCMonth() + 1;$d = this.getUTCDate();return p(this.getWeek());
  };$P.setWeek = function (n) {
    return this.moveToDayOfWeek(1).addWeeks(n - this.getWeek());
  };$D._validate = function (n, min, max, name) {
    if (typeof n == "undefined") {
      return false;
    } else if (typeof n != "number") {
      throw new TypeError(n + " is not a Number.");
    } else if (n < min || n > max) {
      throw new RangeError(n + " is not a valid value for " + name + ".");
    }
    return true;
  };$D.validateMillisecond = function (value) {
    return $D._validate(value, 0, 999, "millisecond");
  };$D.validateSecond = function (value) {
    return $D._validate(value, 0, 59, "second");
  };$D.validateMinute = function (value) {
    return $D._validate(value, 0, 59, "minute");
  };$D.validateHour = function (value) {
    return $D._validate(value, 0, 23, "hour");
  };$D.validateDay = function (value, year, month) {
    return $D._validate(value, 1, $D.getDaysInMonth(year, month), "day");
  };$D.validateMonth = function (value) {
    return $D._validate(value, 0, 11, "month");
  };$D.validateYear = function (value) {
    return $D._validate(value, 0, 9999, "year");
  };$P.set = function (config) {
    if ($D.validateMillisecond(config.millisecond)) {
      this.addMilliseconds(config.millisecond - this.getMilliseconds());
    }
    if ($D.validateSecond(config.second)) {
      this.addSeconds(config.second - this.getSeconds());
    }
    if ($D.validateMinute(config.minute)) {
      this.addMinutes(config.minute - this.getMinutes());
    }
    if ($D.validateHour(config.hour)) {
      this.addHours(config.hour - this.getHours());
    }
    if ($D.validateMonth(config.month)) {
      this.addMonths(config.month - this.getMonth());
    }
    if ($D.validateYear(config.year)) {
      this.addYears(config.year - this.getFullYear());
    }
    if ($D.validateDay(config.day, this.getFullYear(), this.getMonth())) {
      this.addDays(config.day - this.getDate());
    }
    if (config.timezone) {
      this.setTimezone(config.timezone);
    }
    if (config.timezoneOffset) {
      this.setTimezoneOffset(config.timezoneOffset);
    }
    if (config.week && $D._validate(config.week, 0, 53, "week")) {
      this.setWeek(config.week);
    }
    return this;
  };$P.moveToFirstDayOfMonth = function () {
    return this.set({ day: 1 });
  };$P.moveToLastDayOfMonth = function () {
    return this.set({ day: $D.getDaysInMonth(this.getFullYear(), this.getMonth()) });
  };$P.moveToNthOccurrence = function (dayOfWeek, occurrence) {
    var shift = 0;if (occurrence > 0) {
      shift = occurrence - 1;
    } else if (occurrence === -1) {
      this.moveToLastDayOfMonth();if (this.getDay() !== dayOfWeek) {
        this.moveToDayOfWeek(dayOfWeek, -1);
      }
      return this;
    }
    return this.moveToFirstDayOfMonth().addDays(-1).moveToDayOfWeek(dayOfWeek, +1).addWeeks(shift);
  };$P.moveToDayOfWeek = function (dayOfWeek, orient) {
    var diff = (dayOfWeek - this.getDay() + 7 * (orient || +1)) % 7;return this.addDays(diff === 0 ? diff += 7 * (orient || +1) : diff);
  };$P.moveToMonth = function (month, orient) {
    var diff = (month - this.getMonth() + 12 * (orient || +1)) % 12;return this.addMonths(diff === 0 ? diff += 12 * (orient || +1) : diff);
  };$P.getOrdinalNumber = function () {
    return Math.ceil((this.clone().clearTime() - new Date(this.getFullYear(), 0, 1)) / 86400000) + 1;
  };$P.getTimezone = function () {
    return $D.getTimezoneAbbreviation(this.getUTCOffset());
  };$P.setTimezoneOffset = function (offset) {
    var here = this.getTimezoneOffset(),
        there = Number(offset) * -6 / 10;return this.addMinutes(there - here);
  };$P.setTimezone = function (offset) {
    return this.setTimezoneOffset($D.getTimezoneOffset(offset));
  };$P.hasDaylightSavingTime = function () {
    return Date.today().set({ month: 0, day: 1 }).getTimezoneOffset() !== Date.today().set({ month: 6, day: 1 }).getTimezoneOffset();
  };$P.isDaylightSavingTime = function () {
    return this.hasDaylightSavingTime() && new Date().getTimezoneOffset() === Date.today().set({ month: 6, day: 1 }).getTimezoneOffset();
  };$P.getUTCOffset = function () {
    var n = this.getTimezoneOffset() * -10 / 6,
        r;if (n < 0) {
      r = (n - 10000).toString();return r.charAt(0) + r.substr(2);
    } else {
      r = (n + 10000).toString();return "+" + r.substr(1);
    }
  };$P.getElapsed = function (date) {
    return (date || new Date()) - this;
  };if (!$P.toISOString) {
    $P.toISOString = function () {
      function f(n) {
        return n < 10 ? '0' + n : n;
      }
      return '"' + this.getUTCFullYear() + '-' + f(this.getUTCMonth() + 1) + '-' + f(this.getUTCDate()) + 'T' + f(this.getUTCHours()) + ':' + f(this.getUTCMinutes()) + ':' + f(this.getUTCSeconds()) + 'Z"';
    };
  }
  if (typeof $P._toString === 'undefined') {
    $P._toString = $P.toString;
  }$P.toString = function (format) {
    var x = this;if (format && format.length == 1) {
      var c = $C.formatPatterns;x.t = x.toString;switch (format) {case "d":
          return x.t(c.shortDate);case "D":
          return x.t(c.longDate);case "F":
          return x.t(c.fullDateTime);case "m":
          return x.t(c.monthDay);case "r":
          return x.t(c.rfc1123);case "s":
          return x.t(c.sortableDateTime);case "t":
          return x.t(c.shortTime);case "T":
          return x.t(c.longTime);case "u":
          return x.t(c.universalSortableDateTime);case "y":
          return x.t(c.yearMonth);}
    }
    var ord = function ord(n) {
      switch (n * 1) {case 1:case 21:case 31:
          return "st";case 2:case 22:
          return "nd";case 3:case 23:
          return "rd";default:
          return "th";}
    };return format ? format.replace(/(\\)?(dd?d?d?|MM?M?M?|yy?y?y?|hh?|HH?|mm?|ss?|tt?|S)/g, function (m) {
      if (m.charAt(0) === "\\") {
        return m.replace("\\", "");
      }
      x.h = x.getHours;switch (m) {case "hh":
          return p(x.h() < 13 ? x.h() === 0 ? 12 : x.h() : x.h() - 12);case "h":
          return x.h() < 13 ? x.h() === 0 ? 12 : x.h() : x.h() - 12;case "HH":
          return p(x.h());case "H":
          return x.h();case "mm":
          return p(x.getMinutes());case "m":
          return x.getMinutes();case "ss":
          return p(x.getSeconds());case "s":
          return x.getSeconds();case "yyyy":
          return p(x.getFullYear(), 4);case "yy":
          return p(x.getFullYear());case "dddd":
          return $C.dayNames[x.getDay()];case "ddd":
          return $C.abbreviatedDayNames[x.getDay()];case "dd":
          return p(x.getDate());case "d":
          return x.getDate();case "MMMM":
          return $C.monthNames[x.getMonth()];case "MMM":
          return $C.abbreviatedMonthNames[x.getMonth()];case "MM":
          return p(x.getMonth() + 1);case "M":
          return x.getMonth() + 1;case "t":
          return x.h() < 12 ? $C.amDesignator.substring(0, 1) : $C.pmDesignator.substring(0, 1);case "tt":
          return x.h() < 12 ? $C.amDesignator : $C.pmDesignator;case "S":
          return ord(x.getDate());default:
          return m;}
    }) : this._toString();
  };
})();
(function () {
  var $D = Date,
      $P = $D.prototype,
      $C = $D.CultureInfo,
      $N = Number.prototype;$P._orient = +1;$P._nth = null;$P._is = false;$P._same = false;$P._isSecond = false;$N._dateElement = "day";$P.next = function () {
    this._orient = +1;return this;
  };$D.next = function () {
    return $D.today().next();
  };$P.last = $P.prev = $P.previous = function () {
    this._orient = -1;return this;
  };$D.last = $D.prev = $D.previous = function () {
    return $D.today().last();
  };$P.is = function () {
    this._is = true;return this;
  };$P.same = function () {
    this._same = true;this._isSecond = false;return this;
  };$P.today = function () {
    return this.same().day();
  };$P.weekday = function () {
    if (this._is) {
      this._is = false;return !this.is().sat() && !this.is().sun();
    }
    return false;
  };$P.at = function (time) {
    return typeof time === "string" ? $D.parse(this.toString("d") + " " + time) : this.set(time);
  };$N.fromNow = $N.after = function (date) {
    var c = {};c[this._dateElement] = this;return (!date ? new Date() : date.clone()).add(c);
  };$N.ago = $N.before = function (date) {
    var c = {};c[this._dateElement] = this * -1;return (!date ? new Date() : date.clone()).add(c);
  };var dx = "sunday monday tuesday wednesday thursday friday saturday".split(/\s/),
      mx = "january february march april may june july august september october november december".split(/\s/),
      px = "Millisecond Second Minute Hour Day Week Month Year".split(/\s/),
      pxf = "Milliseconds Seconds Minutes Hours Date Week Month FullYear".split(/\s/),
      nth = "final first second third fourth fifth".split(/\s/),
      de;$P.toObject = function () {
    var o = {};for (var i = 0; i < px.length; i++) {
      o[px[i].toLowerCase()] = this["get" + pxf[i]]();
    }
    return o;
  };$D.fromObject = function (config) {
    config.week = null;return Date.today().set(config);
  };var df = function df(n) {
    return function () {
      if (this._is) {
        this._is = false;return this.getDay() == n;
      }
      if (this._nth !== null) {
        if (this._isSecond) {
          this.addSeconds(this._orient * -1);
        }
        this._isSecond = false;var ntemp = this._nth;this._nth = null;var temp = this.clone().moveToLastDayOfMonth();this.moveToNthOccurrence(n, ntemp);if (this > temp) {
          throw new RangeError($D.getDayName(n) + " does not occur " + ntemp + " times in the month of " + $D.getMonthName(temp.getMonth()) + " " + temp.getFullYear() + ".");
        }
        return this;
      }
      return this.moveToDayOfWeek(n, this._orient);
    };
  };var sdf = function sdf(n) {
    return function () {
      var t = $D.today(),
          shift = n - t.getDay();if (n === 0 && $C.firstDayOfWeek === 1 && t.getDay() !== 0) {
        shift = shift + 7;
      }
      return t.addDays(shift);
    };
  };for (var i = 0; i < dx.length; i++) {
    $D[dx[i].toUpperCase()] = $D[dx[i].toUpperCase().substring(0, 3)] = i;$D[dx[i]] = $D[dx[i].substring(0, 3)] = sdf(i);$P[dx[i]] = $P[dx[i].substring(0, 3)] = df(i);
  }
  var mf = function mf(n) {
    return function () {
      if (this._is) {
        this._is = false;return this.getMonth() === n;
      }
      return this.moveToMonth(n, this._orient);
    };
  };var smf = function smf(n) {
    return function () {
      return $D.today().set({ month: n, day: 1 });
    };
  };for (var j = 0; j < mx.length; j++) {
    $D[mx[j].toUpperCase()] = $D[mx[j].toUpperCase().substring(0, 3)] = j;$D[mx[j]] = $D[mx[j].substring(0, 3)] = smf(j);$P[mx[j]] = $P[mx[j].substring(0, 3)] = mf(j);
  }
  var ef = function ef(j) {
    return function () {
      if (this._isSecond) {
        this._isSecond = false;return this;
      }
      if (this._same) {
        this._same = this._is = false;var o1 = this.toObject(),
            o2 = (arguments[0] || new Date()).toObject(),
            v = "",
            k = j.toLowerCase();for (var m = px.length - 1; m > -1; m--) {
          v = px[m].toLowerCase();if (o1[v] != o2[v]) {
            return false;
          }
          if (k == v) {
            break;
          }
        }
        return true;
      }
      if (j.substring(j.length - 1) != "s") {
        j += "s";
      }
      return this["add" + j](this._orient);
    };
  };var nf = function nf(n) {
    return function () {
      this._dateElement = n;return this;
    };
  };for (var k = 0; k < px.length; k++) {
    de = px[k].toLowerCase();$P[de] = $P[de + "s"] = ef(px[k]);$N[de] = $N[de + "s"] = nf(de);
  }
  $P._ss = ef("Second");var nthfn = function nthfn(n) {
    return function (dayOfWeek) {
      if (this._same) {
        return this._ss(arguments[0]);
      }
      if (dayOfWeek || dayOfWeek === 0) {
        return this.moveToNthOccurrence(dayOfWeek, n);
      }
      this._nth = n;if (n === 2 && (dayOfWeek === undefined || dayOfWeek === null)) {
        this._isSecond = true;return this.addSeconds(this._orient);
      }
      return this;
    };
  };for (var l = 0; l < nth.length; l++) {
    $P[nth[l]] = l === 0 ? nthfn(-1) : nthfn(l);
  }
})();
(function () {
  Date.Parsing = { Exception: function Exception(s) {
      this.message = "Parse error at '" + s.substring(0, 10) + " ...'";
    } };var $P = Date.Parsing;var _ = $P.Operators = { rtoken: function rtoken(r) {
      return function (s) {
        var mx = s.match(r);if (mx) {
          return [mx[0], s.substring(mx[0].length)];
        } else {
          throw new $P.Exception(s);
        }
      };
    }, token: function token(s) {
      return function (s) {
        return _.rtoken(new RegExp("^\s*" + s + "\s*"))(s);
      };
    }, stoken: function stoken(s) {
      return _.rtoken(new RegExp("^" + s));
    }, until: function until(p) {
      return function (s) {
        var qx = [],
            rx = null;while (s.length) {
          try {
            rx = p.call(this, s);
          } catch (e) {
            qx.push(rx[0]);s = rx[1];continue;
          }
          break;
        }
        return [qx, s];
      };
    }, many: function many(p) {
      return function (s) {
        var rx = [],
            r = null;while (s.length) {
          try {
            r = p.call(this, s);
          } catch (e) {
            return [rx, s];
          }
          rx.push(r[0]);s = r[1];
        }
        return [rx, s];
      };
    }, optional: function optional(p) {
      return function (s) {
        var r = null;try {
          r = p.call(this, s);
        } catch (e) {
          return [null, s];
        }
        return [r[0], r[1]];
      };
    }, not: function not(p) {
      return function (s) {
        try {
          p.call(this, s);
        } catch (e) {
          return [null, s];
        }
        throw new $P.Exception(s);
      };
    }, ignore: function ignore(p) {
      return p ? function (s) {
        var r = null;r = p.call(this, s);return [null, r[1]];
      } : null;
    }, product: function product() {
      var px = arguments[0],
          qx = Array.prototype.slice.call(arguments, 1),
          rx = [];for (var i = 0; i < px.length; i++) {
        rx.push(_.each(px[i], qx));
      }
      return rx;
    }, cache: function cache(rule) {
      var cache = {},
          r = null;return function (s) {
        try {
          r = cache[s] = cache[s] || rule.call(this, s);
        } catch (e) {
          r = cache[s] = e;
        }
        if (r instanceof $P.Exception) {
          throw r;
        } else {
          return r;
        }
      };
    }, any: function any() {
      var px = arguments;return function (s) {
        var r = null;for (var i = 0; i < px.length; i++) {
          if (px[i] == null) {
            continue;
          }
          try {
            r = px[i].call(this, s);
          } catch (e) {
            r = null;
          }
          if (r) {
            return r;
          }
        }
        throw new $P.Exception(s);
      };
    }, each: function each() {
      var px = arguments;return function (s) {
        var rx = [],
            r = null;for (var i = 0; i < px.length; i++) {
          if (px[i] == null) {
            continue;
          }
          try {
            r = px[i].call(this, s);
          } catch (e) {
            throw new $P.Exception(s);
          }
          rx.push(r[0]);s = r[1];
        }
        return [rx, s];
      };
    }, all: function all() {
      var px = arguments,
          _ = _;return _.each(_.optional(px));
    }, sequence: function sequence(px, d, c) {
      d = d || _.rtoken(/^\s*/);c = c || null;if (px.length == 1) {
        return px[0];
      }
      return function (s) {
        var r = null,
            q = null;var rx = [];for (var i = 0; i < px.length; i++) {
          try {
            r = px[i].call(this, s);
          } catch (e) {
            break;
          }
          rx.push(r[0]);try {
            q = d.call(this, r[1]);
          } catch (ex) {
            q = null;break;
          }
          s = q[1];
        }
        if (!r) {
          throw new $P.Exception(s);
        }
        if (q) {
          throw new $P.Exception(q[1]);
        }
        if (c) {
          try {
            r = c.call(this, r[1]);
          } catch (ey) {
            throw new $P.Exception(r[1]);
          }
        }
        return [rx, r ? r[1] : s];
      };
    }, between: function between(d1, p, d2) {
      d2 = d2 || d1;var _fn = _.each(_.ignore(d1), p, _.ignore(d2));return function (s) {
        var rx = _fn.call(this, s);return [[rx[0][0], r[0][2]], rx[1]];
      };
    }, list: function list(p, d, c) {
      d = d || _.rtoken(/^\s*/);c = c || null;return p instanceof Array ? _.each(_.product(p.slice(0, -1), _.ignore(d)), p.slice(-1), _.ignore(c)) : _.each(_.many(_.each(p, _.ignore(d))), px, _.ignore(c));
    }, set: function set(px, d, c) {
      d = d || _.rtoken(/^\s*/);c = c || null;return function (s) {
        var r = null,
            p = null,
            q = null,
            rx = null,
            best = [[], s],
            last = false;for (var i = 0; i < px.length; i++) {
          q = null;p = null;r = null;last = px.length == 1;try {
            r = px[i].call(this, s);
          } catch (e) {
            continue;
          }
          rx = [[r[0]], r[1]];if (r[1].length > 0 && !last) {
            try {
              q = d.call(this, r[1]);
            } catch (ex) {
              last = true;
            }
          } else {
            last = true;
          }
          if (!last && q[1].length === 0) {
            last = true;
          }
          if (!last) {
            var qx = [];for (var j = 0; j < px.length; j++) {
              if (i != j) {
                qx.push(px[j]);
              }
            }
            p = _.set(qx, d).call(this, q[1]);if (p[0].length > 0) {
              rx[0] = rx[0].concat(p[0]);rx[1] = p[1];
            }
          }
          if (rx[1].length < best[1].length) {
            best = rx;
          }
          if (best[1].length === 0) {
            break;
          }
        }
        if (best[0].length === 0) {
          return best;
        }
        if (c) {
          try {
            q = c.call(this, best[1]);
          } catch (ey) {
            throw new $P.Exception(best[1]);
          }
          best[1] = q[1];
        }
        return best;
      };
    }, forward: function forward(gr, fname) {
      return function (s) {
        return gr[fname].call(this, s);
      };
    }, replace: function replace(rule, repl) {
      return function (s) {
        var r = rule.call(this, s);return [repl, r[1]];
      };
    }, process: function process(rule, fn) {
      return function (s) {
        var r = rule.call(this, s);return [fn.call(this, r[0]), r[1]];
      };
    }, min: function min(_min, rule) {
      return function (s) {
        var rx = rule.call(this, s);if (rx[0].length < _min) {
          throw new $P.Exception(s);
        }
        return rx;
      };
    } };var _generator = function _generator(op) {
    return function () {
      var args = null,
          rx = [];if (arguments.length > 1) {
        args = Array.prototype.slice.call(arguments);
      } else if (arguments[0] instanceof Array) {
        args = arguments[0];
      }
      if (args) {
        for (var i = 0, px = args.shift(); i < px.length; i++) {
          args.unshift(px[i]);rx.push(op.apply(null, args));args.shift();return rx;
        }
      } else {
        return op.apply(null, arguments);
      }
    };
  };var gx = "optional not ignore cache".split(/\s/);for (var i = 0; i < gx.length; i++) {
    _[gx[i]] = _generator(_[gx[i]]);
  }
  var _vector = function _vector(op) {
    return function () {
      if (arguments[0] instanceof Array) {
        return op.apply(null, arguments[0]);
      } else {
        return op.apply(null, arguments);
      }
    };
  };var vx = "each any all".split(/\s/);for (var j = 0; j < vx.length; j++) {
    _[vx[j]] = _vector(_[vx[j]]);
  }
})();(function () {
  var $D = Date,
      $P = $D.prototype,
      $C = $D.CultureInfo;var flattenAndCompact = function flattenAndCompact(ax) {
    var rx = [];for (var i = 0; i < ax.length; i++) {
      if (ax[i] instanceof Array) {
        rx = rx.concat(flattenAndCompact(ax[i]));
      } else {
        if (ax[i]) {
          rx.push(ax[i]);
        }
      }
    }
    return rx;
  };$D.Grammar = {};$D.Translator = { hour: function hour(s) {
      return function () {
        this.hour = Number(s);
      };
    }, minute: function minute(s) {
      return function () {
        this.minute = Number(s);
      };
    }, second: function second(s) {
      return function () {
        this.second = Number(s);
      };
    }, meridian: function meridian(s) {
      return function () {
        this.meridian = s.slice(0, 1).toLowerCase();
      };
    }, timezone: function timezone(s) {
      return function () {
        var n = s.replace(/[^\d\+\-]/g, "");if (n.length) {
          this.timezoneOffset = Number(n);
        } else {
          this.timezone = s.toLowerCase();
        }
      };
    }, day: function day(x) {
      var s = x[0];return function () {
        this.day = Number(s.match(/\d+/)[0]);
      };
    }, month: function month(s) {
      return function () {
        this.month = s.length == 3 ? "jan feb mar apr may jun jul aug sep oct nov dec".indexOf(s) / 4 : Number(s) - 1;
      };
    }, year: function year(s) {
      return function () {
        var n = Number(s);this.year = s.length > 2 ? n : n + (n + 2000 < $C.twoDigitYearMax ? 2000 : 1900);
      };
    }, rday: function rday(s) {
      return function () {
        switch (s) {case "yesterday":
            this.days = -1;break;case "tomorrow":
            this.days = 1;break;case "today":
            this.days = 0;break;case "now":
            this.days = 0;this.now = true;break;}
      };
    }, finishExact: function finishExact(x) {
      x = x instanceof Array ? x : [x];for (var i = 0; i < x.length; i++) {
        if (x[i]) {
          x[i].call(this);
        }
      }
      var now = new Date();if ((this.hour || this.minute) && !this.month && !this.year && !this.day) {
        this.day = now.getDate();
      }
      if (!this.year) {
        this.year = now.getFullYear();
      }
      if (!this.month && this.month !== 0) {
        this.month = now.getMonth();
      }
      if (!this.day) {
        this.day = 1;
      }
      if (!this.hour) {
        this.hour = 0;
      }
      if (!this.minute) {
        this.minute = 0;
      }
      if (!this.second) {
        this.second = 0;
      }
      if (this.meridian && this.hour) {
        if (this.meridian == "p" && this.hour < 12) {
          this.hour = this.hour + 12;
        } else if (this.meridian == "a" && this.hour == 12) {
          this.hour = 0;
        }
      }
      if (this.day > $D.getDaysInMonth(this.year, this.month)) {
        throw new RangeError(this.day + " is not a valid value for days.");
      }
      var r = new Date(this.year, this.month, this.day, this.hour, this.minute, this.second);if (this.timezone) {
        r.set({ timezone: this.timezone });
      } else if (this.timezoneOffset) {
        r.set({ timezoneOffset: this.timezoneOffset });
      }
      return r;
    }, finish: function finish(x) {
      x = x instanceof Array ? flattenAndCompact(x) : [x];if (x.length === 0) {
        return null;
      }
      for (var i = 0; i < x.length; i++) {
        if (typeof x[i] == "function") {
          x[i].call(this);
        }
      }
      var today = $D.today();if (this.now && !this.unit && !this.operator) {
        return new Date();
      } else if (this.now) {
        today = new Date();
      }
      var expression = !!(this.days && this.days !== null || this.orient || this.operator);var gap, mod, orient;orient = this.orient == "past" || this.operator == "subtract" ? -1 : 1;if (!this.now && "hour minute second".indexOf(this.unit) != -1) {
        today.setTimeToNow();
      }
      if (this.month || this.month === 0) {
        if ("year day hour minute second".indexOf(this.unit) != -1) {
          this.value = this.month + 1;this.month = null;expression = true;
        }
      }
      if (!expression && this.weekday && !this.day && !this.days) {
        var temp = Date[this.weekday]();this.day = temp.getDate();if (!this.month) {
          this.month = temp.getMonth();
        }
        this.year = temp.getFullYear();
      }
      if (expression && this.weekday && this.unit != "month") {
        this.unit = "day";gap = $D.getDayNumberFromName(this.weekday) - today.getDay();mod = 7;this.days = gap ? (gap + orient * mod) % mod : orient * mod;
      }
      if (this.month && this.unit == "day" && this.operator) {
        this.value = this.month + 1;this.month = null;
      }
      if (this.value != null && this.month != null && this.year != null) {
        this.day = this.value * 1;
      }
      if (this.month && !this.day && this.value) {
        today.set({ day: this.value * 1 });if (!expression) {
          this.day = this.value * 1;
        }
      }
      if (!this.month && this.value && this.unit == "month" && !this.now) {
        this.month = this.value;expression = true;
      }
      if (expression && (this.month || this.month === 0) && this.unit != "year") {
        this.unit = "month";gap = this.month - today.getMonth();mod = 12;this.months = gap ? (gap + orient * mod) % mod : orient * mod;this.month = null;
      }
      if (!this.unit) {
        this.unit = "day";
      }
      if (!this.value && this.operator && this.operator !== null && this[this.unit + "s"] && this[this.unit + "s"] !== null) {
        this[this.unit + "s"] = this[this.unit + "s"] + (this.operator == "add" ? 1 : -1) + (this.value || 0) * orient;
      } else if (this[this.unit + "s"] == null || this.operator != null) {
        if (!this.value) {
          this.value = 1;
        }
        this[this.unit + "s"] = this.value * orient;
      }
      if (this.meridian && this.hour) {
        if (this.meridian == "p" && this.hour < 12) {
          this.hour = this.hour + 12;
        } else if (this.meridian == "a" && this.hour == 12) {
          this.hour = 0;
        }
      }
      if (this.weekday && !this.day && !this.days) {
        var temp = Date[this.weekday]();this.day = temp.getDate();if (temp.getMonth() !== today.getMonth()) {
          this.month = temp.getMonth();
        }
      }
      if ((this.month || this.month === 0) && !this.day) {
        this.day = 1;
      }
      if (!this.orient && !this.operator && this.unit == "week" && this.value && !this.day && !this.month) {
        return Date.today().setWeek(this.value);
      }
      if (expression && this.timezone && this.day && this.days) {
        this.day = this.days;
      }
      return expression ? today.add(this) : today.set(this);
    } };var _ = $D.Parsing.Operators,
      g = $D.Grammar,
      t = $D.Translator,
      _fn;g.datePartDelimiter = _.rtoken(/^([\s\-\.\,\/\x27]+)/);g.timePartDelimiter = _.stoken(":");g.whiteSpace = _.rtoken(/^\s*/);g.generalDelimiter = _.rtoken(/^(([\s\,]|at|@|on)+)/);var _C = {};g.ctoken = function (keys) {
    var fn = _C[keys];if (!fn) {
      var c = $C.regexPatterns;var kx = keys.split(/\s+/),
          px = [];for (var i = 0; i < kx.length; i++) {
        px.push(_.replace(_.rtoken(c[kx[i]]), kx[i]));
      }
      fn = _C[keys] = _.any.apply(null, px);
    }
    return fn;
  };g.ctoken2 = function (key) {
    return _.rtoken($C.regexPatterns[key]);
  };g.h = _.cache(_.process(_.rtoken(/^(0[0-9]|1[0-2]|[1-9])/), t.hour));g.hh = _.cache(_.process(_.rtoken(/^(0[0-9]|1[0-2])/), t.hour));g.H = _.cache(_.process(_.rtoken(/^([0-1][0-9]|2[0-3]|[0-9])/), t.hour));g.HH = _.cache(_.process(_.rtoken(/^([0-1][0-9]|2[0-3])/), t.hour));g.m = _.cache(_.process(_.rtoken(/^([0-5][0-9]|[0-9])/), t.minute));g.mm = _.cache(_.process(_.rtoken(/^[0-5][0-9]/), t.minute));g.s = _.cache(_.process(_.rtoken(/^([0-5][0-9]|[0-9])/), t.second));g.ss = _.cache(_.process(_.rtoken(/^[0-5][0-9]/), t.second));g.hms = _.cache(_.sequence([g.H, g.m, g.s], g.timePartDelimiter));g.t = _.cache(_.process(g.ctoken2("shortMeridian"), t.meridian));g.tt = _.cache(_.process(g.ctoken2("longMeridian"), t.meridian));g.z = _.cache(_.process(_.rtoken(/^((\+|\-)\s*\d\d\d\d)|((\+|\-)\d\d\:?\d\d)/), t.timezone));g.zz = _.cache(_.process(_.rtoken(/^((\+|\-)\s*\d\d\d\d)|((\+|\-)\d\d\:?\d\d)/), t.timezone));g.zzz = _.cache(_.process(g.ctoken2("timezone"), t.timezone));g.timeSuffix = _.each(_.ignore(g.whiteSpace), _.set([g.tt, g.zzz]));g.time = _.each(_.optional(_.ignore(_.stoken("T"))), g.hms, g.timeSuffix);g.d = _.cache(_.process(_.each(_.rtoken(/^([0-2]\d|3[0-1]|\d)/), _.optional(g.ctoken2("ordinalSuffix"))), t.day));g.dd = _.cache(_.process(_.each(_.rtoken(/^([0-2]\d|3[0-1])/), _.optional(g.ctoken2("ordinalSuffix"))), t.day));g.ddd = g.dddd = _.cache(_.process(g.ctoken("sun mon tue wed thu fri sat"), function (s) {
    return function () {
      this.weekday = s;
    };
  }));g.M = _.cache(_.process(_.rtoken(/^(1[0-2]|0\d|\d)/), t.month));g.MM = _.cache(_.process(_.rtoken(/^(1[0-2]|0\d)/), t.month));g.MMM = g.MMMM = _.cache(_.process(g.ctoken("jan feb mar apr may jun jul aug sep oct nov dec"), t.month));g.y = _.cache(_.process(_.rtoken(/^(\d\d?)/), t.year));g.yy = _.cache(_.process(_.rtoken(/^(\d\d)/), t.year));g.yyy = _.cache(_.process(_.rtoken(/^(\d\d?\d?\d?)/), t.year));g.yyyy = _.cache(_.process(_.rtoken(/^(\d\d\d\d)/), t.year));_fn = function _fn() {
    return _.each(_.any.apply(null, arguments), _.not(g.ctoken2("timeContext")));
  };g.day = _fn(g.d, g.dd);g.month = _fn(g.M, g.MMM);g.year = _fn(g.yyyy, g.yy);g.orientation = _.process(g.ctoken("past future"), function (s) {
    return function () {
      this.orient = s;
    };
  });g.operator = _.process(g.ctoken("add subtract"), function (s) {
    return function () {
      this.operator = s;
    };
  });g.rday = _.process(g.ctoken("yesterday tomorrow today now"), t.rday);g.unit = _.process(g.ctoken("second minute hour day week month year"), function (s) {
    return function () {
      this.unit = s;
    };
  });g.value = _.process(_.rtoken(/^\d\d?(st|nd|rd|th)?/), function (s) {
    return function () {
      this.value = s.replace(/\D/g, "");
    };
  });g.expression = _.set([g.rday, g.operator, g.value, g.unit, g.orientation, g.ddd, g.MMM]);_fn = function _fn() {
    return _.set(arguments, g.datePartDelimiter);
  };g.mdy = _fn(g.ddd, g.month, g.day, g.year);g.ymd = _fn(g.ddd, g.year, g.month, g.day);g.dmy = _fn(g.ddd, g.day, g.month, g.year);g.date = function (s) {
    return (g[$C.dateElementOrder] || g.mdy).call(this, s);
  };g.format = _.process(_.many(_.any(_.process(_.rtoken(/^(dd?d?d?|MM?M?M?|yy?y?y?|hh?|HH?|mm?|ss?|tt?|zz?z?)/), function (fmt) {
    if (g[fmt]) {
      return g[fmt];
    } else {
      throw $D.Parsing.Exception(fmt);
    }
  }), _.process(_.rtoken(/^[^dMyhHmstz]+/), function (s) {
    return _.ignore(_.stoken(s));
  }))), function (rules) {
    return _.process(_.each.apply(null, rules), t.finishExact);
  });var _F = {};var _get = function _get(f) {
    return _F[f] = _F[f] || g.format(f)[0];
  };g.formats = function (fx) {
    if (fx instanceof Array) {
      var rx = [];for (var i = 0; i < fx.length; i++) {
        rx.push(_get(fx[i]));
      }
      return _.any.apply(null, rx);
    } else {
      return _get(fx);
    }
  };g._formats = g.formats(["\"yyyy-MM-ddTHH:mm:ssZ\"", "yyyy-MM-ddTHH:mm:ssZ", "yyyy-MM-ddTHH:mm:ssz", "yyyy-MM-ddTHH:mm:ss", "yyyy-MM-ddTHH:mmZ", "yyyy-MM-ddTHH:mmz", "yyyy-MM-ddTHH:mm", "ddd, MMM dd, yyyy H:mm:ss tt", "ddd MMM d yyyy HH:mm:ss zzz", "MMddyyyy", "ddMMyyyy", "Mddyyyy", "ddMyyyy", "Mdyyyy", "dMyyyy", "yyyy", "Mdyy", "dMyy", "d"]);g._start = _.process(_.set([g.date, g.time, g.expression], g.generalDelimiter, g.whiteSpace), t.finish);g.start = function (s) {
    try {
      var r = g._formats.call({}, s);if (r[1].length === 0) {
        return r;
      }
    } catch (e) {}
    return g._start.call({}, s);
  };$D._parse = $D.parse;$D.parse = function (s) {
    var r = null;if (!s) {
      return null;
    }
    if (s instanceof Date) {
      return s;
    }
    try {
      r = $D.Grammar.start.call({}, s.replace(/^\s*(\S*(\s+\S+)*)\s*$/, "$1"));
    } catch (e) {
      return null;
    }
    return r[1].length === 0 ? r[0] : null;
  };$D.getParseFunction = function (fx) {
    var fn = $D.Grammar.formats(fx);return function (s) {
      var r = null;try {
        r = fn.call({}, s);
      } catch (e) {
        return null;
      }
      return r[1].length === 0 ? r[0] : null;
    };
  };$D.parseExact = function (s, fx) {
    return $D.getParseFunction(fx)(s);
  };
})();

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

/***/ "./common/static/js/vendor/jquery-ui.min.js":
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(jQuery) {var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; };

/*! jQuery UI - v1.10.0 - 2013-01-23
* http://jqueryui.com
* Includes: jquery.ui.core.js, jquery.ui.widget.js, jquery.ui.mouse.js, jquery.ui.position.js, jquery.ui.draggable.js, jquery.ui.droppable.js, jquery.ui.resizable.js, jquery.ui.selectable.js, jquery.ui.sortable.js, jquery.ui.accordion.js, jquery.ui.autocomplete.js, jquery.ui.button.js, jquery.ui.datepicker.js, jquery.ui.dialog.js, jquery.ui.menu.js, jquery.ui.progressbar.js, jquery.ui.slider.js, jquery.ui.spinner.js, jquery.ui.tabs.js, jquery.ui.tooltip.js, jquery.ui.effect.js, jquery.ui.effect-blind.js, jquery.ui.effect-bounce.js, jquery.ui.effect-clip.js, jquery.ui.effect-drop.js, jquery.ui.effect-explode.js, jquery.ui.effect-fade.js, jquery.ui.effect-fold.js, jquery.ui.effect-highlight.js, jquery.ui.effect-pulsate.js, jquery.ui.effect-scale.js, jquery.ui.effect-shake.js, jquery.ui.effect-slide.js, jquery.ui.effect-transfer.js
* Copyright (c) 2013 jQuery Foundation and other contributors Licensed MIT */

(function (e, t) {
  function i(t, n) {
    var r,
        i,
        o,
        u = t.nodeName.toLowerCase();return "area" === u ? (r = t.parentNode, i = r.name, !t.href || !i || r.nodeName.toLowerCase() !== "map" ? !1 : (o = e("img[usemap=#" + i + "]")[0], !!o && s(o))) : (/input|select|textarea|button|object/.test(u) ? !t.disabled : "a" === u ? t.href || n : n) && s(t);
  }function s(t) {
    return e.expr.filters.visible(t) && !e(t).parents().addBack().filter(function () {
      return e.css(this, "visibility") === "hidden";
    }).length;
  }var n = 0,
      r = /^ui-id-\d+$/;e.ui = e.ui || {};if (e.ui.version) return;e.extend(e.ui, { version: "1.10.0", keyCode: { BACKSPACE: 8, COMMA: 188, DELETE: 46, DOWN: 40, END: 35, ENTER: 13, ESCAPE: 27, HOME: 36, LEFT: 37, NUMPAD_ADD: 107, NUMPAD_DECIMAL: 110, NUMPAD_DIVIDE: 111, NUMPAD_ENTER: 108, NUMPAD_MULTIPLY: 106, NUMPAD_SUBTRACT: 109, PAGE_DOWN: 34, PAGE_UP: 33, PERIOD: 190, RIGHT: 39, SPACE: 32, TAB: 9, UP: 38 } }), e.fn.extend({ _focus: e.fn.focus, focus: function focus(t, n) {
      return typeof t == "number" ? this.each(function () {
        var r = this;setTimeout(function () {
          e(r).focus(), n && n.call(r);
        }, t);
      }) : this._focus.apply(this, arguments);
    }, scrollParent: function scrollParent() {
      var t;return e.ui.ie && /(static|relative)/.test(this.css("position")) || /absolute/.test(this.css("position")) ? t = this.parents().filter(function () {
        return (/(relative|absolute|fixed)/.test(e.css(this, "position")) && /(auto|scroll)/.test(e.css(this, "overflow") + e.css(this, "overflow-y") + e.css(this, "overflow-x"))
        );
      }).eq(0) : t = this.parents().filter(function () {
        return (/(auto|scroll)/.test(e.css(this, "overflow") + e.css(this, "overflow-y") + e.css(this, "overflow-x"))
        );
      }).eq(0), /fixed/.test(this.css("position")) || !t.length ? e(document) : t;
    }, zIndex: function zIndex(n) {
      if (n !== t) return this.css("zIndex", n);if (this.length) {
        var r = e(this[0]),
            i,
            s;while (r.length && r[0] !== document) {
          i = r.css("position");if (i === "absolute" || i === "relative" || i === "fixed") {
            s = parseInt(r.css("zIndex"), 10);if (!isNaN(s) && s !== 0) return s;
          }r = r.parent();
        }
      }return 0;
    }, uniqueId: function uniqueId() {
      return this.each(function () {
        this.id || (this.id = "ui-id-" + ++n);
      });
    }, removeUniqueId: function removeUniqueId() {
      return this.each(function () {
        r.test(this.id) && e(this).removeAttr("id");
      });
    } }), e.extend(e.expr[":"], { data: e.expr.createPseudo ? e.expr.createPseudo(function (t) {
      return function (n) {
        return !!e.data(n, t);
      };
    }) : function (t, n, r) {
      return !!e.data(t, r[3]);
    }, focusable: function focusable(t) {
      return i(t, !isNaN(e.attr(t, "tabindex")));
    }, tabbable: function tabbable(t) {
      var n = e.attr(t, "tabindex"),
          r = isNaN(n);return (r || n >= 0) && i(t, !r);
    } }), e("<a>").outerWidth(1).jquery || e.each(["Width", "Height"], function (n, r) {
    function u(t, n, r, s) {
      return e.each(i, function () {
        n -= parseFloat(e.css(t, "padding" + this)) || 0, r && (n -= parseFloat(e.css(t, "border" + this + "Width")) || 0), s && (n -= parseFloat(e.css(t, "margin" + this)) || 0);
      }), n;
    }var i = r === "Width" ? ["Left", "Right"] : ["Top", "Bottom"],
        s = r.toLowerCase(),
        o = { innerWidth: e.fn.innerWidth, innerHeight: e.fn.innerHeight, outerWidth: e.fn.outerWidth, outerHeight: e.fn.outerHeight };e.fn["inner" + r] = function (n) {
      return n === t ? o["inner" + r].call(this) : this.each(function () {
        e(this).css(s, u(this, n) + "px");
      });
    }, e.fn["outer" + r] = function (t, n) {
      return typeof t != "number" ? o["outer" + r].call(this, t) : this.each(function () {
        e(this).css(s, u(this, t, !0, n) + "px");
      });
    };
  }), e.fn.addBack || (e.fn.addBack = function (e) {
    return this.add(e == null ? this.prevObject : this.prevObject.filter(e));
  }), e("<a>").data("a-b", "a").removeData("a-b").data("a-b") && (e.fn.removeData = function (t) {
    return function (n) {
      return arguments.length ? t.call(this, e.camelCase(n)) : t.call(this);
    };
  }(e.fn.removeData)), e.ui.ie = !!/msie [\w.]+/.exec(navigator.userAgent.toLowerCase()), e.support.selectstart = "onselectstart" in document.createElement("div"), e.fn.extend({ disableSelection: function disableSelection() {
      return this.bind((e.support.selectstart ? "selectstart" : "mousedown") + ".ui-disableSelection", function (e) {
        e.preventDefault();
      });
    }, enableSelection: function enableSelection() {
      return this.unbind(".ui-disableSelection");
    } }), e.extend(e.ui, { plugin: { add: function add(t, n, r) {
        var i,
            s = e.ui[t].prototype;for (i in r) {
          s.plugins[i] = s.plugins[i] || [], s.plugins[i].push([n, r[i]]);
        }
      }, call: function call(e, t, n) {
        var r,
            i = e.plugins[t];if (!i || !e.element[0].parentNode || e.element[0].parentNode.nodeType === 11) return;for (r = 0; r < i.length; r++) {
          e.options[i[r][0]] && i[r][1].apply(e.element, n);
        }
      } }, hasScroll: function hasScroll(t, n) {
      if (e(t).css("overflow") === "hidden") return !1;var r = n && n === "left" ? "scrollLeft" : "scrollTop",
          i = !1;return t[r] > 0 ? !0 : (t[r] = 1, i = t[r] > 0, t[r] = 0, i);
    } });
})(jQuery);(function (e, t) {
  var n = 0,
      r = Array.prototype.slice,
      i = e.cleanData;e.cleanData = function (t) {
    for (var n = 0, r; (r = t[n]) != null; n++) {
      try {
        e(r).triggerHandler("remove");
      } catch (s) {}
    }i(t);
  }, e.widget = function (t, n, r) {
    var i,
        s,
        o,
        u,
        a = {},
        f = t.split(".")[0];t = t.split(".")[1], i = f + "-" + t, r || (r = n, n = e.Widget), e.expr[":"][i.toLowerCase()] = function (t) {
      return !!e.data(t, i);
    }, e[f] = e[f] || {}, s = e[f][t], o = e[f][t] = function (e, t) {
      if (!this._createWidget) return new o(e, t);arguments.length && this._createWidget(e, t);
    }, e.extend(o, s, { version: r.version, _proto: e.extend({}, r), _childConstructors: [] }), u = new n(), u.options = e.widget.extend({}, u.options), e.each(r, function (t, r) {
      if (!e.isFunction(r)) {
        a[t] = r;return;
      }a[t] = function () {
        var e = function e() {
          return n.prototype[t].apply(this, arguments);
        },
            i = function i(e) {
          return n.prototype[t].apply(this, e);
        };return function () {
          var t = this._super,
              n = this._superApply,
              s;return this._super = e, this._superApply = i, s = r.apply(this, arguments), this._super = t, this._superApply = n, s;
        };
      }();
    }), o.prototype = e.widget.extend(u, { widgetEventPrefix: s ? u.widgetEventPrefix : t }, a, { constructor: o, namespace: f, widgetName: t, widgetFullName: i }), s ? (e.each(s._childConstructors, function (t, n) {
      var r = n.prototype;e.widget(r.namespace + "." + r.widgetName, o, n._proto);
    }), delete s._childConstructors) : n._childConstructors.push(o), e.widget.bridge(t, o);
  }, e.widget.extend = function (n) {
    var i = r.call(arguments, 1),
        s = 0,
        o = i.length,
        u,
        a;for (; s < o; s++) {
      for (u in i[s]) {
        a = i[s][u], i[s].hasOwnProperty(u) && a !== t && (e.isPlainObject(a) ? n[u] = e.isPlainObject(n[u]) ? e.widget.extend({}, n[u], a) : e.widget.extend({}, a) : n[u] = a);
      }
    }return n;
  }, e.widget.bridge = function (n, i) {
    var s = i.prototype.widgetFullName || n;e.fn[n] = function (o) {
      var u = typeof o == "string",
          a = r.call(arguments, 1),
          f = this;return o = !u && a.length ? e.widget.extend.apply(null, [o].concat(a)) : o, u ? this.each(function () {
        var r,
            i = e.data(this, s);if (!i) return e.error("cannot call methods on " + n + " prior to initialization; " + "attempted to call method '" + o + "'");if (!e.isFunction(i[o]) || o.charAt(0) === "_") return e.error("no such method '" + o + "' for " + n + " widget instance");r = i[o].apply(i, a);if (r !== i && r !== t) return f = r && r.jquery ? f.pushStack(r.get()) : r, !1;
      }) : this.each(function () {
        var t = e.data(this, s);t ? t.option(o || {})._init() : e.data(this, s, new i(o, this));
      }), f;
    };
  }, e.Widget = function () {}, e.Widget._childConstructors = [], e.Widget.prototype = { widgetName: "widget", widgetEventPrefix: "", defaultElement: "<div>", options: { disabled: !1, create: null }, _createWidget: function _createWidget(t, r) {
      r = e(r || this.defaultElement || this)[0], this.element = e(r), this.uuid = n++, this.eventNamespace = "." + this.widgetName + this.uuid, this.options = e.widget.extend({}, this.options, this._getCreateOptions(), t), this.bindings = e(), this.hoverable = e(), this.focusable = e(), r !== this && (e.data(r, this.widgetFullName, this), this._on(!0, this.element, { remove: function remove(e) {
          e.target === r && this.destroy();
        } }), this.document = e(r.style ? r.ownerDocument : r.document || r), this.window = e(this.document[0].defaultView || this.document[0].parentWindow)), this._create(), this._trigger("create", null, this._getCreateEventData()), this._init();
    }, _getCreateOptions: e.noop, _getCreateEventData: e.noop, _create: e.noop, _init: e.noop, destroy: function destroy() {
      this._destroy(), this.element.unbind(this.eventNamespace).removeData(this.widgetName).removeData(this.widgetFullName).removeData(e.camelCase(this.widgetFullName)), this.widget().unbind(this.eventNamespace).removeAttr("aria-disabled").removeClass(this.widgetFullName + "-disabled " + "ui-state-disabled"), this.bindings.unbind(this.eventNamespace), this.hoverable.removeClass("ui-state-hover"), this.focusable.removeClass("ui-state-focus");
    }, _destroy: e.noop, widget: function widget() {
      return this.element;
    }, option: function option(n, r) {
      var i = n,
          s,
          o,
          u;if (arguments.length === 0) return e.widget.extend({}, this.options);if (typeof n == "string") {
        i = {}, s = n.split("."), n = s.shift();if (s.length) {
          o = i[n] = e.widget.extend({}, this.options[n]);for (u = 0; u < s.length - 1; u++) {
            o[s[u]] = o[s[u]] || {}, o = o[s[u]];
          }n = s.pop();if (r === t) return o[n] === t ? null : o[n];o[n] = r;
        } else {
          if (r === t) return this.options[n] === t ? null : this.options[n];i[n] = r;
        }
      }return this._setOptions(i), this;
    }, _setOptions: function _setOptions(e) {
      var t;for (t in e) {
        this._setOption(t, e[t]);
      }return this;
    }, _setOption: function _setOption(e, t) {
      return this.options[e] = t, e === "disabled" && (this.widget().toggleClass(this.widgetFullName + "-disabled ui-state-disabled", !!t).attr("aria-disabled", t), this.hoverable.removeClass("ui-state-hover"), this.focusable.removeClass("ui-state-focus")), this;
    }, enable: function enable() {
      return this._setOption("disabled", !1);
    }, disable: function disable() {
      return this._setOption("disabled", !0);
    }, _on: function _on(t, n, r) {
      var i,
          s = this;typeof t != "boolean" && (r = n, n = t, t = !1), r ? (n = i = e(n), this.bindings = this.bindings.add(n)) : (r = n, n = this.element, i = this.widget()), e.each(r, function (r, o) {
        function u() {
          if (!t && (s.options.disabled === !0 || e(this).hasClass("ui-state-disabled"))) return;return (typeof o == "string" ? s[o] : o).apply(s, arguments);
        }typeof o != "string" && (u.guid = o.guid = o.guid || u.guid || e.guid++);var a = r.match(/^(\w+)\s*(.*)$/),
            f = a[1] + s.eventNamespace,
            l = a[2];l ? i.delegate(l, f, u) : n.bind(f, u);
      });
    }, _off: function _off(e, t) {
      t = (t || "").split(" ").join(this.eventNamespace + " ") + this.eventNamespace, e.unbind(t).undelegate(t);
    }, _delay: function _delay(e, t) {
      function n() {
        return (typeof e == "string" ? r[e] : e).apply(r, arguments);
      }var r = this;return setTimeout(n, t || 0);
    }, _hoverable: function _hoverable(t) {
      this.hoverable = this.hoverable.add(t), this._on(t, { mouseenter: function mouseenter(t) {
          e(t.currentTarget).addClass("ui-state-hover");
        }, mouseleave: function mouseleave(t) {
          e(t.currentTarget).removeClass("ui-state-hover");
        } });
    }, _focusable: function _focusable(t) {
      this.focusable = this.focusable.add(t), this._on(t, { focusin: function focusin(t) {
          e(t.currentTarget).addClass("ui-state-focus");
        }, focusout: function focusout(t) {
          e(t.currentTarget).removeClass("ui-state-focus");
        } });
    }, _trigger: function _trigger(t, n, r) {
      var i,
          s,
          o = this.options[t];r = r || {}, n = e.Event(n), n.type = (t === this.widgetEventPrefix ? t : this.widgetEventPrefix + t).toLowerCase(), n.target = this.element[0], s = n.originalEvent;if (s) for (i in s) {
        i in n || (n[i] = s[i]);
      }return this.element.trigger(n, r), !(e.isFunction(o) && o.apply(this.element[0], [n].concat(r)) === !1 || n.isDefaultPrevented());
    } }, e.each({ show: "fadeIn", hide: "fadeOut" }, function (t, n) {
    e.Widget.prototype["_" + t] = function (r, i, s) {
      typeof i == "string" && (i = { effect: i });var o,
          u = i ? i === !0 || typeof i == "number" ? n : i.effect || n : t;i = i || {}, typeof i == "number" && (i = { duration: i }), o = !e.isEmptyObject(i), i.complete = s, i.delay && r.delay(i.delay), o && e.effects && e.effects.effect[u] ? r[t](i) : u !== t && r[u] ? r[u](i.duration, i.easing, s) : r.queue(function (n) {
        e(this)[t](), s && s.call(r[0]), n();
      });
    };
  });
})(jQuery);(function (e, t) {
  var n = !1;e(document).mouseup(function () {
    n = !1;
  }), e.widget("ui.mouse", { version: "1.10.0", options: { cancel: "input,textarea,button,select,option", distance: 1, delay: 0 }, _mouseInit: function _mouseInit() {
      var t = this;this.element.bind("mousedown." + this.widgetName, function (e) {
        return t._mouseDown(e);
      }).bind("click." + this.widgetName, function (n) {
        if (!0 === e.data(n.target, t.widgetName + ".preventClickEvent")) return e.removeData(n.target, t.widgetName + ".preventClickEvent"), n.stopImmediatePropagation(), !1;
      }), this.started = !1;
    }, _mouseDestroy: function _mouseDestroy() {
      this.element.unbind("." + this.widgetName), this._mouseMoveDelegate && e(document).unbind("mousemove." + this.widgetName, this._mouseMoveDelegate).unbind("mouseup." + this.widgetName, this._mouseUpDelegate);
    }, _mouseDown: function _mouseDown(t) {
      if (n) return;this._mouseStarted && this._mouseUp(t), this._mouseDownEvent = t;var r = this,
          i = t.which === 1,
          s = typeof this.options.cancel == "string" && t.target.nodeName ? e(t.target).closest(this.options.cancel).length : !1;if (!i || s || !this._mouseCapture(t)) return !0;this.mouseDelayMet = !this.options.delay, this.mouseDelayMet || (this._mouseDelayTimer = setTimeout(function () {
        r.mouseDelayMet = !0;
      }, this.options.delay));if (this._mouseDistanceMet(t) && this._mouseDelayMet(t)) {
        this._mouseStarted = this._mouseStart(t) !== !1;if (!this._mouseStarted) return t.preventDefault(), !0;
      }return !0 === e.data(t.target, this.widgetName + ".preventClickEvent") && e.removeData(t.target, this.widgetName + ".preventClickEvent"), this._mouseMoveDelegate = function (e) {
        return r._mouseMove(e);
      }, this._mouseUpDelegate = function (e) {
        return r._mouseUp(e);
      }, e(document).bind("mousemove." + this.widgetName, this._mouseMoveDelegate).bind("mouseup." + this.widgetName, this._mouseUpDelegate), t.preventDefault(), n = !0, !0;
    }, _mouseMove: function _mouseMove(t) {
      return e.ui.ie && (!document.documentMode || document.documentMode < 9) && !t.button ? this._mouseUp(t) : this._mouseStarted ? (this._mouseDrag(t), t.preventDefault()) : (this._mouseDistanceMet(t) && this._mouseDelayMet(t) && (this._mouseStarted = this._mouseStart(this._mouseDownEvent, t) !== !1, this._mouseStarted ? this._mouseDrag(t) : this._mouseUp(t)), !this._mouseStarted);
    }, _mouseUp: function _mouseUp(t) {
      return e(document).unbind("mousemove." + this.widgetName, this._mouseMoveDelegate).unbind("mouseup." + this.widgetName, this._mouseUpDelegate), this._mouseStarted && (this._mouseStarted = !1, t.target === this._mouseDownEvent.target && e.data(t.target, this.widgetName + ".preventClickEvent", !0), this._mouseStop(t)), !1;
    }, _mouseDistanceMet: function _mouseDistanceMet(e) {
      return Math.max(Math.abs(this._mouseDownEvent.pageX - e.pageX), Math.abs(this._mouseDownEvent.pageY - e.pageY)) >= this.options.distance;
    }, _mouseDelayMet: function _mouseDelayMet() {
      return this.mouseDelayMet;
    }, _mouseStart: function _mouseStart() {}, _mouseDrag: function _mouseDrag() {}, _mouseStop: function _mouseStop() {}, _mouseCapture: function _mouseCapture() {
      return !0;
    } });
})(jQuery);(function (e, t) {
  function h(e, t, n) {
    return [parseInt(e[0], 10) * (l.test(e[0]) ? t / 100 : 1), parseInt(e[1], 10) * (l.test(e[1]) ? n / 100 : 1)];
  }function p(t, n) {
    return parseInt(e.css(t, n), 10) || 0;
  }function d(t) {
    var n = t[0];return n.nodeType === 9 ? { width: t.width(), height: t.height(), offset: { top: 0, left: 0 } } : e.isWindow(n) ? { width: t.width(), height: t.height(), offset: { top: t.scrollTop(), left: t.scrollLeft() } } : n.preventDefault ? { width: 0, height: 0, offset: { top: n.pageY, left: n.pageX } } : { width: t.outerWidth(), height: t.outerHeight(), offset: t.offset() };
  }e.ui = e.ui || {};var n,
      r = Math.max,
      i = Math.abs,
      s = Math.round,
      o = /left|center|right/,
      u = /top|center|bottom/,
      a = /[\+\-]\d+%?/,
      f = /^\w+/,
      l = /%$/,
      c = e.fn.position;e.position = { scrollbarWidth: function scrollbarWidth() {
      if (n !== t) return n;var r,
          i,
          s = e("<div style='display:block;width:50px;height:50px;overflow:hidden;'><div style='height:100px;width:auto;'></div></div>"),
          o = s.children()[0];return e("body").append(s), r = o.offsetWidth, s.css("overflow", "scroll"), i = o.offsetWidth, r === i && (i = s[0].clientWidth), s.remove(), n = r - i;
    }, getScrollInfo: function getScrollInfo(t) {
      var n = t.isWindow ? "" : t.element.css("overflow-x"),
          r = t.isWindow ? "" : t.element.css("overflow-y"),
          i = n === "scroll" || n === "auto" && t.width < t.element[0].scrollWidth,
          s = r === "scroll" || r === "auto" && t.height < t.element[0].scrollHeight;return { width: i ? e.position.scrollbarWidth() : 0, height: s ? e.position.scrollbarWidth() : 0 };
    }, getWithinInfo: function getWithinInfo(t) {
      var n = e(t || window),
          r = e.isWindow(n[0]);return { element: n, isWindow: r, offset: n.offset() || { left: 0, top: 0 }, scrollLeft: n.scrollLeft(), scrollTop: n.scrollTop(), width: r ? n.width() : n.outerWidth(), height: r ? n.height() : n.outerHeight() };
    } }, e.fn.position = function (t) {
    if (!t || !t.of) return c.apply(this, arguments);t = e.extend({}, t);var n,
        l,
        v,
        m,
        g,
        y,
        b = e(t.of),
        w = e.position.getWithinInfo(t.within),
        E = e.position.getScrollInfo(w),
        S = (t.collision || "flip").split(" "),
        x = {};return y = d(b), b[0].preventDefault && (t.at = "left top"), l = y.width, v = y.height, m = y.offset, g = e.extend({}, m), e.each(["my", "at"], function () {
      var e = (t[this] || "").split(" "),
          n,
          r;e.length === 1 && (e = o.test(e[0]) ? e.concat(["center"]) : u.test(e[0]) ? ["center"].concat(e) : ["center", "center"]), e[0] = o.test(e[0]) ? e[0] : "center", e[1] = u.test(e[1]) ? e[1] : "center", n = a.exec(e[0]), r = a.exec(e[1]), x[this] = [n ? n[0] : 0, r ? r[0] : 0], t[this] = [f.exec(e[0])[0], f.exec(e[1])[0]];
    }), S.length === 1 && (S[1] = S[0]), t.at[0] === "right" ? g.left += l : t.at[0] === "center" && (g.left += l / 2), t.at[1] === "bottom" ? g.top += v : t.at[1] === "center" && (g.top += v / 2), n = h(x.at, l, v), g.left += n[0], g.top += n[1], this.each(function () {
      var o,
          u,
          a = e(this),
          f = a.outerWidth(),
          c = a.outerHeight(),
          d = p(this, "marginLeft"),
          y = p(this, "marginTop"),
          T = f + d + p(this, "marginRight") + E.width,
          N = c + y + p(this, "marginBottom") + E.height,
          C = e.extend({}, g),
          k = h(x.my, a.outerWidth(), a.outerHeight());t.my[0] === "right" ? C.left -= f : t.my[0] === "center" && (C.left -= f / 2), t.my[1] === "bottom" ? C.top -= c : t.my[1] === "center" && (C.top -= c / 2), C.left += k[0], C.top += k[1], e.support.offsetFractions || (C.left = s(C.left), C.top = s(C.top)), o = { marginLeft: d, marginTop: y }, e.each(["left", "top"], function (r, i) {
        e.ui.position[S[r]] && e.ui.position[S[r]][i](C, { targetWidth: l, targetHeight: v, elemWidth: f, elemHeight: c, collisionPosition: o, collisionWidth: T, collisionHeight: N, offset: [n[0] + k[0], n[1] + k[1]], my: t.my, at: t.at, within: w, elem: a });
      }), t.using && (u = function u(e) {
        var n = m.left - C.left,
            s = n + l - f,
            o = m.top - C.top,
            u = o + v - c,
            h = { target: { element: b, left: m.left, top: m.top, width: l, height: v }, element: { element: a, left: C.left, top: C.top, width: f, height: c }, horizontal: s < 0 ? "left" : n > 0 ? "right" : "center", vertical: u < 0 ? "top" : o > 0 ? "bottom" : "middle" };l < f && i(n + s) < l && (h.horizontal = "center"), v < c && i(o + u) < v && (h.vertical = "middle"), r(i(n), i(s)) > r(i(o), i(u)) ? h.important = "horizontal" : h.important = "vertical", t.using.call(this, e, h);
      }), a.offset(e.extend(C, { using: u }));
    });
  }, e.ui.position = { fit: { left: function left(e, t) {
        var n = t.within,
            i = n.isWindow ? n.scrollLeft : n.offset.left,
            s = n.width,
            o = e.left - t.collisionPosition.marginLeft,
            u = i - o,
            a = o + t.collisionWidth - s - i,
            f;t.collisionWidth > s ? u > 0 && a <= 0 ? (f = e.left + u + t.collisionWidth - s - i, e.left += u - f) : a > 0 && u <= 0 ? e.left = i : u > a ? e.left = i + s - t.collisionWidth : e.left = i : u > 0 ? e.left += u : a > 0 ? e.left -= a : e.left = r(e.left - o, e.left);
      }, top: function top(e, t) {
        var n = t.within,
            i = n.isWindow ? n.scrollTop : n.offset.top,
            s = t.within.height,
            o = e.top - t.collisionPosition.marginTop,
            u = i - o,
            a = o + t.collisionHeight - s - i,
            f;t.collisionHeight > s ? u > 0 && a <= 0 ? (f = e.top + u + t.collisionHeight - s - i, e.top += u - f) : a > 0 && u <= 0 ? e.top = i : u > a ? e.top = i + s - t.collisionHeight : e.top = i : u > 0 ? e.top += u : a > 0 ? e.top -= a : e.top = r(e.top - o, e.top);
      } }, flip: { left: function left(e, t) {
        var n = t.within,
            r = n.offset.left + n.scrollLeft,
            s = n.width,
            o = n.isWindow ? n.scrollLeft : n.offset.left,
            u = e.left - t.collisionPosition.marginLeft,
            a = u - o,
            f = u + t.collisionWidth - s - o,
            l = t.my[0] === "left" ? -t.elemWidth : t.my[0] === "right" ? t.elemWidth : 0,
            c = t.at[0] === "left" ? t.targetWidth : t.at[0] === "right" ? -t.targetWidth : 0,
            h = -2 * t.offset[0],
            p,
            d;if (a < 0) {
          p = e.left + l + c + h + t.collisionWidth - s - r;if (p < 0 || p < i(a)) e.left += l + c + h;
        } else if (f > 0) {
          d = e.left - t.collisionPosition.marginLeft + l + c + h - o;if (d > 0 || i(d) < f) e.left += l + c + h;
        }
      }, top: function top(e, t) {
        var n = t.within,
            r = n.offset.top + n.scrollTop,
            s = n.height,
            o = n.isWindow ? n.scrollTop : n.offset.top,
            u = e.top - t.collisionPosition.marginTop,
            a = u - o,
            f = u + t.collisionHeight - s - o,
            l = t.my[1] === "top",
            c = l ? -t.elemHeight : t.my[1] === "bottom" ? t.elemHeight : 0,
            h = t.at[1] === "top" ? t.targetHeight : t.at[1] === "bottom" ? -t.targetHeight : 0,
            p = -2 * t.offset[1],
            d,
            v;a < 0 ? (v = e.top + c + h + p + t.collisionHeight - s - r, e.top + c + h + p > a && (v < 0 || v < i(a)) && (e.top += c + h + p)) : f > 0 && (d = e.top - t.collisionPosition.marginTop + c + h + p - o, e.top + c + h + p > f && (d > 0 || i(d) < f) && (e.top += c + h + p));
      } }, flipfit: { left: function left() {
        e.ui.position.flip.left.apply(this, arguments), e.ui.position.fit.left.apply(this, arguments);
      }, top: function top() {
        e.ui.position.flip.top.apply(this, arguments), e.ui.position.fit.top.apply(this, arguments);
      } } }, function () {
    var t,
        n,
        r,
        i,
        s,
        o = document.getElementsByTagName("body")[0],
        u = document.createElement("div");t = document.createElement(o ? "div" : "body"), r = { visibility: "hidden", width: 0, height: 0, border: 0, margin: 0, background: "none" }, o && e.extend(r, { position: "absolute", left: "-1000px", top: "-1000px" });for (s in r) {
      t.style[s] = r[s];
    }t.appendChild(u), n = o || document.documentElement, n.insertBefore(t, n.firstChild), u.style.cssText = "position: absolute; left: 10.7432222px;", i = e(u).offset().left, e.support.offsetFractions = i > 10 && i < 11, t.innerHTML = "", n.removeChild(t);
  }();
})(jQuery);(function (e, t) {
  e.widget("ui.draggable", e.ui.mouse, { version: "1.10.0", widgetEventPrefix: "drag", options: { addClasses: !0, appendTo: "parent", axis: !1, connectToSortable: !1, containment: !1, cursor: "auto", cursorAt: !1, grid: !1, handle: !1, helper: "original", iframeFix: !1, opacity: !1, refreshPositions: !1, revert: !1, revertDuration: 500, scope: "default", scroll: !0, scrollSensitivity: 20, scrollSpeed: 20, snap: !1, snapMode: "both", snapTolerance: 20, stack: !1, zIndex: !1, drag: null, start: null, stop: null }, _create: function _create() {
      this.options.helper === "original" && !/^(?:r|a|f)/.test(this.element.css("position")) && (this.element[0].style.position = "relative"), this.options.addClasses && this.element.addClass("ui-draggable"), this.options.disabled && this.element.addClass("ui-draggable-disabled"), this._mouseInit();
    }, _destroy: function _destroy() {
      this.element.removeClass("ui-draggable ui-draggable-dragging ui-draggable-disabled"), this._mouseDestroy();
    }, _mouseCapture: function _mouseCapture(t) {
      var n = this.options;return this.helper || n.disabled || e(t.target).closest(".ui-resizable-handle").length > 0 ? !1 : (this.handle = this._getHandle(t), this.handle ? (e(n.iframeFix === !0 ? "iframe" : n.iframeFix).each(function () {
        e("<div class='ui-draggable-iframeFix' style='background: #fff;'></div>").css({ width: this.offsetWidth + "px", height: this.offsetHeight + "px", position: "absolute", opacity: "0.001", zIndex: 1e3 }).css(e(this).offset()).appendTo("body");
      }), !0) : !1);
    }, _mouseStart: function _mouseStart(t) {
      var n = this.options;return this.helper = this._createHelper(t), this.helper.addClass("ui-draggable-dragging"), this._cacheHelperProportions(), e.ui.ddmanager && (e.ui.ddmanager.current = this), this._cacheMargins(), this.cssPosition = this.helper.css("position"), this.scrollParent = this.helper.scrollParent(), this.offset = this.positionAbs = this.element.offset(), this.offset = { top: this.offset.top - this.margins.top, left: this.offset.left - this.margins.left }, e.extend(this.offset, { click: { left: t.pageX - this.offset.left, top: t.pageY - this.offset.top }, parent: this._getParentOffset(), relative: this._getRelativeOffset() }), this.originalPosition = this.position = this._generatePosition(t), this.originalPageX = t.pageX, this.originalPageY = t.pageY, n.cursorAt && this._adjustOffsetFromHelper(n.cursorAt), n.containment && this._setContainment(), this._trigger("start", t) === !1 ? (this._clear(), !1) : (this._cacheHelperProportions(), e.ui.ddmanager && !n.dropBehaviour && e.ui.ddmanager.prepareOffsets(this, t), this._mouseDrag(t, !0), e.ui.ddmanager && e.ui.ddmanager.dragStart(this, t), !0);
    }, _mouseDrag: function _mouseDrag(t, n) {
      this.position = this._generatePosition(t), this.positionAbs = this._convertPositionTo("absolute");if (!n) {
        var r = this._uiHash();if (this._trigger("drag", t, r) === !1) return this._mouseUp({}), !1;this.position = r.position;
      }if (!this.options.axis || this.options.axis !== "y") this.helper[0].style.left = this.position.left + "px";if (!this.options.axis || this.options.axis !== "x") this.helper[0].style.top = this.position.top + "px";return e.ui.ddmanager && e.ui.ddmanager.drag(this, t), !1;
    }, _mouseStop: function _mouseStop(t) {
      var n,
          r = this,
          i = !1,
          s = !1;e.ui.ddmanager && !this.options.dropBehaviour && (s = e.ui.ddmanager.drop(this, t)), this.dropped && (s = this.dropped, this.dropped = !1), n = this.element[0];while (n && (n = n.parentNode)) {
        n === document && (i = !0);
      }return !i && this.options.helper === "original" ? !1 : (this.options.revert === "invalid" && !s || this.options.revert === "valid" && s || this.options.revert === !0 || e.isFunction(this.options.revert) && this.options.revert.call(this.element, s) ? e(this.helper).animate(this.originalPosition, parseInt(this.options.revertDuration, 10), function () {
        r._trigger("stop", t) !== !1 && r._clear();
      }) : this._trigger("stop", t) !== !1 && this._clear(), !1);
    }, _mouseUp: function _mouseUp(t) {
      return e("div.ui-draggable-iframeFix").each(function () {
        this.parentNode.removeChild(this);
      }), e.ui.ddmanager && e.ui.ddmanager.dragStop(this, t), e.ui.mouse.prototype._mouseUp.call(this, t);
    }, cancel: function cancel() {
      return this.helper.is(".ui-draggable-dragging") ? this._mouseUp({}) : this._clear(), this;
    }, _getHandle: function _getHandle(t) {
      var n = !this.options.handle || !e(this.options.handle, this.element).length ? !0 : !1;return e(this.options.handle, this.element).find("*").addBack().each(function () {
        this === t.target && (n = !0);
      }), n;
    }, _createHelper: function _createHelper(t) {
      var n = this.options,
          r = e.isFunction(n.helper) ? e(n.helper.apply(this.element[0], [t])) : n.helper === "clone" ? this.element.clone().removeAttr("id") : this.element;return r.parents("body").length || r.appendTo(n.appendTo === "parent" ? this.element[0].parentNode : n.appendTo), r[0] !== this.element[0] && !/(fixed|absolute)/.test(r.css("position")) && r.css("position", "absolute"), r;
    }, _adjustOffsetFromHelper: function _adjustOffsetFromHelper(t) {
      typeof t == "string" && (t = t.split(" ")), e.isArray(t) && (t = { left: +t[0], top: +t[1] || 0 }), "left" in t && (this.offset.click.left = t.left + this.margins.left), "right" in t && (this.offset.click.left = this.helperProportions.width - t.right + this.margins.left), "top" in t && (this.offset.click.top = t.top + this.margins.top), "bottom" in t && (this.offset.click.top = this.helperProportions.height - t.bottom + this.margins.top);
    }, _getParentOffset: function _getParentOffset() {
      this.offsetParent = this.helper.offsetParent();var t = this.offsetParent.offset();this.cssPosition === "absolute" && this.scrollParent[0] !== document && e.contains(this.scrollParent[0], this.offsetParent[0]) && (t.left += this.scrollParent.scrollLeft(), t.top += this.scrollParent.scrollTop());if (this.offsetParent[0] === document.body || this.offsetParent[0].tagName && this.offsetParent[0].tagName.toLowerCase() === "html" && e.ui.ie) t = { top: 0, left: 0 };return { top: t.top + (parseInt(this.offsetParent.css("borderTopWidth"), 10) || 0), left: t.left + (parseInt(this.offsetParent.css("borderLeftWidth"), 10) || 0) };
    }, _getRelativeOffset: function _getRelativeOffset() {
      if (this.cssPosition === "relative") {
        var e = this.element.position();return { top: e.top - (parseInt(this.helper.css("top"), 10) || 0) + this.scrollParent.scrollTop(), left: e.left - (parseInt(this.helper.css("left"), 10) || 0) + this.scrollParent.scrollLeft() };
      }return { top: 0, left: 0 };
    }, _cacheMargins: function _cacheMargins() {
      this.margins = { left: parseInt(this.element.css("marginLeft"), 10) || 0, top: parseInt(this.element.css("marginTop"), 10) || 0, right: parseInt(this.element.css("marginRight"), 10) || 0, bottom: parseInt(this.element.css("marginBottom"), 10) || 0 };
    }, _cacheHelperProportions: function _cacheHelperProportions() {
      this.helperProportions = { width: this.helper.outerWidth(), height: this.helper.outerHeight() };
    }, _setContainment: function _setContainment() {
      var t,
          n,
          r,
          i = this.options;i.containment === "parent" && (i.containment = this.helper[0].parentNode);if (i.containment === "document" || i.containment === "window") this.containment = [i.containment === "document" ? 0 : e(window).scrollLeft() - this.offset.relative.left - this.offset.parent.left, i.containment === "document" ? 0 : e(window).scrollTop() - this.offset.relative.top - this.offset.parent.top, (i.containment === "document" ? 0 : e(window).scrollLeft()) + e(i.containment === "document" ? document : window).width() - this.helperProportions.width - this.margins.left, (i.containment === "document" ? 0 : e(window).scrollTop()) + (e(i.containment === "document" ? document : window).height() || document.body.parentNode.scrollHeight) - this.helperProportions.height - this.margins.top];if (!/^(document|window|parent)$/.test(i.containment) && i.containment.constructor !== Array) {
        n = e(i.containment), r = n[0];if (!r) return;t = e(r).css("overflow") !== "hidden", this.containment = [(parseInt(e(r).css("borderLeftWidth"), 10) || 0) + (parseInt(e(r).css("paddingLeft"), 10) || 0), (parseInt(e(r).css("borderTopWidth"), 10) || 0) + (parseInt(e(r).css("paddingTop"), 10) || 0), (t ? Math.max(r.scrollWidth, r.offsetWidth) : r.offsetWidth) - (parseInt(e(r).css("borderLeftWidth"), 10) || 0) - (parseInt(e(r).css("paddingRight"), 10) || 0) - this.helperProportions.width - this.margins.left - this.margins.right, (t ? Math.max(r.scrollHeight, r.offsetHeight) : r.offsetHeight) - (parseInt(e(r).css("borderTopWidth"), 10) || 0) - (parseInt(e(r).css("paddingBottom"), 10) || 0) - this.helperProportions.height - this.margins.top - this.margins.bottom], this.relative_container = n;
      } else i.containment.constructor === Array && (this.containment = i.containment);
    }, _convertPositionTo: function _convertPositionTo(t, n) {
      n || (n = this.position);var r = t === "absolute" ? 1 : -1,
          i = this.cssPosition !== "absolute" || this.scrollParent[0] !== document && !!e.contains(this.scrollParent[0], this.offsetParent[0]) ? this.scrollParent : this.offsetParent,
          s = /(html|body)/i.test(i[0].tagName);return { top: n.top + this.offset.relative.top * r + this.offset.parent.top * r - (this.cssPosition === "fixed" ? -this.scrollParent.scrollTop() : s ? 0 : i.scrollTop()) * r, left: n.left + this.offset.relative.left * r + this.offset.parent.left * r - (this.cssPosition === "fixed" ? -this.scrollParent.scrollLeft() : s ? 0 : i.scrollLeft()) * r };
    }, _generatePosition: function _generatePosition(t) {
      var n,
          r,
          i,
          s,
          o = this.options,
          u = this.cssPosition !== "absolute" || this.scrollParent[0] !== document && !!e.contains(this.scrollParent[0], this.offsetParent[0]) ? this.scrollParent : this.offsetParent,
          a = /(html|body)/i.test(u[0].tagName),
          f = t.pageX,
          l = t.pageY;return this.originalPosition && (this.containment && (this.relative_container ? (r = this.relative_container.offset(), n = [this.containment[0] + r.left, this.containment[1] + r.top, this.containment[2] + r.left, this.containment[3] + r.top]) : n = this.containment, t.pageX - this.offset.click.left < n[0] && (f = n[0] + this.offset.click.left), t.pageY - this.offset.click.top < n[1] && (l = n[1] + this.offset.click.top), t.pageX - this.offset.click.left > n[2] && (f = n[2] + this.offset.click.left), t.pageY - this.offset.click.top > n[3] && (l = n[3] + this.offset.click.top)), o.grid && (i = o.grid[1] ? this.originalPageY + Math.round((l - this.originalPageY) / o.grid[1]) * o.grid[1] : this.originalPageY, l = n ? i - this.offset.click.top >= n[1] || i - this.offset.click.top > n[3] ? i : i - this.offset.click.top >= n[1] ? i - o.grid[1] : i + o.grid[1] : i, s = o.grid[0] ? this.originalPageX + Math.round((f - this.originalPageX) / o.grid[0]) * o.grid[0] : this.originalPageX, f = n ? s - this.offset.click.left >= n[0] || s - this.offset.click.left > n[2] ? s : s - this.offset.click.left >= n[0] ? s - o.grid[0] : s + o.grid[0] : s)), { top: l - this.offset.click.top - this.offset.relative.top - this.offset.parent.top + (this.cssPosition === "fixed" ? -this.scrollParent.scrollTop() : a ? 0 : u.scrollTop()), left: f - this.offset.click.left - this.offset.relative.left - this.offset.parent.left + (this.cssPosition === "fixed" ? -this.scrollParent.scrollLeft() : a ? 0 : u.scrollLeft()) };
    }, _clear: function _clear() {
      this.helper.removeClass("ui-draggable-dragging"), this.helper[0] !== this.element[0] && !this.cancelHelperRemoval && this.helper.remove(), this.helper = null, this.cancelHelperRemoval = !1;
    }, _trigger: function _trigger(t, n, r) {
      return r = r || this._uiHash(), e.ui.plugin.call(this, t, [n, r]), t === "drag" && (this.positionAbs = this._convertPositionTo("absolute")), e.Widget.prototype._trigger.call(this, t, n, r);
    }, plugins: {}, _uiHash: function _uiHash() {
      return { helper: this.helper, position: this.position, originalPosition: this.originalPosition, offset: this.positionAbs };
    } }), e.ui.plugin.add("draggable", "connectToSortable", { start: function start(t, n) {
      var r = e(this).data("ui-draggable"),
          i = r.options,
          s = e.extend({}, n, { item: r.element });r.sortables = [], e(i.connectToSortable).each(function () {
        var n = e.data(this, "ui-sortable");n && !n.options.disabled && (r.sortables.push({ instance: n, shouldRevert: n.options.revert }), n.refreshPositions(), n._trigger("activate", t, s));
      });
    }, stop: function stop(t, n) {
      var r = e(this).data("ui-draggable"),
          i = e.extend({}, n, { item: r.element });e.each(r.sortables, function () {
        this.instance.isOver ? (this.instance.isOver = 0, r.cancelHelperRemoval = !0, this.instance.cancelHelperRemoval = !1, this.shouldRevert && (this.instance.options.revert = !0), this.instance._mouseStop(t), this.instance.options.helper = this.instance.options._helper, r.options.helper === "original" && this.instance.currentItem.css({ top: "auto", left: "auto" })) : (this.instance.cancelHelperRemoval = !1, this.instance._trigger("deactivate", t, i));
      });
    }, drag: function drag(t, n) {
      var r = e(this).data("ui-draggable"),
          i = this;e.each(r.sortables, function () {
        var s = !1,
            o = this;this.instance.positionAbs = r.positionAbs, this.instance.helperProportions = r.helperProportions, this.instance.offset.click = r.offset.click, this.instance._intersectsWith(this.instance.containerCache) && (s = !0, e.each(r.sortables, function () {
          return this.instance.positionAbs = r.positionAbs, this.instance.helperProportions = r.helperProportions, this.instance.offset.click = r.offset.click, this !== o && this.instance._intersectsWith(this.instance.containerCache) && e.ui.contains(o.instance.element[0], this.instance.element[0]) && (s = !1), s;
        })), s ? (this.instance.isOver || (this.instance.isOver = 1, this.instance.currentItem = e(i).clone().removeAttr("id").appendTo(this.instance.element).data("ui-sortable-item", !0), this.instance.options._helper = this.instance.options.helper, this.instance.options.helper = function () {
          return n.helper[0];
        }, t.target = this.instance.currentItem[0], this.instance._mouseCapture(t, !0), this.instance._mouseStart(t, !0, !0), this.instance.offset.click.top = r.offset.click.top, this.instance.offset.click.left = r.offset.click.left, this.instance.offset.parent.left -= r.offset.parent.left - this.instance.offset.parent.left, this.instance.offset.parent.top -= r.offset.parent.top - this.instance.offset.parent.top, r._trigger("toSortable", t), r.dropped = this.instance.element, r.currentItem = r.element, this.instance.fromOutside = r), this.instance.currentItem && this.instance._mouseDrag(t)) : this.instance.isOver && (this.instance.isOver = 0, this.instance.cancelHelperRemoval = !0, this.instance.options.revert = !1, this.instance._trigger("out", t, this.instance._uiHash(this.instance)), this.instance._mouseStop(t, !0), this.instance.options.helper = this.instance.options._helper, this.instance.currentItem.remove(), this.instance.placeholder && this.instance.placeholder.remove(), r._trigger("fromSortable", t), r.dropped = !1);
      });
    } }), e.ui.plugin.add("draggable", "cursor", { start: function start() {
      var t = e("body"),
          n = e(this).data("ui-draggable").options;t.css("cursor") && (n._cursor = t.css("cursor")), t.css("cursor", n.cursor);
    }, stop: function stop() {
      var t = e(this).data("ui-draggable").options;t._cursor && e("body").css("cursor", t._cursor);
    } }), e.ui.plugin.add("draggable", "opacity", { start: function start(t, n) {
      var r = e(n.helper),
          i = e(this).data("ui-draggable").options;r.css("opacity") && (i._opacity = r.css("opacity")), r.css("opacity", i.opacity);
    }, stop: function stop(t, n) {
      var r = e(this).data("ui-draggable").options;r._opacity && e(n.helper).css("opacity", r._opacity);
    } }), e.ui.plugin.add("draggable", "scroll", { start: function start() {
      var t = e(this).data("ui-draggable");t.scrollParent[0] !== document && t.scrollParent[0].tagName !== "HTML" && (t.overflowOffset = t.scrollParent.offset());
    }, drag: function drag(t) {
      var n = e(this).data("ui-draggable"),
          r = n.options,
          i = !1;if (n.scrollParent[0] !== document && n.scrollParent[0].tagName !== "HTML") {
        if (!r.axis || r.axis !== "x") n.overflowOffset.top + n.scrollParent[0].offsetHeight - t.pageY < r.scrollSensitivity ? n.scrollParent[0].scrollTop = i = n.scrollParent[0].scrollTop + r.scrollSpeed : t.pageY - n.overflowOffset.top < r.scrollSensitivity && (n.scrollParent[0].scrollTop = i = n.scrollParent[0].scrollTop - r.scrollSpeed);if (!r.axis || r.axis !== "y") n.overflowOffset.left + n.scrollParent[0].offsetWidth - t.pageX < r.scrollSensitivity ? n.scrollParent[0].scrollLeft = i = n.scrollParent[0].scrollLeft + r.scrollSpeed : t.pageX - n.overflowOffset.left < r.scrollSensitivity && (n.scrollParent[0].scrollLeft = i = n.scrollParent[0].scrollLeft - r.scrollSpeed);
      } else {
        if (!r.axis || r.axis !== "x") t.pageY - e(document).scrollTop() < r.scrollSensitivity ? i = e(document).scrollTop(e(document).scrollTop() - r.scrollSpeed) : e(window).height() - (t.pageY - e(document).scrollTop()) < r.scrollSensitivity && (i = e(document).scrollTop(e(document).scrollTop() + r.scrollSpeed));if (!r.axis || r.axis !== "y") t.pageX - e(document).scrollLeft() < r.scrollSensitivity ? i = e(document).scrollLeft(e(document).scrollLeft() - r.scrollSpeed) : e(window).width() - (t.pageX - e(document).scrollLeft()) < r.scrollSensitivity && (i = e(document).scrollLeft(e(document).scrollLeft() + r.scrollSpeed));
      }i !== !1 && e.ui.ddmanager && !r.dropBehaviour && e.ui.ddmanager.prepareOffsets(n, t);
    } }), e.ui.plugin.add("draggable", "snap", { start: function start() {
      var t = e(this).data("ui-draggable"),
          n = t.options;t.snapElements = [], e(n.snap.constructor !== String ? n.snap.items || ":data(ui-draggable)" : n.snap).each(function () {
        var n = e(this),
            r = n.offset();this !== t.element[0] && t.snapElements.push({ item: this, width: n.outerWidth(), height: n.outerHeight(), top: r.top, left: r.left });
      });
    }, drag: function drag(t, n) {
      var r,
          i,
          s,
          o,
          u,
          a,
          f,
          l,
          c,
          h,
          p = e(this).data("ui-draggable"),
          d = p.options,
          v = d.snapTolerance,
          m = n.offset.left,
          g = m + p.helperProportions.width,
          y = n.offset.top,
          b = y + p.helperProportions.height;for (c = p.snapElements.length - 1; c >= 0; c--) {
        u = p.snapElements[c].left, a = u + p.snapElements[c].width, f = p.snapElements[c].top, l = f + p.snapElements[c].height;if (!(u - v < m && m < a + v && f - v < y && y < l + v || u - v < m && m < a + v && f - v < b && b < l + v || u - v < g && g < a + v && f - v < y && y < l + v || u - v < g && g < a + v && f - v < b && b < l + v)) {
          p.snapElements[c].snapping && p.options.snap.release && p.options.snap.release.call(p.element, t, e.extend(p._uiHash(), { snapItem: p.snapElements[c].item })), p.snapElements[c].snapping = !1;continue;
        }d.snapMode !== "inner" && (r = Math.abs(f - b) <= v, i = Math.abs(l - y) <= v, s = Math.abs(u - g) <= v, o = Math.abs(a - m) <= v, r && (n.position.top = p._convertPositionTo("relative", { top: f - p.helperProportions.height, left: 0 }).top - p.margins.top), i && (n.position.top = p._convertPositionTo("relative", { top: l, left: 0 }).top - p.margins.top), s && (n.position.left = p._convertPositionTo("relative", { top: 0, left: u - p.helperProportions.width }).left - p.margins.left), o && (n.position.left = p._convertPositionTo("relative", { top: 0, left: a }).left - p.margins.left)), h = r || i || s || o, d.snapMode !== "outer" && (r = Math.abs(f - y) <= v, i = Math.abs(l - b) <= v, s = Math.abs(u - m) <= v, o = Math.abs(a - g) <= v, r && (n.position.top = p._convertPositionTo("relative", { top: f, left: 0 }).top - p.margins.top), i && (n.position.top = p._convertPositionTo("relative", { top: l - p.helperProportions.height, left: 0 }).top - p.margins.top), s && (n.position.left = p._convertPositionTo("relative", { top: 0, left: u }).left - p.margins.left), o && (n.position.left = p._convertPositionTo("relative", { top: 0, left: a - p.helperProportions.width }).left - p.margins.left)), !p.snapElements[c].snapping && (r || i || s || o || h) && p.options.snap.snap && p.options.snap.snap.call(p.element, t, e.extend(p._uiHash(), { snapItem: p.snapElements[c].item })), p.snapElements[c].snapping = r || i || s || o || h;
      }
    } }), e.ui.plugin.add("draggable", "stack", { start: function start() {
      var t,
          n = e(this).data("ui-draggable").options,
          r = e.makeArray(e(n.stack)).sort(function (t, n) {
        return (parseInt(e(t).css("zIndex"), 10) || 0) - (parseInt(e(n).css("zIndex"), 10) || 0);
      });if (!r.length) return;t = parseInt(r[0].style.zIndex, 10) || 0, e(r).each(function (e) {
        this.style.zIndex = t + e;
      }), this[0].style.zIndex = t + r.length;
    } }), e.ui.plugin.add("draggable", "zIndex", { start: function start(t, n) {
      var r = e(n.helper),
          i = e(this).data("ui-draggable").options;r.css("zIndex") && (i._zIndex = r.css("zIndex")), r.css("zIndex", i.zIndex);
    }, stop: function stop(t, n) {
      var r = e(this).data("ui-draggable").options;r._zIndex && e(n.helper).css("zIndex", r._zIndex);
    } });
})(jQuery);(function (e, t) {
  function n(e, t, n) {
    return e > t && e < t + n;
  }e.widget("ui.droppable", { version: "1.10.0", widgetEventPrefix: "drop", options: { accept: "*", activeClass: !1, addClasses: !0, greedy: !1, hoverClass: !1, scope: "default", tolerance: "intersect", activate: null, deactivate: null, drop: null, out: null, over: null }, _create: function _create() {
      var t = this.options,
          n = t.accept;this.isover = !1, this.isout = !0, this.accept = e.isFunction(n) ? n : function (e) {
        return e.is(n);
      }, this.proportions = { width: this.element[0].offsetWidth, height: this.element[0].offsetHeight }, e.ui.ddmanager.droppables[t.scope] = e.ui.ddmanager.droppables[t.scope] || [], e.ui.ddmanager.droppables[t.scope].push(this), t.addClasses && this.element.addClass("ui-droppable");
    }, _destroy: function _destroy() {
      var t = 0,
          n = e.ui.ddmanager.droppables[this.options.scope];for (; t < n.length; t++) {
        n[t] === this && n.splice(t, 1);
      }this.element.removeClass("ui-droppable ui-droppable-disabled");
    }, _setOption: function _setOption(t, n) {
      t === "accept" && (this.accept = e.isFunction(n) ? n : function (e) {
        return e.is(n);
      }), e.Widget.prototype._setOption.apply(this, arguments);
    }, _activate: function _activate(t) {
      var n = e.ui.ddmanager.current;this.options.activeClass && this.element.addClass(this.options.activeClass), n && this._trigger("activate", t, this.ui(n));
    }, _deactivate: function _deactivate(t) {
      var n = e.ui.ddmanager.current;this.options.activeClass && this.element.removeClass(this.options.activeClass), n && this._trigger("deactivate", t, this.ui(n));
    }, _over: function _over(t) {
      var n = e.ui.ddmanager.current;if (!n || (n.currentItem || n.element)[0] === this.element[0]) return;this.accept.call(this.element[0], n.currentItem || n.element) && (this.options.hoverClass && this.element.addClass(this.options.hoverClass), this._trigger("over", t, this.ui(n)));
    }, _out: function _out(t) {
      var n = e.ui.ddmanager.current;if (!n || (n.currentItem || n.element)[0] === this.element[0]) return;this.accept.call(this.element[0], n.currentItem || n.element) && (this.options.hoverClass && this.element.removeClass(this.options.hoverClass), this._trigger("out", t, this.ui(n)));
    }, _drop: function _drop(t, n) {
      var r = n || e.ui.ddmanager.current,
          i = !1;return !r || (r.currentItem || r.element)[0] === this.element[0] ? !1 : (this.element.find(":data(ui-droppable)").not(".ui-draggable-dragging").each(function () {
        var t = e.data(this, "ui-droppable");if (t.options.greedy && !t.options.disabled && t.options.scope === r.options.scope && t.accept.call(t.element[0], r.currentItem || r.element) && e.ui.intersect(r, e.extend(t, { offset: t.element.offset() }), t.options.tolerance)) return i = !0, !1;
      }), i ? !1 : this.accept.call(this.element[0], r.currentItem || r.element) ? (this.options.activeClass && this.element.removeClass(this.options.activeClass), this.options.hoverClass && this.element.removeClass(this.options.hoverClass), this._trigger("drop", t, this.ui(r)), this.element) : !1);
    }, ui: function ui(e) {
      return { draggable: e.currentItem || e.element, helper: e.helper, position: e.position, offset: e.positionAbs };
    } }), e.ui.intersect = function (e, t, r) {
    if (!t.offset) return !1;var i,
        s,
        o = (e.positionAbs || e.position.absolute).left,
        u = o + e.helperProportions.width,
        a = (e.positionAbs || e.position.absolute).top,
        f = a + e.helperProportions.height,
        l = t.offset.left,
        c = l + t.proportions.width,
        h = t.offset.top,
        p = h + t.proportions.height;switch (r) {case "fit":
        return l <= o && u <= c && h <= a && f <= p;case "intersect":
        return l < o + e.helperProportions.width / 2 && u - e.helperProportions.width / 2 < c && h < a + e.helperProportions.height / 2 && f - e.helperProportions.height / 2 < p;case "pointer":
        return i = (e.positionAbs || e.position.absolute).left + (e.clickOffset || e.offset.click).left, s = (e.positionAbs || e.position.absolute).top + (e.clickOffset || e.offset.click).top, n(s, h, t.proportions.height) && n(i, l, t.proportions.width);case "touch":
        return (a >= h && a <= p || f >= h && f <= p || a < h && f > p) && (o >= l && o <= c || u >= l && u <= c || o < l && u > c);default:
        return !1;}
  }, e.ui.ddmanager = { current: null, droppables: { "default": [] }, prepareOffsets: function prepareOffsets(t, n) {
      var r,
          i,
          s = e.ui.ddmanager.droppables[t.options.scope] || [],
          o = n ? n.type : null,
          u = (t.currentItem || t.element).find(":data(ui-droppable)").addBack();e: for (r = 0; r < s.length; r++) {
        if (s[r].options.disabled || t && !s[r].accept.call(s[r].element[0], t.currentItem || t.element)) continue;for (i = 0; i < u.length; i++) {
          if (u[i] === s[r].element[0]) {
            s[r].proportions.height = 0;continue e;
          }
        }s[r].visible = s[r].element.css("display") !== "none";if (!s[r].visible) continue;o === "mousedown" && s[r]._activate.call(s[r], n), s[r].offset = s[r].element.offset(), s[r].proportions = { width: s[r].element[0].offsetWidth, height: s[r].element[0].offsetHeight };
      }
    }, drop: function drop(t, n) {
      var r = !1;return e.each(e.ui.ddmanager.droppables[t.options.scope] || [], function () {
        if (!this.options) return;!this.options.disabled && this.visible && e.ui.intersect(t, this, this.options.tolerance) && (r = this._drop.call(this, n) || r), !this.options.disabled && this.visible && this.accept.call(this.element[0], t.currentItem || t.element) && (this.isout = !0, this.isover = !1, this._deactivate.call(this, n));
      }), r;
    }, dragStart: function dragStart(t, n) {
      t.element.parentsUntil("body").bind("scroll.droppable", function () {
        t.options.refreshPositions || e.ui.ddmanager.prepareOffsets(t, n);
      });
    }, drag: function drag(t, n) {
      t.options.refreshPositions && e.ui.ddmanager.prepareOffsets(t, n), e.each(e.ui.ddmanager.droppables[t.options.scope] || [], function () {
        if (this.options.disabled || this.greedyChild || !this.visible) return;var r,
            i,
            s,
            o = e.ui.intersect(t, this, this.options.tolerance),
            u = !o && this.isover ? "isout" : o && !this.isover ? "isover" : null;if (!u) return;this.options.greedy && (i = this.options.scope, s = this.element.parents(":data(ui-droppable)").filter(function () {
          return e.data(this, "ui-droppable").options.scope === i;
        }), s.length && (r = e.data(s[0], "ui-droppable"), r.greedyChild = u === "isover")), r && u === "isover" && (r.isover = !1, r.isout = !0, r._out.call(r, n)), this[u] = !0, this[u === "isout" ? "isover" : "isout"] = !1, this[u === "isover" ? "_over" : "_out"].call(this, n), r && u === "isout" && (r.isout = !1, r.isover = !0, r._over.call(r, n));
      });
    }, dragStop: function dragStop(t, n) {
      t.element.parentsUntil("body").unbind("scroll.droppable"), t.options.refreshPositions || e.ui.ddmanager.prepareOffsets(t, n);
    } };
})(jQuery);(function (e, t) {
  function n(e) {
    return parseInt(e, 10) || 0;
  }function r(e) {
    return !isNaN(parseInt(e, 10));
  }e.widget("ui.resizable", e.ui.mouse, { version: "1.10.0", widgetEventPrefix: "resize", options: { alsoResize: !1, animate: !1, animateDuration: "slow", animateEasing: "swing", aspectRatio: !1, autoHide: !1, containment: !1, ghost: !1, grid: !1, handles: "e,s,se", helper: !1, maxHeight: null, maxWidth: null, minHeight: 10, minWidth: 10, zIndex: 90, resize: null, start: null, stop: null }, _create: function _create() {
      var t,
          n,
          r,
          i,
          s,
          o = this,
          u = this.options;this.element.addClass("ui-resizable"), e.extend(this, { _aspectRatio: !!u.aspectRatio, aspectRatio: u.aspectRatio, originalElement: this.element, _proportionallyResizeElements: [], _helper: u.helper || u.ghost || u.animate ? u.helper || "ui-resizable-helper" : null }), this.element[0].nodeName.match(/canvas|textarea|input|select|button|img/i) && (this.element.wrap(e("<div class='ui-wrapper' style='overflow: hidden;'></div>").css({ position: this.element.css("position"), width: this.element.outerWidth(), height: this.element.outerHeight(), top: this.element.css("top"), left: this.element.css("left") })), this.element = this.element.parent().data("ui-resizable", this.element.data("ui-resizable")), this.elementIsWrapper = !0, this.element.css({ marginLeft: this.originalElement.css("marginLeft"), marginTop: this.originalElement.css("marginTop"), marginRight: this.originalElement.css("marginRight"), marginBottom: this.originalElement.css("marginBottom") }), this.originalElement.css({ marginLeft: 0, marginTop: 0, marginRight: 0, marginBottom: 0 }), this.originalResizeStyle = this.originalElement.css("resize"), this.originalElement.css("resize", "none"), this._proportionallyResizeElements.push(this.originalElement.css({ position: "static", zoom: 1, display: "block" })), this.originalElement.css({ margin: this.originalElement.css("margin") }), this._proportionallyResize()), this.handles = u.handles || (e(".ui-resizable-handle", this.element).length ? { n: ".ui-resizable-n", e: ".ui-resizable-e", s: ".ui-resizable-s", w: ".ui-resizable-w", se: ".ui-resizable-se", sw: ".ui-resizable-sw", ne: ".ui-resizable-ne", nw: ".ui-resizable-nw" } : "e,s,se");if (this.handles.constructor === String) {
        this.handles === "all" && (this.handles = "n,e,s,w,se,sw,ne,nw"), t = this.handles.split(","), this.handles = {};for (n = 0; n < t.length; n++) {
          r = e.trim(t[n]), s = "ui-resizable-" + r, i = e("<div class='ui-resizable-handle " + s + "'></div>"), i.css({ zIndex: u.zIndex }), "se" === r && i.addClass("ui-icon ui-icon-gripsmall-diagonal-se"), this.handles[r] = ".ui-resizable-" + r, this.element.append(i);
        }
      }this._renderAxis = function (t) {
        var n, r, i, s;t = t || this.element;for (n in this.handles) {
          this.handles[n].constructor === String && (this.handles[n] = e(this.handles[n], this.element).show()), this.elementIsWrapper && this.originalElement[0].nodeName.match(/textarea|input|select|button/i) && (r = e(this.handles[n], this.element), s = /sw|ne|nw|se|n|s/.test(n) ? r.outerHeight() : r.outerWidth(), i = ["padding", /ne|nw|n/.test(n) ? "Top" : /se|sw|s/.test(n) ? "Bottom" : /^e$/.test(n) ? "Right" : "Left"].join(""), t.css(i, s), this._proportionallyResize());if (!e(this.handles[n]).length) continue;
        }
      }, this._renderAxis(this.element), this._handles = e(".ui-resizable-handle", this.element).disableSelection(), this._handles.mouseover(function () {
        o.resizing || (this.className && (i = this.className.match(/ui-resizable-(se|sw|ne|nw|n|e|s|w)/i)), o.axis = i && i[1] ? i[1] : "se");
      }), u.autoHide && (this._handles.hide(), e(this.element).addClass("ui-resizable-autohide").mouseenter(function () {
        if (u.disabled) return;e(this).removeClass("ui-resizable-autohide"), o._handles.show();
      }).mouseleave(function () {
        if (u.disabled) return;o.resizing || (e(this).addClass("ui-resizable-autohide"), o._handles.hide());
      })), this._mouseInit();
    }, _destroy: function _destroy() {
      this._mouseDestroy();var t,
          n = function n(t) {
        e(t).removeClass("ui-resizable ui-resizable-disabled ui-resizable-resizing").removeData("resizable").removeData("ui-resizable").unbind(".resizable").find(".ui-resizable-handle").remove();
      };return this.elementIsWrapper && (n(this.element), t = this.element, this.originalElement.css({ position: t.css("position"), width: t.outerWidth(), height: t.outerHeight(), top: t.css("top"), left: t.css("left") }).insertAfter(t), t.remove()), this.originalElement.css("resize", this.originalResizeStyle), n(this.originalElement), this;
    }, _mouseCapture: function _mouseCapture(t) {
      var n,
          r,
          i = !1;for (n in this.handles) {
        r = e(this.handles[n])[0];if (r === t.target || e.contains(r, t.target)) i = !0;
      }return !this.options.disabled && i;
    }, _mouseStart: function _mouseStart(t) {
      var r,
          i,
          s,
          o = this.options,
          u = this.element.position(),
          a = this.element;return this.resizing = !0, /absolute/.test(a.css("position")) ? a.css({ position: "absolute", top: a.css("top"), left: a.css("left") }) : a.is(".ui-draggable") && a.css({ position: "absolute", top: u.top, left: u.left }), this._renderProxy(), r = n(this.helper.css("left")), i = n(this.helper.css("top")), o.containment && (r += e(o.containment).scrollLeft() || 0, i += e(o.containment).scrollTop() || 0), this.offset = this.helper.offset(), this.position = { left: r, top: i }, this.size = this._helper ? { width: a.outerWidth(), height: a.outerHeight() } : { width: a.width(), height: a.height() }, this.originalSize = this._helper ? { width: a.outerWidth(), height: a.outerHeight() } : { width: a.width(), height: a.height() }, this.originalPosition = { left: r, top: i }, this.sizeDiff = { width: a.outerWidth() - a.width(), height: a.outerHeight() - a.height() }, this.originalMousePosition = { left: t.pageX, top: t.pageY }, this.aspectRatio = typeof o.aspectRatio == "number" ? o.aspectRatio : this.originalSize.width / this.originalSize.height || 1, s = e(".ui-resizable-" + this.axis).css("cursor"), e("body").css("cursor", s === "auto" ? this.axis + "-resize" : s), a.addClass("ui-resizable-resizing"), this._propagate("start", t), !0;
    }, _mouseDrag: function _mouseDrag(t) {
      var n,
          r = this.helper,
          i = {},
          s = this.originalMousePosition,
          o = this.axis,
          u = this.position.top,
          a = this.position.left,
          f = this.size.width,
          l = this.size.height,
          c = t.pageX - s.left || 0,
          h = t.pageY - s.top || 0,
          p = this._change[o];if (!p) return !1;n = p.apply(this, [t, c, h]), this._updateVirtualBoundaries(t.shiftKey);if (this._aspectRatio || t.shiftKey) n = this._updateRatio(n, t);return n = this._respectSize(n, t), this._updateCache(n), this._propagate("resize", t), this.position.top !== u && (i.top = this.position.top + "px"), this.position.left !== a && (i.left = this.position.left + "px"), this.size.width !== f && (i.width = this.size.width + "px"), this.size.height !== l && (i.height = this.size.height + "px"), r.css(i), !this._helper && this._proportionallyResizeElements.length && this._proportionallyResize(), e.isEmptyObject(i) || this._trigger("resize", t, this.ui()), !1;
    }, _mouseStop: function _mouseStop(t) {
      this.resizing = !1;var n,
          r,
          i,
          s,
          o,
          u,
          a,
          f = this.options,
          l = this;return this._helper && (n = this._proportionallyResizeElements, r = n.length && /textarea/i.test(n[0].nodeName), i = r && e.ui.hasScroll(n[0], "left") ? 0 : l.sizeDiff.height, s = r ? 0 : l.sizeDiff.width, o = { width: l.helper.width() - s, height: l.helper.height() - i }, u = parseInt(l.element.css("left"), 10) + (l.position.left - l.originalPosition.left) || null, a = parseInt(l.element.css("top"), 10) + (l.position.top - l.originalPosition.top) || null, f.animate || this.element.css(e.extend(o, { top: a, left: u })), l.helper.height(l.size.height), l.helper.width(l.size.width), this._helper && !f.animate && this._proportionallyResize()), e("body").css("cursor", "auto"), this.element.removeClass("ui-resizable-resizing"), this._propagate("stop", t), this._helper && this.helper.remove(), !1;
    }, _updateVirtualBoundaries: function _updateVirtualBoundaries(e) {
      var t,
          n,
          i,
          s,
          o,
          u = this.options;o = { minWidth: r(u.minWidth) ? u.minWidth : 0, maxWidth: r(u.maxWidth) ? u.maxWidth : Infinity, minHeight: r(u.minHeight) ? u.minHeight : 0, maxHeight: r(u.maxHeight) ? u.maxHeight : Infinity };if (this._aspectRatio || e) t = o.minHeight * this.aspectRatio, i = o.minWidth / this.aspectRatio, n = o.maxHeight * this.aspectRatio, s = o.maxWidth / this.aspectRatio, t > o.minWidth && (o.minWidth = t), i > o.minHeight && (o.minHeight = i), n < o.maxWidth && (o.maxWidth = n), s < o.maxHeight && (o.maxHeight = s);this._vBoundaries = o;
    }, _updateCache: function _updateCache(e) {
      this.offset = this.helper.offset(), r(e.left) && (this.position.left = e.left), r(e.top) && (this.position.top = e.top), r(e.height) && (this.size.height = e.height), r(e.width) && (this.size.width = e.width);
    }, _updateRatio: function _updateRatio(e) {
      var t = this.position,
          n = this.size,
          i = this.axis;return r(e.height) ? e.width = e.height * this.aspectRatio : r(e.width) && (e.height = e.width / this.aspectRatio), i === "sw" && (e.left = t.left + (n.width - e.width), e.top = null), i === "nw" && (e.top = t.top + (n.height - e.height), e.left = t.left + (n.width - e.width)), e;
    }, _respectSize: function _respectSize(e) {
      var t = this._vBoundaries,
          n = this.axis,
          i = r(e.width) && t.maxWidth && t.maxWidth < e.width,
          s = r(e.height) && t.maxHeight && t.maxHeight < e.height,
          o = r(e.width) && t.minWidth && t.minWidth > e.width,
          u = r(e.height) && t.minHeight && t.minHeight > e.height,
          a = this.originalPosition.left + this.originalSize.width,
          f = this.position.top + this.size.height,
          l = /sw|nw|w/.test(n),
          c = /nw|ne|n/.test(n);return o && (e.width = t.minWidth), u && (e.height = t.minHeight), i && (e.width = t.maxWidth), s && (e.height = t.maxHeight), o && l && (e.left = a - t.minWidth), i && l && (e.left = a - t.maxWidth), u && c && (e.top = f - t.minHeight), s && c && (e.top = f - t.maxHeight), !e.width && !e.height && !e.left && e.top ? e.top = null : !e.width && !e.height && !e.top && e.left && (e.left = null), e;
    }, _proportionallyResize: function _proportionallyResize() {
      if (!this._proportionallyResizeElements.length) return;var e,
          t,
          n,
          r,
          i,
          s = this.helper || this.element;for (e = 0; e < this._proportionallyResizeElements.length; e++) {
        i = this._proportionallyResizeElements[e];if (!this.borderDif) {
          this.borderDif = [], n = [i.css("borderTopWidth"), i.css("borderRightWidth"), i.css("borderBottomWidth"), i.css("borderLeftWidth")], r = [i.css("paddingTop"), i.css("paddingRight"), i.css("paddingBottom"), i.css("paddingLeft")];for (t = 0; t < n.length; t++) {
            this.borderDif[t] = (parseInt(n[t], 10) || 0) + (parseInt(r[t], 10) || 0);
          }
        }i.css({ height: s.height() - this.borderDif[0] - this.borderDif[2] || 0, width: s.width() - this.borderDif[1] - this.borderDif[3] || 0 });
      }
    }, _renderProxy: function _renderProxy() {
      var t = this.element,
          n = this.options;this.elementOffset = t.offset(), this._helper ? (this.helper = this.helper || e("<div style='overflow:hidden;'></div>"), this.helper.addClass(this._helper).css({ width: this.element.outerWidth() - 1, height: this.element.outerHeight() - 1, position: "absolute", left: this.elementOffset.left + "px", top: this.elementOffset.top + "px", zIndex: ++n.zIndex }), this.helper.appendTo("body").disableSelection()) : this.helper = this.element;
    }, _change: { e: function e(_e, t) {
        return { width: this.originalSize.width + t };
      }, w: function w(e, t) {
        var n = this.originalSize,
            r = this.originalPosition;return { left: r.left + t, width: n.width - t };
      }, n: function n(e, t, _n) {
        var r = this.originalSize,
            i = this.originalPosition;return { top: i.top + _n, height: r.height - _n };
      }, s: function s(e, t, n) {
        return { height: this.originalSize.height + n };
      }, se: function se(t, n, r) {
        return e.extend(this._change.s.apply(this, arguments), this._change.e.apply(this, [t, n, r]));
      }, sw: function sw(t, n, r) {
        return e.extend(this._change.s.apply(this, arguments), this._change.w.apply(this, [t, n, r]));
      }, ne: function ne(t, n, r) {
        return e.extend(this._change.n.apply(this, arguments), this._change.e.apply(this, [t, n, r]));
      }, nw: function nw(t, n, r) {
        return e.extend(this._change.n.apply(this, arguments), this._change.w.apply(this, [t, n, r]));
      } }, _propagate: function _propagate(t, n) {
      e.ui.plugin.call(this, t, [n, this.ui()]), t !== "resize" && this._trigger(t, n, this.ui());
    }, plugins: {}, ui: function ui() {
      return { originalElement: this.originalElement, element: this.element, helper: this.helper, position: this.position, size: this.size, originalSize: this.originalSize, originalPosition: this.originalPosition };
    } }), e.ui.plugin.add("resizable", "animate", { stop: function stop(t) {
      var n = e(this).data("ui-resizable"),
          r = n.options,
          i = n._proportionallyResizeElements,
          s = i.length && /textarea/i.test(i[0].nodeName),
          o = s && e.ui.hasScroll(i[0], "left") ? 0 : n.sizeDiff.height,
          u = s ? 0 : n.sizeDiff.width,
          a = { width: n.size.width - u, height: n.size.height - o },
          f = parseInt(n.element.css("left"), 10) + (n.position.left - n.originalPosition.left) || null,
          l = parseInt(n.element.css("top"), 10) + (n.position.top - n.originalPosition.top) || null;n.element.animate(e.extend(a, l && f ? { top: l, left: f } : {}), { duration: r.animateDuration, easing: r.animateEasing, step: function step() {
          var r = { width: parseInt(n.element.css("width"), 10), height: parseInt(n.element.css("height"), 10), top: parseInt(n.element.css("top"), 10), left: parseInt(n.element.css("left"), 10) };i && i.length && e(i[0]).css({ width: r.width, height: r.height }), n._updateCache(r), n._propagate("resize", t);
        } });
    } }), e.ui.plugin.add("resizable", "containment", { start: function start() {
      var t,
          r,
          i,
          s,
          o,
          u,
          a,
          f = e(this).data("ui-resizable"),
          l = f.options,
          c = f.element,
          h = l.containment,
          p = h instanceof e ? h.get(0) : /parent/.test(h) ? c.parent().get(0) : h;if (!p) return;f.containerElement = e(p), /document/.test(h) || h === document ? (f.containerOffset = { left: 0, top: 0 }, f.containerPosition = { left: 0, top: 0 }, f.parentData = { element: e(document), left: 0, top: 0, width: e(document).width(), height: e(document).height() || document.body.parentNode.scrollHeight }) : (t = e(p), r = [], e(["Top", "Right", "Left", "Bottom"]).each(function (e, i) {
        r[e] = n(t.css("padding" + i));
      }), f.containerOffset = t.offset(), f.containerPosition = t.position(), f.containerSize = { height: t.innerHeight() - r[3], width: t.innerWidth() - r[1] }, i = f.containerOffset, s = f.containerSize.height, o = f.containerSize.width, u = e.ui.hasScroll(p, "left") ? p.scrollWidth : o, a = e.ui.hasScroll(p) ? p.scrollHeight : s, f.parentData = { element: p, left: i.left, top: i.top, width: u, height: a });
    }, resize: function resize(t) {
      var n,
          r,
          i,
          s,
          o = e(this).data("ui-resizable"),
          u = o.options,
          a = o.containerOffset,
          f = o.position,
          l = o._aspectRatio || t.shiftKey,
          c = { top: 0, left: 0 },
          h = o.containerElement;h[0] !== document && /static/.test(h.css("position")) && (c = a), f.left < (o._helper ? a.left : 0) && (o.size.width = o.size.width + (o._helper ? o.position.left - a.left : o.position.left - c.left), l && (o.size.height = o.size.width / o.aspectRatio), o.position.left = u.helper ? a.left : 0), f.top < (o._helper ? a.top : 0) && (o.size.height = o.size.height + (o._helper ? o.position.top - a.top : o.position.top), l && (o.size.width = o.size.height * o.aspectRatio), o.position.top = o._helper ? a.top : 0), o.offset.left = o.parentData.left + o.position.left, o.offset.top = o.parentData.top + o.position.top, n = Math.abs((o._helper ? o.offset.left - c.left : o.offset.left - c.left) + o.sizeDiff.width), r = Math.abs((o._helper ? o.offset.top - c.top : o.offset.top - a.top) + o.sizeDiff.height), i = o.containerElement.get(0) === o.element.parent().get(0), s = /relative|absolute/.test(o.containerElement.css("position")), i && s && (n -= o.parentData.left), n + o.size.width >= o.parentData.width && (o.size.width = o.parentData.width - n, l && (o.size.height = o.size.width / o.aspectRatio)), r + o.size.height >= o.parentData.height && (o.size.height = o.parentData.height - r, l && (o.size.width = o.size.height * o.aspectRatio));
    }, stop: function stop() {
      var t = e(this).data("ui-resizable"),
          n = t.options,
          r = t.containerOffset,
          i = t.containerPosition,
          s = t.containerElement,
          o = e(t.helper),
          u = o.offset(),
          a = o.outerWidth() - t.sizeDiff.width,
          f = o.outerHeight() - t.sizeDiff.height;t._helper && !n.animate && /relative/.test(s.css("position")) && e(this).css({ left: u.left - i.left - r.left, width: a, height: f }), t._helper && !n.animate && /static/.test(s.css("position")) && e(this).css({ left: u.left - i.left - r.left, width: a, height: f });
    } }), e.ui.plugin.add("resizable", "alsoResize", { start: function start() {
      var t = e(this).data("ui-resizable"),
          n = t.options,
          r = function r(t) {
        e(t).each(function () {
          var t = e(this);t.data("ui-resizable-alsoresize", { width: parseInt(t.width(), 10), height: parseInt(t.height(), 10), left: parseInt(t.css("left"), 10), top: parseInt(t.css("top"), 10) });
        });
      };_typeof(n.alsoResize) == "object" && !n.alsoResize.parentNode ? n.alsoResize.length ? (n.alsoResize = n.alsoResize[0], r(n.alsoResize)) : e.each(n.alsoResize, function (e) {
        r(e);
      }) : r(n.alsoResize);
    }, resize: function resize(t, n) {
      var r = e(this).data("ui-resizable"),
          i = r.options,
          s = r.originalSize,
          o = r.originalPosition,
          u = { height: r.size.height - s.height || 0, width: r.size.width - s.width || 0, top: r.position.top - o.top || 0, left: r.position.left - o.left || 0 },
          a = function a(t, r) {
        e(t).each(function () {
          var t = e(this),
              i = e(this).data("ui-resizable-alsoresize"),
              s = {},
              o = r && r.length ? r : t.parents(n.originalElement[0]).length ? ["width", "height"] : ["width", "height", "top", "left"];e.each(o, function (e, t) {
            var n = (i[t] || 0) + (u[t] || 0);n && n >= 0 && (s[t] = n || null);
          }), t.css(s);
        });
      };_typeof(i.alsoResize) == "object" && !i.alsoResize.nodeType ? e.each(i.alsoResize, function (e, t) {
        a(e, t);
      }) : a(i.alsoResize);
    }, stop: function stop() {
      e(this).removeData("resizable-alsoresize");
    } }), e.ui.plugin.add("resizable", "ghost", { start: function start() {
      var t = e(this).data("ui-resizable"),
          n = t.options,
          r = t.size;t.ghost = t.originalElement.clone(), t.ghost.css({ opacity: .25, display: "block", position: "relative", height: r.height, width: r.width, margin: 0, left: 0, top: 0 }).addClass("ui-resizable-ghost").addClass(typeof n.ghost == "string" ? n.ghost : ""), t.ghost.appendTo(t.helper);
    }, resize: function resize() {
      var t = e(this).data("ui-resizable");t.ghost && t.ghost.css({ position: "relative", height: t.size.height, width: t.size.width });
    }, stop: function stop() {
      var t = e(this).data("ui-resizable");t.ghost && t.helper && t.helper.get(0).removeChild(t.ghost.get(0));
    } }), e.ui.plugin.add("resizable", "grid", { resize: function resize() {
      var t = e(this).data("ui-resizable"),
          n = t.options,
          r = t.size,
          i = t.originalSize,
          s = t.originalPosition,
          o = t.axis,
          u = typeof n.grid == "number" ? [n.grid, n.grid] : n.grid,
          a = u[0] || 1,
          f = u[1] || 1,
          l = Math.round((r.width - i.width) / a) * a,
          c = Math.round((r.height - i.height) / f) * f,
          h = i.width + l,
          p = i.height + c,
          d = n.maxWidth && n.maxWidth < h,
          v = n.maxHeight && n.maxHeight < p,
          m = n.minWidth && n.minWidth > h,
          g = n.minHeight && n.minHeight > p;n.grid = u, m && (h += a), g && (p += f), d && (h -= a), v && (p -= f), /^(se|s|e)$/.test(o) ? (t.size.width = h, t.size.height = p) : /^(ne)$/.test(o) ? (t.size.width = h, t.size.height = p, t.position.top = s.top - c) : /^(sw)$/.test(o) ? (t.size.width = h, t.size.height = p, t.position.left = s.left - l) : (t.size.width = h, t.size.height = p, t.position.top = s.top - c, t.position.left = s.left - l);
    } });
})(jQuery);(function (e, t) {
  e.widget("ui.selectable", e.ui.mouse, { version: "1.10.0", options: { appendTo: "body", autoRefresh: !0, distance: 0, filter: "*", tolerance: "touch", selected: null, selecting: null, start: null, stop: null, unselected: null, unselecting: null }, _create: function _create() {
      var t,
          n = this;this.element.addClass("ui-selectable"), this.dragged = !1, this.refresh = function () {
        t = e(n.options.filter, n.element[0]), t.addClass("ui-selectee"), t.each(function () {
          var t = e(this),
              n = t.offset();e.data(this, "selectable-item", { element: this, $element: t, left: n.left, top: n.top, right: n.left + t.outerWidth(), bottom: n.top + t.outerHeight(), startselected: !1, selected: t.hasClass("ui-selected"), selecting: t.hasClass("ui-selecting"), unselecting: t.hasClass("ui-unselecting") });
        });
      }, this.refresh(), this.selectees = t.addClass("ui-selectee"), this._mouseInit(), this.helper = e("<div class='ui-selectable-helper'></div>");
    }, _destroy: function _destroy() {
      this.selectees.removeClass("ui-selectee").removeData("selectable-item"), this.element.removeClass("ui-selectable ui-selectable-disabled"), this._mouseDestroy();
    }, _mouseStart: function _mouseStart(t) {
      var n = this,
          r = this.options;this.opos = [t.pageX, t.pageY];if (this.options.disabled) return;this.selectees = e(r.filter, this.element[0]), this._trigger("start", t), e(r.appendTo).append(this.helper), this.helper.css({ left: t.pageX, top: t.pageY, width: 0, height: 0 }), r.autoRefresh && this.refresh(), this.selectees.filter(".ui-selected").each(function () {
        var r = e.data(this, "selectable-item");r.startselected = !0, !t.metaKey && !t.ctrlKey && (r.$element.removeClass("ui-selected"), r.selected = !1, r.$element.addClass("ui-unselecting"), r.unselecting = !0, n._trigger("unselecting", t, { unselecting: r.element }));
      }), e(t.target).parents().addBack().each(function () {
        var r,
            i = e.data(this, "selectable-item");if (i) return r = !t.metaKey && !t.ctrlKey || !i.$element.hasClass("ui-selected"), i.$element.removeClass(r ? "ui-unselecting" : "ui-selected").addClass(r ? "ui-selecting" : "ui-unselecting"), i.unselecting = !r, i.selecting = r, i.selected = r, r ? n._trigger("selecting", t, { selecting: i.element }) : n._trigger("unselecting", t, { unselecting: i.element }), !1;
      });
    }, _mouseDrag: function _mouseDrag(t) {
      this.dragged = !0;if (this.options.disabled) return;var n,
          r = this,
          i = this.options,
          s = this.opos[0],
          o = this.opos[1],
          u = t.pageX,
          a = t.pageY;return s > u && (n = u, u = s, s = n), o > a && (n = a, a = o, o = n), this.helper.css({ left: s, top: o, width: u - s, height: a - o }), this.selectees.each(function () {
        var n = e.data(this, "selectable-item"),
            f = !1;if (!n || n.element === r.element[0]) return;i.tolerance === "touch" ? f = !(n.left > u || n.right < s || n.top > a || n.bottom < o) : i.tolerance === "fit" && (f = n.left > s && n.right < u && n.top > o && n.bottom < a), f ? (n.selected && (n.$element.removeClass("ui-selected"), n.selected = !1), n.unselecting && (n.$element.removeClass("ui-unselecting"), n.unselecting = !1), n.selecting || (n.$element.addClass("ui-selecting"), n.selecting = !0, r._trigger("selecting", t, { selecting: n.element }))) : (n.selecting && ((t.metaKey || t.ctrlKey) && n.startselected ? (n.$element.removeClass("ui-selecting"), n.selecting = !1, n.$element.addClass("ui-selected"), n.selected = !0) : (n.$element.removeClass("ui-selecting"), n.selecting = !1, n.startselected && (n.$element.addClass("ui-unselecting"), n.unselecting = !0), r._trigger("unselecting", t, { unselecting: n.element }))), n.selected && !t.metaKey && !t.ctrlKey && !n.startselected && (n.$element.removeClass("ui-selected"), n.selected = !1, n.$element.addClass("ui-unselecting"), n.unselecting = !0, r._trigger("unselecting", t, { unselecting: n.element })));
      }), !1;
    }, _mouseStop: function _mouseStop(t) {
      var n = this;return this.dragged = !1, e(".ui-unselecting", this.element[0]).each(function () {
        var r = e.data(this, "selectable-item");r.$element.removeClass("ui-unselecting"), r.unselecting = !1, r.startselected = !1, n._trigger("unselected", t, { unselected: r.element });
      }), e(".ui-selecting", this.element[0]).each(function () {
        var r = e.data(this, "selectable-item");r.$element.removeClass("ui-selecting").addClass("ui-selected"), r.selecting = !1, r.selected = !0, r.startselected = !0, n._trigger("selected", t, { selected: r.element });
      }), this._trigger("stop", t), this.helper.remove(), !1;
    } });
})(jQuery);(function (e, t) {
  function n(e, t, n) {
    return e > t && e < t + n;
  }e.widget("ui.sortable", e.ui.mouse, { version: "1.10.0", widgetEventPrefix: "sort", ready: !1, options: { appendTo: "parent", axis: !1, connectWith: !1, containment: !1, cursor: "auto", cursorAt: !1, dropOnEmpty: !0, forcePlaceholderSize: !1, forceHelperSize: !1, grid: !1, handle: !1, helper: "original", items: "> *", opacity: !1, placeholder: !1, revert: !1, scroll: !0, scrollSensitivity: 20, scrollSpeed: 20, scope: "default", tolerance: "intersect", zIndex: 1e3, activate: null, beforeStop: null, change: null, deactivate: null, out: null, over: null, receive: null, remove: null, sort: null, start: null, stop: null, update: null }, _create: function _create() {
      var e = this.options;this.containerCache = {}, this.element.addClass("ui-sortable"), this.refresh(), this.floating = this.items.length ? e.axis === "x" || /left|right/.test(this.items[0].item.css("float")) || /inline|table-cell/.test(this.items[0].item.css("display")) : !1, this.offset = this.element.offset(), this._mouseInit(), this.ready = !0;
    }, _destroy: function _destroy() {
      this.element.removeClass("ui-sortable ui-sortable-disabled"), this._mouseDestroy();for (var e = this.items.length - 1; e >= 0; e--) {
        this.items[e].item.removeData(this.widgetName + "-item");
      }return this;
    }, _setOption: function _setOption(t, n) {
      t === "disabled" ? (this.options[t] = n, this.widget().toggleClass("ui-sortable-disabled", !!n)) : e.Widget.prototype._setOption.apply(this, arguments);
    }, _mouseCapture: function _mouseCapture(t, n) {
      var r = null,
          i = !1,
          s = this;if (this.reverting) return !1;if (this.options.disabled || this.options.type === "static") return !1;this._refreshItems(t), e(t.target).parents().each(function () {
        if (e.data(this, s.widgetName + "-item") === s) return r = e(this), !1;
      }), e.data(t.target, s.widgetName + "-item") === s && (r = e(t.target));if (!r) return !1;if (this.options.handle && !n) {
        e(this.options.handle, r).find("*").addBack().each(function () {
          this === t.target && (i = !0);
        });if (!i) return !1;
      }return this.currentItem = r, this._removeCurrentsFromItems(), !0;
    }, _mouseStart: function _mouseStart(t, n, r) {
      var i,
          s = this.options;this.currentContainer = this, this.refreshPositions(), this.helper = this._createHelper(t), this._cacheHelperProportions(), this._cacheMargins(), this.scrollParent = this.helper.scrollParent(), this.offset = this.currentItem.offset(), this.offset = { top: this.offset.top - this.margins.top, left: this.offset.left - this.margins.left }, e.extend(this.offset, { click: { left: t.pageX - this.offset.left, top: t.pageY - this.offset.top }, parent: this._getParentOffset(), relative: this._getRelativeOffset() }), this.helper.css("position", "absolute"), this.cssPosition = this.helper.css("position"), this.originalPosition = this._generatePosition(t), this.originalPageX = t.pageX, this.originalPageY = t.pageY, s.cursorAt && this._adjustOffsetFromHelper(s.cursorAt), this.domPosition = { prev: this.currentItem.prev()[0], parent: this.currentItem.parent()[0] }, this.helper[0] !== this.currentItem[0] && this.currentItem.hide(), this._createPlaceholder(), s.containment && this._setContainment(), s.cursor && (e("body").css("cursor") && (this._storedCursor = e("body").css("cursor")), e("body").css("cursor", s.cursor)), s.opacity && (this.helper.css("opacity") && (this._storedOpacity = this.helper.css("opacity")), this.helper.css("opacity", s.opacity)), s.zIndex && (this.helper.css("zIndex") && (this._storedZIndex = this.helper.css("zIndex")), this.helper.css("zIndex", s.zIndex)), this.scrollParent[0] !== document && this.scrollParent[0].tagName !== "HTML" && (this.overflowOffset = this.scrollParent.offset()), this._trigger("start", t, this._uiHash()), this._preserveHelperProportions || this._cacheHelperProportions();if (!r) for (i = this.containers.length - 1; i >= 0; i--) {
        this.containers[i]._trigger("activate", t, this._uiHash(this));
      }return e.ui.ddmanager && (e.ui.ddmanager.current = this), e.ui.ddmanager && !s.dropBehaviour && e.ui.ddmanager.prepareOffsets(this, t), this.dragging = !0, this.helper.addClass("ui-sortable-helper"), this._mouseDrag(t), !0;
    }, _mouseDrag: function _mouseDrag(t) {
      var n,
          r,
          i,
          s,
          o = this.options,
          u = !1;this.position = this._generatePosition(t), this.positionAbs = this._convertPositionTo("absolute"), this.lastPositionAbs || (this.lastPositionAbs = this.positionAbs), this.options.scroll && (this.scrollParent[0] !== document && this.scrollParent[0].tagName !== "HTML" ? (this.overflowOffset.top + this.scrollParent[0].offsetHeight - t.pageY < o.scrollSensitivity ? this.scrollParent[0].scrollTop = u = this.scrollParent[0].scrollTop + o.scrollSpeed : t.pageY - this.overflowOffset.top < o.scrollSensitivity && (this.scrollParent[0].scrollTop = u = this.scrollParent[0].scrollTop - o.scrollSpeed), this.overflowOffset.left + this.scrollParent[0].offsetWidth - t.pageX < o.scrollSensitivity ? this.scrollParent[0].scrollLeft = u = this.scrollParent[0].scrollLeft + o.scrollSpeed : t.pageX - this.overflowOffset.left < o.scrollSensitivity && (this.scrollParent[0].scrollLeft = u = this.scrollParent[0].scrollLeft - o.scrollSpeed)) : (t.pageY - e(document).scrollTop() < o.scrollSensitivity ? u = e(document).scrollTop(e(document).scrollTop() - o.scrollSpeed) : e(window).height() - (t.pageY - e(document).scrollTop()) < o.scrollSensitivity && (u = e(document).scrollTop(e(document).scrollTop() + o.scrollSpeed)), t.pageX - e(document).scrollLeft() < o.scrollSensitivity ? u = e(document).scrollLeft(e(document).scrollLeft() - o.scrollSpeed) : e(window).width() - (t.pageX - e(document).scrollLeft()) < o.scrollSensitivity && (u = e(document).scrollLeft(e(document).scrollLeft() + o.scrollSpeed))), u !== !1 && e.ui.ddmanager && !o.dropBehaviour && e.ui.ddmanager.prepareOffsets(this, t)), this.positionAbs = this._convertPositionTo("absolute");if (!this.options.axis || this.options.axis !== "y") this.helper[0].style.left = this.position.left + "px";if (!this.options.axis || this.options.axis !== "x") this.helper[0].style.top = this.position.top + "px";for (n = this.items.length - 1; n >= 0; n--) {
        r = this.items[n], i = r.item[0], s = this._intersectsWithPointer(r);if (!s) continue;if (r.instance !== this.currentContainer) continue;if (i !== this.currentItem[0] && this.placeholder[s === 1 ? "next" : "prev"]()[0] !== i && !e.contains(this.placeholder[0], i) && (this.options.type === "semi-dynamic" ? !e.contains(this.element[0], i) : !0)) {
          this.direction = s === 1 ? "down" : "up";if (this.options.tolerance !== "pointer" && !this._intersectsWithSides(r)) break;this._rearrange(t, r), this._trigger("change", t, this._uiHash());break;
        }
      }return this._contactContainers(t), e.ui.ddmanager && e.ui.ddmanager.drag(this, t), this._trigger("sort", t, this._uiHash()), this.lastPositionAbs = this.positionAbs, !1;
    }, _mouseStop: function _mouseStop(t, n) {
      if (!t) return;e.ui.ddmanager && !this.options.dropBehaviour && e.ui.ddmanager.drop(this, t);if (this.options.revert) {
        var r = this,
            i = this.placeholder.offset();this.reverting = !0, e(this.helper).animate({ left: i.left - this.offset.parent.left - this.margins.left + (this.offsetParent[0] === document.body ? 0 : this.offsetParent[0].scrollLeft), top: i.top - this.offset.parent.top - this.margins.top + (this.offsetParent[0] === document.body ? 0 : this.offsetParent[0].scrollTop) }, parseInt(this.options.revert, 10) || 500, function () {
          r._clear(t);
        });
      } else this._clear(t, n);return !1;
    }, cancel: function cancel() {
      if (this.dragging) {
        this._mouseUp({ target: null }), this.options.helper === "original" ? this.currentItem.css(this._storedCSS).removeClass("ui-sortable-helper") : this.currentItem.show();for (var t = this.containers.length - 1; t >= 0; t--) {
          this.containers[t]._trigger("deactivate", null, this._uiHash(this)), this.containers[t].containerCache.over && (this.containers[t]._trigger("out", null, this._uiHash(this)), this.containers[t].containerCache.over = 0);
        }
      }return this.placeholder && (this.placeholder[0].parentNode && this.placeholder[0].parentNode.removeChild(this.placeholder[0]), this.options.helper !== "original" && this.helper && this.helper[0].parentNode && this.helper.remove(), e.extend(this, { helper: null, dragging: !1, reverting: !1, _noFinalSort: null }), this.domPosition.prev ? e(this.domPosition.prev).after(this.currentItem) : e(this.domPosition.parent).prepend(this.currentItem)), this;
    }, serialize: function serialize(t) {
      var n = this._getItemsAsjQuery(t && t.connected),
          r = [];return t = t || {}, e(n).each(function () {
        var n = (e(t.item || this).attr(t.attribute || "id") || "").match(t.expression || /(.+)[\-=_](.+)/);n && r.push((t.key || n[1] + "[]") + "=" + (t.key && t.expression ? n[1] : n[2]));
      }), !r.length && t.key && r.push(t.key + "="), r.join("&");
    }, toArray: function toArray(t) {
      var n = this._getItemsAsjQuery(t && t.connected),
          r = [];return t = t || {}, n.each(function () {
        r.push(e(t.item || this).attr(t.attribute || "id") || "");
      }), r;
    }, _intersectsWith: function _intersectsWith(e) {
      var t = this.positionAbs.left,
          n = t + this.helperProportions.width,
          r = this.positionAbs.top,
          i = r + this.helperProportions.height,
          s = e.left,
          o = s + e.width,
          u = e.top,
          a = u + e.height,
          f = this.offset.click.top,
          l = this.offset.click.left,
          c = r + f > u && r + f < a && t + l > s && t + l < o;return this.options.tolerance === "pointer" || this.options.forcePointerForContainers || this.options.tolerance !== "pointer" && this.helperProportions[this.floating ? "width" : "height"] > e[this.floating ? "width" : "height"] ? c : s < t + this.helperProportions.width / 2 && n - this.helperProportions.width / 2 < o && u < r + this.helperProportions.height / 2 && i - this.helperProportions.height / 2 < a;
    }, _intersectsWithPointer: function _intersectsWithPointer(e) {
      var t = this.options.axis === "x" || n(this.positionAbs.top + this.offset.click.top, e.top, e.height),
          r = this.options.axis === "y" || n(this.positionAbs.left + this.offset.click.left, e.left, e.width),
          i = t && r,
          s = this._getDragVerticalDirection(),
          o = this._getDragHorizontalDirection();return i ? this.floating ? o && o === "right" || s === "down" ? 2 : 1 : s && (s === "down" ? 2 : 1) : !1;
    }, _intersectsWithSides: function _intersectsWithSides(e) {
      var t = n(this.positionAbs.top + this.offset.click.top, e.top + e.height / 2, e.height),
          r = n(this.positionAbs.left + this.offset.click.left, e.left + e.width / 2, e.width),
          i = this._getDragVerticalDirection(),
          s = this._getDragHorizontalDirection();return this.floating && s ? s === "right" && r || s === "left" && !r : i && (i === "down" && t || i === "up" && !t);
    }, _getDragVerticalDirection: function _getDragVerticalDirection() {
      var e = this.positionAbs.top - this.lastPositionAbs.top;return e !== 0 && (e > 0 ? "down" : "up");
    }, _getDragHorizontalDirection: function _getDragHorizontalDirection() {
      var e = this.positionAbs.left - this.lastPositionAbs.left;return e !== 0 && (e > 0 ? "right" : "left");
    }, refresh: function refresh(e) {
      return this._refreshItems(e), this.refreshPositions(), this;
    }, _connectWith: function _connectWith() {
      var e = this.options;return e.connectWith.constructor === String ? [e.connectWith] : e.connectWith;
    }, _getItemsAsjQuery: function _getItemsAsjQuery(t) {
      var n,
          r,
          i,
          s,
          o = [],
          u = [],
          a = this._connectWith();if (a && t) for (n = a.length - 1; n >= 0; n--) {
        i = e(a[n]);for (r = i.length - 1; r >= 0; r--) {
          s = e.data(i[r], this.widgetFullName), s && s !== this && !s.options.disabled && u.push([e.isFunction(s.options.items) ? s.options.items.call(s.element) : e(s.options.items, s.element).not(".ui-sortable-helper").not(".ui-sortable-placeholder"), s]);
        }
      }u.push([e.isFunction(this.options.items) ? this.options.items.call(this.element, null, { options: this.options, item: this.currentItem }) : e(this.options.items, this.element).not(".ui-sortable-helper").not(".ui-sortable-placeholder"), this]);for (n = u.length - 1; n >= 0; n--) {
        u[n][0].each(function () {
          o.push(this);
        });
      }return e(o);
    }, _removeCurrentsFromItems: function _removeCurrentsFromItems() {
      var t = this.currentItem.find(":data(" + this.widgetName + "-item)");this.items = e.grep(this.items, function (e) {
        for (var n = 0; n < t.length; n++) {
          if (t[n] === e.item[0]) return !1;
        }return !0;
      });
    }, _refreshItems: function _refreshItems(t) {
      this.items = [], this.containers = [this];var n,
          r,
          i,
          s,
          o,
          u,
          a,
          f,
          l = this.items,
          c = [[e.isFunction(this.options.items) ? this.options.items.call(this.element[0], t, { item: this.currentItem }) : e(this.options.items, this.element), this]],
          h = this._connectWith();if (h && this.ready) for (n = h.length - 1; n >= 0; n--) {
        i = e(h[n]);for (r = i.length - 1; r >= 0; r--) {
          s = e.data(i[r], this.widgetFullName), s && s !== this && !s.options.disabled && (c.push([e.isFunction(s.options.items) ? s.options.items.call(s.element[0], t, { item: this.currentItem }) : e(s.options.items, s.element), s]), this.containers.push(s));
        }
      }for (n = c.length - 1; n >= 0; n--) {
        o = c[n][1], u = c[n][0];for (r = 0, f = u.length; r < f; r++) {
          a = e(u[r]), a.data(this.widgetName + "-item", o), l.push({ item: a, instance: o, width: 0, height: 0, left: 0, top: 0 });
        }
      }
    }, refreshPositions: function refreshPositions(t) {
      this.offsetParent && this.helper && (this.offset.parent = this._getParentOffset());var n, r, i, s;for (n = this.items.length - 1; n >= 0; n--) {
        r = this.items[n];if (r.instance !== this.currentContainer && this.currentContainer && r.item[0] !== this.currentItem[0]) continue;i = this.options.toleranceElement ? e(this.options.toleranceElement, r.item) : r.item, t || (r.width = i.outerWidth(), r.height = i.outerHeight()), s = i.offset(), r.left = s.left, r.top = s.top;
      }if (this.options.custom && this.options.custom.refreshContainers) this.options.custom.refreshContainers.call(this);else for (n = this.containers.length - 1; n >= 0; n--) {
        s = this.containers[n].element.offset(), this.containers[n].containerCache.left = s.left, this.containers[n].containerCache.top = s.top, this.containers[n].containerCache.width = this.containers[n].element.outerWidth(), this.containers[n].containerCache.height = this.containers[n].element.outerHeight();
      }return this;
    }, _createPlaceholder: function _createPlaceholder(t) {
      t = t || this;var n,
          r = t.options;if (!r.placeholder || r.placeholder.constructor === String) n = r.placeholder, r.placeholder = { element: function element() {
          var r = e(document.createElement(t.currentItem[0].nodeName)).addClass(n || t.currentItem[0].className + " ui-sortable-placeholder").removeClass("ui-sortable-helper")[0];return n || (r.style.visibility = "hidden"), r;
        }, update: function update(e, i) {
          if (n && !r.forcePlaceholderSize) return;i.height() || i.height(t.currentItem.innerHeight() - parseInt(t.currentItem.css("paddingTop") || 0, 10) - parseInt(t.currentItem.css("paddingBottom") || 0, 10)), i.width() || i.width(t.currentItem.innerWidth() - parseInt(t.currentItem.css("paddingLeft") || 0, 10) - parseInt(t.currentItem.css("paddingRight") || 0, 10));
        } };t.placeholder = e(r.placeholder.element.call(t.element, t.currentItem)), t.currentItem.after(t.placeholder), r.placeholder.update(t, t.placeholder);
    }, _contactContainers: function _contactContainers(t) {
      var n,
          r,
          i,
          s,
          o,
          u,
          a,
          f,
          l,
          c = null,
          h = null;for (n = this.containers.length - 1; n >= 0; n--) {
        if (e.contains(this.currentItem[0], this.containers[n].element[0])) continue;if (this._intersectsWith(this.containers[n].containerCache)) {
          if (c && e.contains(this.containers[n].element[0], c.element[0])) continue;c = this.containers[n], h = n;
        } else this.containers[n].containerCache.over && (this.containers[n]._trigger("out", t, this._uiHash(this)), this.containers[n].containerCache.over = 0);
      }if (!c) return;if (this.containers.length === 1) this.containers[h]._trigger("over", t, this._uiHash(this)), this.containers[h].containerCache.over = 1;else {
        i = 1e4, s = null, o = this.containers[h].floating ? "left" : "top", u = this.containers[h].floating ? "width" : "height", a = this.positionAbs[o] + this.offset.click[o];for (r = this.items.length - 1; r >= 0; r--) {
          if (!e.contains(this.containers[h].element[0], this.items[r].item[0])) continue;if (this.items[r].item[0] === this.currentItem[0]) continue;f = this.items[r].item.offset()[o], l = !1, Math.abs(f - a) > Math.abs(f + this.items[r][u] - a) && (l = !0, f += this.items[r][u]), Math.abs(f - a) < i && (i = Math.abs(f - a), s = this.items[r], this.direction = l ? "up" : "down");
        }if (!s && !this.options.dropOnEmpty) return;this.currentContainer = this.containers[h], s ? this._rearrange(t, s, null, !0) : this._rearrange(t, null, this.containers[h].element, !0), this._trigger("change", t, this._uiHash()), this.containers[h]._trigger("change", t, this._uiHash(this)), this.options.placeholder.update(this.currentContainer, this.placeholder), this.containers[h]._trigger("over", t, this._uiHash(this)), this.containers[h].containerCache.over = 1;
      }
    }, _createHelper: function _createHelper(t) {
      var n = this.options,
          r = e.isFunction(n.helper) ? e(n.helper.apply(this.element[0], [t, this.currentItem])) : n.helper === "clone" ? this.currentItem.clone() : this.currentItem;return r.parents("body").length || e(n.appendTo !== "parent" ? n.appendTo : this.currentItem[0].parentNode)[0].appendChild(r[0]), r[0] === this.currentItem[0] && (this._storedCSS = { width: this.currentItem[0].style.width, height: this.currentItem[0].style.height, position: this.currentItem.css("position"), top: this.currentItem.css("top"), left: this.currentItem.css("left") }), (!r[0].style.width || n.forceHelperSize) && r.width(this.currentItem.width()), (!r[0].style.height || n.forceHelperSize) && r.height(this.currentItem.height()), r;
    }, _adjustOffsetFromHelper: function _adjustOffsetFromHelper(t) {
      typeof t == "string" && (t = t.split(" ")), e.isArray(t) && (t = { left: +t[0], top: +t[1] || 0 }), "left" in t && (this.offset.click.left = t.left + this.margins.left), "right" in t && (this.offset.click.left = this.helperProportions.width - t.right + this.margins.left), "top" in t && (this.offset.click.top = t.top + this.margins.top), "bottom" in t && (this.offset.click.top = this.helperProportions.height - t.bottom + this.margins.top);
    }, _getParentOffset: function _getParentOffset() {
      this.offsetParent = this.helper.offsetParent();var t = this.offsetParent.offset();this.cssPosition === "absolute" && this.scrollParent[0] !== document && e.contains(this.scrollParent[0], this.offsetParent[0]) && (t.left += this.scrollParent.scrollLeft(), t.top += this.scrollParent.scrollTop());if (this.offsetParent[0] === document.body || this.offsetParent[0].tagName && this.offsetParent[0].tagName.toLowerCase() === "html" && e.ui.ie) t = { top: 0, left: 0 };return { top: t.top + (parseInt(this.offsetParent.css("borderTopWidth"), 10) || 0), left: t.left + (parseInt(this.offsetParent.css("borderLeftWidth"), 10) || 0) };
    }, _getRelativeOffset: function _getRelativeOffset() {
      if (this.cssPosition === "relative") {
        var e = this.currentItem.position();return { top: e.top - (parseInt(this.helper.css("top"), 10) || 0) + this.scrollParent.scrollTop(), left: e.left - (parseInt(this.helper.css("left"), 10) || 0) + this.scrollParent.scrollLeft() };
      }return { top: 0, left: 0 };
    }, _cacheMargins: function _cacheMargins() {
      this.margins = { left: parseInt(this.currentItem.css("marginLeft"), 10) || 0, top: parseInt(this.currentItem.css("marginTop"), 10) || 0 };
    }, _cacheHelperProportions: function _cacheHelperProportions() {
      this.helperProportions = { width: this.helper.outerWidth(), height: this.helper.outerHeight() };
    }, _setContainment: function _setContainment() {
      var t,
          n,
          r,
          i = this.options;i.containment === "parent" && (i.containment = this.helper[0].parentNode);if (i.containment === "document" || i.containment === "window") this.containment = [0 - this.offset.relative.left - this.offset.parent.left, 0 - this.offset.relative.top - this.offset.parent.top, e(i.containment === "document" ? document : window).width() - this.helperProportions.width - this.margins.left, (e(i.containment === "document" ? document : window).height() || document.body.parentNode.scrollHeight) - this.helperProportions.height - this.margins.top];/^(document|window|parent)$/.test(i.containment) || (t = e(i.containment)[0], n = e(i.containment).offset(), r = e(t).css("overflow") !== "hidden", this.containment = [n.left + (parseInt(e(t).css("borderLeftWidth"), 10) || 0) + (parseInt(e(t).css("paddingLeft"), 10) || 0) - this.margins.left, n.top + (parseInt(e(t).css("borderTopWidth"), 10) || 0) + (parseInt(e(t).css("paddingTop"), 10) || 0) - this.margins.top, n.left + (r ? Math.max(t.scrollWidth, t.offsetWidth) : t.offsetWidth) - (parseInt(e(t).css("borderLeftWidth"), 10) || 0) - (parseInt(e(t).css("paddingRight"), 10) || 0) - this.helperProportions.width - this.margins.left, n.top + (r ? Math.max(t.scrollHeight, t.offsetHeight) : t.offsetHeight) - (parseInt(e(t).css("borderTopWidth"), 10) || 0) - (parseInt(e(t).css("paddingBottom"), 10) || 0) - this.helperProportions.height - this.margins.top]);
    }, _convertPositionTo: function _convertPositionTo(t, n) {
      n || (n = this.position);var r = t === "absolute" ? 1 : -1,
          i = this.cssPosition !== "absolute" || this.scrollParent[0] !== document && !!e.contains(this.scrollParent[0], this.offsetParent[0]) ? this.scrollParent : this.offsetParent,
          s = /(html|body)/i.test(i[0].tagName);return { top: n.top + this.offset.relative.top * r + this.offset.parent.top * r - (this.cssPosition === "fixed" ? -this.scrollParent.scrollTop() : s ? 0 : i.scrollTop()) * r, left: n.left + this.offset.relative.left * r + this.offset.parent.left * r - (this.cssPosition === "fixed" ? -this.scrollParent.scrollLeft() : s ? 0 : i.scrollLeft()) * r };
    }, _generatePosition: function _generatePosition(t) {
      var n,
          r,
          i = this.options,
          s = t.pageX,
          o = t.pageY,
          u = this.cssPosition !== "absolute" || this.scrollParent[0] !== document && !!e.contains(this.scrollParent[0], this.offsetParent[0]) ? this.scrollParent : this.offsetParent,
          a = /(html|body)/i.test(u[0].tagName);return this.cssPosition === "relative" && (this.scrollParent[0] === document || this.scrollParent[0] === this.offsetParent[0]) && (this.offset.relative = this._getRelativeOffset()), this.originalPosition && (this.containment && (t.pageX - this.offset.click.left < this.containment[0] && (s = this.containment[0] + this.offset.click.left), t.pageY - this.offset.click.top < this.containment[1] && (o = this.containment[1] + this.offset.click.top), t.pageX - this.offset.click.left > this.containment[2] && (s = this.containment[2] + this.offset.click.left), t.pageY - this.offset.click.top > this.containment[3] && (o = this.containment[3] + this.offset.click.top)), i.grid && (n = this.originalPageY + Math.round((o - this.originalPageY) / i.grid[1]) * i.grid[1], o = this.containment ? n - this.offset.click.top >= this.containment[1] && n - this.offset.click.top <= this.containment[3] ? n : n - this.offset.click.top >= this.containment[1] ? n - i.grid[1] : n + i.grid[1] : n, r = this.originalPageX + Math.round((s - this.originalPageX) / i.grid[0]) * i.grid[0], s = this.containment ? r - this.offset.click.left >= this.containment[0] && r - this.offset.click.left <= this.containment[2] ? r : r - this.offset.click.left >= this.containment[0] ? r - i.grid[0] : r + i.grid[0] : r)), { top: o - this.offset.click.top - this.offset.relative.top - this.offset.parent.top + (this.cssPosition === "fixed" ? -this.scrollParent.scrollTop() : a ? 0 : u.scrollTop()), left: s - this.offset.click.left - this.offset.relative.left - this.offset.parent.left + (this.cssPosition === "fixed" ? -this.scrollParent.scrollLeft() : a ? 0 : u.scrollLeft()) };
    }, _rearrange: function _rearrange(e, t, n, r) {
      n ? n[0].appendChild(this.placeholder[0]) : t.item[0].parentNode.insertBefore(this.placeholder[0], this.direction === "down" ? t.item[0] : t.item[0].nextSibling), this.counter = this.counter ? ++this.counter : 1;var i = this.counter;this._delay(function () {
        i === this.counter && this.refreshPositions(!r);
      });
    }, _clear: function _clear(t, n) {
      this.reverting = !1;var r,
          i = [];!this._noFinalSort && this.currentItem.parent().length && this.placeholder.before(this.currentItem), this._noFinalSort = null;if (this.helper[0] === this.currentItem[0]) {
        for (r in this._storedCSS) {
          if (this._storedCSS[r] === "auto" || this._storedCSS[r] === "static") this._storedCSS[r] = "";
        }this.currentItem.css(this._storedCSS).removeClass("ui-sortable-helper");
      } else this.currentItem.show();this.fromOutside && !n && i.push(function (e) {
        this._trigger("receive", e, this._uiHash(this.fromOutside));
      }), (this.fromOutside || this.domPosition.prev !== this.currentItem.prev().not(".ui-sortable-helper")[0] || this.domPosition.parent !== this.currentItem.parent()[0]) && !n && i.push(function (e) {
        this._trigger("update", e, this._uiHash());
      }), this !== this.currentContainer && (n || (i.push(function (e) {
        this._trigger("remove", e, this._uiHash());
      }), i.push(function (e) {
        return function (t) {
          e._trigger("receive", t, this._uiHash(this));
        };
      }.call(this, this.currentContainer)), i.push(function (e) {
        return function (t) {
          e._trigger("update", t, this._uiHash(this));
        };
      }.call(this, this.currentContainer))));for (r = this.containers.length - 1; r >= 0; r--) {
        n || i.push(function (e) {
          return function (t) {
            e._trigger("deactivate", t, this._uiHash(this));
          };
        }.call(this, this.containers[r])), this.containers[r].containerCache.over && (i.push(function (e) {
          return function (t) {
            e._trigger("out", t, this._uiHash(this));
          };
        }.call(this, this.containers[r])), this.containers[r].containerCache.over = 0);
      }this._storedCursor && e("body").css("cursor", this._storedCursor), this._storedOpacity && this.helper.css("opacity", this._storedOpacity), this._storedZIndex && this.helper.css("zIndex", this._storedZIndex === "auto" ? "" : this._storedZIndex), this.dragging = !1;if (this.cancelHelperRemoval) {
        if (!n) {
          this._trigger("beforeStop", t, this._uiHash());for (r = 0; r < i.length; r++) {
            i[r].call(this, t);
          }this._trigger("stop", t, this._uiHash());
        }return this.fromOutside = !1, !1;
      }n || this._trigger("beforeStop", t, this._uiHash()), this.placeholder[0].parentNode.removeChild(this.placeholder[0]), this.helper[0] !== this.currentItem[0] && this.helper.remove(), this.helper = null;if (!n) {
        for (r = 0; r < i.length; r++) {
          i[r].call(this, t);
        }this._trigger("stop", t, this._uiHash());
      }return this.fromOutside = !1, !0;
    }, _trigger: function _trigger() {
      e.Widget.prototype._trigger.apply(this, arguments) === !1 && this.cancel();
    }, _uiHash: function _uiHash(t) {
      var n = t || this;return { helper: n.helper, placeholder: n.placeholder || e([]), position: n.position, originalPosition: n.originalPosition, offset: n.positionAbs, item: n.currentItem, sender: t ? t.element : null };
    } });
})(jQuery);(function (e, t) {
  var n = 0,
      r = {},
      i = {};r.height = r.paddingTop = r.paddingBottom = r.borderTopWidth = r.borderBottomWidth = "hide", i.height = i.paddingTop = i.paddingBottom = i.borderTopWidth = i.borderBottomWidth = "show", e.widget("ui.accordion", { version: "1.10.0", options: { active: 0, animate: {}, collapsible: !1, event: "click", header: "> li > :first-child,> :not(li):even", heightStyle: "auto", icons: { activeHeader: "ui-icon-triangle-1-s", header: "ui-icon-triangle-1-e" }, activate: null, beforeActivate: null }, _create: function _create() {
      var t = this.options;this.prevShow = this.prevHide = e(), this.element.addClass("ui-accordion ui-widget ui-helper-reset").attr("role", "tablist"), !t.collapsible && (t.active === !1 || t.active == null) && (t.active = 0), this._processPanels(), t.active < 0 && (t.active += this.headers.length), this._refresh();
    }, _getCreateEventData: function _getCreateEventData() {
      return { header: this.active, content: this.active.length ? this.active.next() : e() };
    }, _createIcons: function _createIcons() {
      var t = this.options.icons;t && (e("<span>").addClass("ui-accordion-header-icon ui-icon " + t.header).prependTo(this.headers), this.active.children(".ui-accordion-header-icon").removeClass(t.header).addClass(t.activeHeader), this.headers.addClass("ui-accordion-icons"));
    }, _destroyIcons: function _destroyIcons() {
      this.headers.removeClass("ui-accordion-icons").children(".ui-accordion-header-icon").remove();
    }, _destroy: function _destroy() {
      var e;this.element.removeClass("ui-accordion ui-widget ui-helper-reset").removeAttr("role"), this.headers.removeClass("ui-accordion-header ui-accordion-header-active ui-helper-reset ui-state-default ui-corner-all ui-state-active ui-state-disabled ui-corner-top").removeAttr("role").removeAttr("aria-selected").removeAttr("aria-controls").removeAttr("tabIndex").each(function () {
        /^ui-accordion/.test(this.id) && this.removeAttribute("id");
      }), this._destroyIcons(), e = this.headers.next().css("display", "").removeAttr("role").removeAttr("aria-expanded").removeAttr("aria-hidden").removeAttr("aria-labelledby").removeClass("ui-helper-reset ui-widget-content ui-corner-bottom ui-accordion-content ui-accordion-content-active ui-state-disabled").each(function () {
        /^ui-accordion/.test(this.id) && this.removeAttribute("id");
      }), this.options.heightStyle !== "content" && e.css("height", "");
    }, _setOption: function _setOption(e, t) {
      if (e === "active") {
        this._activate(t);return;
      }e === "event" && (this.options.event && this._off(this.headers, this.options.event), this._setupEvents(t)), this._super(e, t), e === "collapsible" && !t && this.options.active === !1 && this._activate(0), e === "icons" && (this._destroyIcons(), t && this._createIcons()), e === "disabled" && this.headers.add(this.headers.next()).toggleClass("ui-state-disabled", !!t);
    }, _keydown: function _keydown(t) {
      if (t.altKey || t.ctrlKey) return;var n = e.ui.keyCode,
          r = this.headers.length,
          i = this.headers.index(t.target),
          s = !1;switch (t.keyCode) {case n.RIGHT:case n.DOWN:
          s = this.headers[(i + 1) % r];break;case n.LEFT:case n.UP:
          s = this.headers[(i - 1 + r) % r];break;case n.SPACE:case n.ENTER:
          this._eventHandler(t);break;case n.HOME:
          s = this.headers[0];break;case n.END:
          s = this.headers[r - 1];}s && (e(t.target).attr("tabIndex", -1), e(s).attr("tabIndex", 0), s.focus(), t.preventDefault());
    }, _panelKeyDown: function _panelKeyDown(t) {
      t.keyCode === e.ui.keyCode.UP && t.ctrlKey && e(t.currentTarget).prev().focus();
    }, refresh: function refresh() {
      var t = this.options;this._processPanels();if (t.active === !1 && t.collapsible === !0 || !this.headers.length) t.active = !1, this.active = e();t.active === !1 ? this._activate(0) : this.active.length && !e.contains(this.element[0], this.active[0]) ? this.headers.length === this.headers.find(".ui-state-disabled").length ? (t.active = !1, this.active = e()) : this._activate(Math.max(0, t.active - 1)) : t.active = this.headers.index(this.active), this._destroyIcons(), this._refresh();
    }, _processPanels: function _processPanels() {
      this.headers = this.element.find(this.options.header).addClass("ui-accordion-header ui-helper-reset ui-state-default ui-corner-all"), this.headers.next().addClass("ui-accordion-content ui-helper-reset ui-widget-content ui-corner-bottom").filter(":not(.ui-accordion-content-active)").hide();
    }, _refresh: function _refresh() {
      var t,
          r = this.options,
          i = r.heightStyle,
          s = this.element.parent(),
          o = this.accordionId = "ui-accordion-" + (this.element.attr("id") || ++n);this.active = this._findActive(r.active).addClass("ui-accordion-header-active ui-state-active").toggleClass("ui-corner-all ui-corner-top"), this.active.next().addClass("ui-accordion-content-active").show(), this.headers.attr("role", "tab").each(function (t) {
        var n = e(this),
            r = n.attr("id"),
            i = n.next(),
            s = i.attr("id");r || (r = o + "-header-" + t, n.attr("id", r)), s || (s = o + "-panel-" + t, i.attr("id", s)), n.attr("aria-controls", s), i.attr("aria-labelledby", r);
      }).next().attr("role", "tabpanel"), this.headers.not(this.active).attr({ "aria-selected": "false", tabIndex: -1 }).next().attr({ "aria-expanded": "false", "aria-hidden": "true" }).hide(), this.active.length ? this.active.attr({ "aria-selected": "true", tabIndex: 0 }).next().attr({ "aria-expanded": "true", "aria-hidden": "false" }) : this.headers.eq(0).attr("tabIndex", 0), this._createIcons(), this._setupEvents(r.event), i === "fill" ? (t = s.height(), this.element.siblings(":visible").each(function () {
        var n = e(this),
            r = n.css("position");if (r === "absolute" || r === "fixed") return;t -= n.outerHeight(!0);
      }), this.headers.each(function () {
        t -= e(this).outerHeight(!0);
      }), this.headers.next().each(function () {
        e(this).height(Math.max(0, t - e(this).innerHeight() + e(this).height()));
      }).css("overflow", "auto")) : i === "auto" && (t = 0, this.headers.next().each(function () {
        t = Math.max(t, e(this).css("height", "").height());
      }).height(t));
    }, _activate: function _activate(t) {
      var n = this._findActive(t)[0];if (n === this.active[0]) return;n = n || this.active[0], this._eventHandler({ target: n, currentTarget: n, preventDefault: e.noop });
    }, _findActive: function _findActive(t) {
      return typeof t == "number" ? this.headers.eq(t) : e();
    }, _setupEvents: function _setupEvents(t) {
      var n = { keydown: "_keydown" };t && e.each(t.split(" "), function (e, t) {
        n[t] = "_eventHandler";
      }), this._off(this.headers.add(this.headers.next())), this._on(this.headers, n), this._on(this.headers.next(), { keydown: "_panelKeyDown" }), this._hoverable(this.headers), this._focusable(this.headers);
    }, _eventHandler: function _eventHandler(t) {
      var n = this.options,
          r = this.active,
          i = e(t.currentTarget),
          s = i[0] === r[0],
          o = s && n.collapsible,
          u = o ? e() : i.next(),
          a = r.next(),
          f = { oldHeader: r, oldPanel: a, newHeader: o ? e() : i, newPanel: u };t.preventDefault();if (s && !n.collapsible || this._trigger("beforeActivate", t, f) === !1) return;n.active = o ? !1 : this.headers.index(i), this.active = s ? e() : i, this._toggle(f), r.removeClass("ui-accordion-header-active ui-state-active"), n.icons && r.children(".ui-accordion-header-icon").removeClass(n.icons.activeHeader).addClass(n.icons.header), s || (i.removeClass("ui-corner-all").addClass("ui-accordion-header-active ui-state-active ui-corner-top"), n.icons && i.children(".ui-accordion-header-icon").removeClass(n.icons.header).addClass(n.icons.activeHeader), i.next().addClass("ui-accordion-content-active"));
    }, _toggle: function _toggle(t) {
      var n = t.newPanel,
          r = this.prevShow.length ? this.prevShow : t.oldPanel;this.prevShow.add(this.prevHide).stop(!0, !0), this.prevShow = n, this.prevHide = r, this.options.animate ? this._animate(n, r, t) : (r.hide(), n.show(), this._toggleComplete(t)), r.attr({ "aria-expanded": "false", "aria-hidden": "true" }), r.prev().attr("aria-selected", "false"), n.length && r.length ? r.prev().attr("tabIndex", -1) : n.length && this.headers.filter(function () {
        return e(this).attr("tabIndex") === 0;
      }).attr("tabIndex", -1), n.attr({ "aria-expanded": "true", "aria-hidden": "false" }).prev().attr({ "aria-selected": "true", tabIndex: 0 });
    }, _animate: function _animate(e, t, n) {
      var s,
          o,
          u,
          a = this,
          f = 0,
          l = e.length && (!t.length || e.index() < t.index()),
          c = this.options.animate || {},
          h = l && c.down || c,
          p = function p() {
        a._toggleComplete(n);
      };typeof h == "number" && (u = h), typeof h == "string" && (o = h), o = o || h.easing || c.easing, u = u || h.duration || c.duration;if (!t.length) return e.animate(i, u, o, p);if (!e.length) return t.animate(r, u, o, p);s = e.show().outerHeight(), t.animate(r, { duration: u, easing: o, step: function step(e, t) {
          t.now = Math.round(e);
        } }), e.hide().animate(i, { duration: u, easing: o, complete: p, step: function step(e, n) {
          n.now = Math.round(e), n.prop !== "height" ? f += n.now : a.options.heightStyle !== "content" && (n.now = Math.round(s - t.outerHeight() - f), f = 0);
        } });
    }, _toggleComplete: function _toggleComplete(e) {
      var t = e.oldPanel;t.removeClass("ui-accordion-content-active").prev().removeClass("ui-corner-top").addClass("ui-corner-all"), t.length && (t.parent()[0].className = t.parent()[0].className), this._trigger("activate", null, e);
    } });
})(jQuery);(function (e, t) {
  var n = 0;e.widget("ui.autocomplete", { version: "1.10.0", defaultElement: "<input>", options: { appendTo: null, autoFocus: !1, delay: 300, minLength: 1, position: { my: "left top", at: "left bottom", collision: "none" }, source: null, change: null, close: null, focus: null, open: null, response: null, search: null, select: null }, pending: 0, _create: function _create() {
      var t, n, r;this.isMultiLine = this._isMultiLine(), this.valueMethod = this.element[this.element.is("input,textarea") ? "val" : "text"], this.isNewMenu = !0, this.element.addClass("ui-autocomplete-input").attr("autocomplete", "off"), this._on(this.element, { keydown: function keydown(i) {
          if (this.element.prop("readOnly")) {
            t = !0, r = !0, n = !0;return;
          }t = !1, r = !1, n = !1;var s = e.ui.keyCode;switch (i.keyCode) {case s.PAGE_UP:
              t = !0, this._move("previousPage", i);break;case s.PAGE_DOWN:
              t = !0, this._move("nextPage", i);break;case s.UP:
              t = !0, this._keyEvent("previous", i);break;case s.DOWN:
              t = !0, this._keyEvent("next", i);break;case s.ENTER:case s.NUMPAD_ENTER:
              this.menu.active && (t = !0, i.preventDefault(), this.menu.select(i));break;case s.TAB:
              this.menu.active && this.menu.select(i);break;case s.ESCAPE:
              this.menu.element.is(":visible") && (this._value(this.term), this.close(i), i.preventDefault());break;default:
              n = !0, this._searchTimeout(i);}
        }, keypress: function keypress(r) {
          if (t) {
            t = !1, r.preventDefault();return;
          }if (n) return;var i = e.ui.keyCode;switch (r.keyCode) {case i.PAGE_UP:
              this._move("previousPage", r);break;case i.PAGE_DOWN:
              this._move("nextPage", r);break;case i.UP:
              this._keyEvent("previous", r);break;case i.DOWN:
              this._keyEvent("next", r);}
        }, input: function input(e) {
          if (r) {
            r = !1, e.preventDefault();return;
          }this._searchTimeout(e);
        }, focus: function focus() {
          this.selectedItem = null, this.previous = this._value();
        }, blur: function blur(e) {
          if (this.cancelBlur) {
            delete this.cancelBlur;return;
          }clearTimeout(this.searching), this.close(e), this._change(e);
        } }), this._initSource(), this.menu = e("<ul>").addClass("ui-autocomplete").appendTo(this._appendTo()).menu({ input: e(), role: null }).zIndex(this.element.zIndex() + 1).hide().data("ui-menu"), this._on(this.menu.element, { mousedown: function mousedown(t) {
          t.preventDefault(), this.cancelBlur = !0, this._delay(function () {
            delete this.cancelBlur;
          });var n = this.menu.element[0];e(t.target).closest(".ui-menu-item").length || this._delay(function () {
            var t = this;this.document.one("mousedown", function (r) {
              r.target !== t.element[0] && r.target !== n && !e.contains(n, r.target) && t.close();
            });
          });
        }, menufocus: function menufocus(t, n) {
          if (this.isNewMenu) {
            this.isNewMenu = !1;if (t.originalEvent && /^mouse/.test(t.originalEvent.type)) {
              this.menu.blur(), this.document.one("mousemove", function () {
                e(t.target).trigger(t.originalEvent);
              });return;
            }
          }var r = n.item.data("ui-autocomplete-item");!1 !== this._trigger("focus", t, { item: r }) ? t.originalEvent && /^key/.test(t.originalEvent.type) && this._value(r.value) : this.liveRegion.text(r.value);
        }, menuselect: function menuselect(e, t) {
          var n = t.item.data("ui-autocomplete-item"),
              r = this.previous;this.element[0] !== this.document[0].activeElement && (this.element.focus(), this.previous = r, this._delay(function () {
            this.previous = r, this.selectedItem = n;
          })), !1 !== this._trigger("select", e, { item: n }) && this._value(n.value), this.term = this._value(), this.close(e), this.selectedItem = n;
        } }), this.liveRegion = e("<span>", { role: "status", "aria-live": "polite" }).addClass("ui-helper-hidden-accessible").insertAfter(this.element), this._on(this.window, { beforeunload: function beforeunload() {
          this.element.removeAttr("autocomplete");
        } });
    }, _destroy: function _destroy() {
      clearTimeout(this.searching), this.element.removeClass("ui-autocomplete-input").removeAttr("autocomplete"), this.menu.element.remove(), this.liveRegion.remove();
    }, _setOption: function _setOption(e, t) {
      this._super(e, t), e === "source" && this._initSource(), e === "appendTo" && this.menu.element.appendTo(this._appendTo()), e === "disabled" && t && this.xhr && this.xhr.abort();
    }, _appendTo: function _appendTo() {
      var t = this.options.appendTo;return t && (t = t.jquery || t.nodeType ? e(t) : this.document.find(t).eq(0)), t || (t = this.element.closest(".ui-front")), t.length || (t = this.document[0].body), t;
    }, _isMultiLine: function _isMultiLine() {
      return this.element.is("textarea") ? !0 : this.element.is("input") ? !1 : this.element.prop("isContentEditable");
    }, _initSource: function _initSource() {
      var t,
          n,
          r = this;e.isArray(this.options.source) ? (t = this.options.source, this.source = function (n, r) {
        r(e.ui.autocomplete.filter(t, n.term));
      }) : typeof this.options.source == "string" ? (n = this.options.source, this.source = function (t, i) {
        r.xhr && r.xhr.abort(), r.xhr = e.ajax({ url: n, data: t, dataType: "json", success: function success(e) {
            i(e);
          }, error: function error() {
            i([]);
          } });
      }) : this.source = this.options.source;
    }, _searchTimeout: function _searchTimeout(e) {
      clearTimeout(this.searching), this.searching = this._delay(function () {
        this.term !== this._value() && (this.selectedItem = null, this.search(null, e));
      }, this.options.delay);
    }, search: function search(e, t) {
      e = e != null ? e : this._value(), this.term = this._value();if (e.length < this.options.minLength) return this.close(t);if (this._trigger("search", t) === !1) return;return this._search(e);
    }, _search: function _search(e) {
      this.pending++, this.element.addClass("ui-autocomplete-loading"), this.cancelSearch = !1, this.source({ term: e }, this._response());
    }, _response: function _response() {
      var e = this,
          t = ++n;return function (r) {
        t === n && e.__response(r), e.pending--, e.pending || e.element.removeClass("ui-autocomplete-loading");
      };
    }, __response: function __response(e) {
      e && (e = this._normalize(e)), this._trigger("response", null, { content: e }), !this.options.disabled && e && e.length && !this.cancelSearch ? (this._suggest(e), this._trigger("open")) : this._close();
    }, close: function close(e) {
      this.cancelSearch = !0, this._close(e);
    }, _close: function _close(e) {
      this.menu.element.is(":visible") && (this.menu.element.hide(), this.menu.blur(), this.isNewMenu = !0, this._trigger("close", e));
    }, _change: function _change(e) {
      this.previous !== this._value() && this._trigger("change", e, { item: this.selectedItem });
    }, _normalize: function _normalize(t) {
      return t.length && t[0].label && t[0].value ? t : e.map(t, function (t) {
        return typeof t == "string" ? { label: t, value: t } : e.extend({ label: t.label || t.value, value: t.value || t.label }, t);
      });
    }, _suggest: function _suggest(t) {
      var n = this.menu.element.empty().zIndex(this.element.zIndex() + 1);this._renderMenu(n, t), this.menu.refresh(), n.show(), this._resizeMenu(), n.position(e.extend({ of: this.element }, this.options.position)), this.options.autoFocus && this.menu.next();
    }, _resizeMenu: function _resizeMenu() {
      var e = this.menu.element;e.outerWidth(Math.max(e.width("").outerWidth() + 1, this.element.outerWidth()));
    }, _renderMenu: function _renderMenu(t, n) {
      var r = this;e.each(n, function (e, n) {
        r._renderItemData(t, n);
      });
    }, _renderItemData: function _renderItemData(e, t) {
      return this._renderItem(e, t).data("ui-autocomplete-item", t);
    }, _renderItem: function _renderItem(t, n) {
      return e("<li>").append(e("<a>").text(n.label)).appendTo(t);
    }, _move: function _move(e, t) {
      if (!this.menu.element.is(":visible")) {
        this.search(null, t);return;
      }if (this.menu.isFirstItem() && /^previous/.test(e) || this.menu.isLastItem() && /^next/.test(e)) {
        this._value(this.term), this.menu.blur();return;
      }this.menu[e](t);
    }, widget: function widget() {
      return this.menu.element;
    }, _value: function _value() {
      return this.valueMethod.apply(this.element, arguments);
    }, _keyEvent: function _keyEvent(e, t) {
      if (!this.isMultiLine || this.menu.element.is(":visible")) this._move(e, t), t.preventDefault();
    } }), e.extend(e.ui.autocomplete, { escapeRegex: function escapeRegex(e) {
      return e.replace(/[\-\[\]{}()*+?.,\\\^$|#\s]/g, "\\$&");
    }, filter: function filter(t, n) {
      var r = new RegExp(e.ui.autocomplete.escapeRegex(n), "i");return e.grep(t, function (e) {
        return r.test(e.label || e.value || e);
      });
    } }), e.widget("ui.autocomplete", e.ui.autocomplete, { options: { messages: { noResults: "No search results.", results: function results(e) {
          return e + (e > 1 ? " results are" : " result is") + " available, use up and down arrow keys to navigate.";
        } } }, __response: function __response(e) {
      var t;this._superApply(arguments);if (this.options.disabled || this.cancelSearch) return;e && e.length ? t = this.options.messages.results(e.length) : t = this.options.messages.noResults, this.liveRegion.text(t);
    } });
})(jQuery);(function (e, t) {
  var n,
      r,
      i,
      s,
      o = "ui-button ui-widget ui-state-default ui-corner-all",
      u = "ui-state-hover ui-state-active ",
      a = "ui-button-icons-only ui-button-icon-only ui-button-text-icons ui-button-text-icon-primary ui-button-text-icon-secondary ui-button-text-only",
      f = function f() {
    var t = e(this).find(":ui-button");setTimeout(function () {
      t.button("refresh");
    }, 1);
  },
      l = function l(t) {
    var n = t.name,
        r = t.form,
        i = e([]);return n && (n = n.replace(/'/g, "\\'"), r ? i = e(r).find("[name='" + n + "']") : i = e("[name='" + n + "']", t.ownerDocument).filter(function () {
      return !this.form;
    })), i;
  };e.widget("ui.button", { version: "1.10.0", defaultElement: "<button>", options: { disabled: null, text: !0, label: null, icons: { primary: null, secondary: null } }, _create: function _create() {
      this.element.closest("form").unbind("reset" + this.eventNamespace).bind("reset" + this.eventNamespace, f), typeof this.options.disabled != "boolean" ? this.options.disabled = !!this.element.prop("disabled") : this.element.prop("disabled", this.options.disabled), this._determineButtonType(), this.hasTitle = !!this.buttonElement.attr("title");var t = this,
          u = this.options,
          a = this.type === "checkbox" || this.type === "radio",
          c = a ? "" : "ui-state-active",
          h = "ui-state-focus";u.label === null && (u.label = this.type === "input" ? this.buttonElement.val() : this.buttonElement.html()), this._hoverable(this.buttonElement), this.buttonElement.addClass(o).attr("role", "button").bind("mouseenter" + this.eventNamespace, function () {
        if (u.disabled) return;this === n && e(this).addClass("ui-state-active");
      }).bind("mouseleave" + this.eventNamespace, function () {
        if (u.disabled) return;e(this).removeClass(c);
      }).bind("click" + this.eventNamespace, function (e) {
        u.disabled && (e.preventDefault(), e.stopImmediatePropagation());
      }), this.element.bind("focus" + this.eventNamespace, function () {
        t.buttonElement.addClass(h);
      }).bind("blur" + this.eventNamespace, function () {
        t.buttonElement.removeClass(h);
      }), a && (this.element.bind("change" + this.eventNamespace, function () {
        if (s) return;t.refresh();
      }), this.buttonElement.bind("mousedown" + this.eventNamespace, function (e) {
        if (u.disabled) return;s = !1, r = e.pageX, i = e.pageY;
      }).bind("mouseup" + this.eventNamespace, function (e) {
        if (u.disabled) return;if (r !== e.pageX || i !== e.pageY) s = !0;
      })), this.type === "checkbox" ? this.buttonElement.bind("click" + this.eventNamespace, function () {
        if (u.disabled || s) return !1;
      }) : this.type === "radio" ? this.buttonElement.bind("click" + this.eventNamespace, function () {
        if (u.disabled || s) return !1;e(this).addClass("ui-state-active"), t.buttonElement.attr("aria-pressed", "true");var n = t.element[0];l(n).not(n).map(function () {
          return e(this).button("widget")[0];
        }).removeClass("ui-state-active").attr("aria-pressed", "false");
      }) : (this.buttonElement.bind("mousedown" + this.eventNamespace, function () {
        if (u.disabled) return !1;e(this).addClass("ui-state-active"), n = this, t.document.one("mouseup", function () {
          n = null;
        });
      }).bind("mouseup" + this.eventNamespace, function () {
        if (u.disabled) return !1;e(this).removeClass("ui-state-active");
      }).bind("keydown" + this.eventNamespace, function (t) {
        if (u.disabled) return !1;(t.keyCode === e.ui.keyCode.SPACE || t.keyCode === e.ui.keyCode.ENTER) && e(this).addClass("ui-state-active");
      }).bind("keyup" + this.eventNamespace + " blur" + this.eventNamespace, function () {
        e(this).removeClass("ui-state-active");
      }), this.buttonElement.is("a") && this.buttonElement.keyup(function (t) {
        t.keyCode === e.ui.keyCode.SPACE && e(this).click();
      })), this._setOption("disabled", u.disabled), this._resetButton();
    }, _determineButtonType: function _determineButtonType() {
      var e, t, n;this.element.is("[type=checkbox]") ? this.type = "checkbox" : this.element.is("[type=radio]") ? this.type = "radio" : this.element.is("input") ? this.type = "input" : this.type = "button", this.type === "checkbox" || this.type === "radio" ? (e = this.element.parents().last(), t = "label[for='" + this.element.attr("id") + "']", this.buttonElement = e.find(t), this.buttonElement.length || (e = e.length ? e.siblings() : this.element.siblings(), this.buttonElement = e.filter(t), this.buttonElement.length || (this.buttonElement = e.find(t))), this.element.addClass("ui-helper-hidden-accessible"), n = this.element.is(":checked"), n && this.buttonElement.addClass("ui-state-active"), this.buttonElement.prop("aria-pressed", n)) : this.buttonElement = this.element;
    }, widget: function widget() {
      return this.buttonElement;
    }, _destroy: function _destroy() {
      this.element.removeClass("ui-helper-hidden-accessible"), this.buttonElement.removeClass(o + " " + u + " " + a).removeAttr("role").removeAttr("aria-pressed").html(this.buttonElement.find(".ui-button-text").html()), this.hasTitle || this.buttonElement.removeAttr("title");
    }, _setOption: function _setOption(e, t) {
      this._super(e, t);if (e === "disabled") {
        t ? this.element.prop("disabled", !0) : this.element.prop("disabled", !1);return;
      }this._resetButton();
    }, refresh: function refresh() {
      var t = this.element.is("input, button") ? this.element.is(":disabled") : this.element.hasClass("ui-button-disabled");t !== this.options.disabled && this._setOption("disabled", t), this.type === "radio" ? l(this.element[0]).each(function () {
        e(this).is(":checked") ? e(this).button("widget").addClass("ui-state-active").attr("aria-pressed", "true") : e(this).button("widget").removeClass("ui-state-active").attr("aria-pressed", "false");
      }) : this.type === "checkbox" && (this.element.is(":checked") ? this.buttonElement.addClass("ui-state-active").attr("aria-pressed", "true") : this.buttonElement.removeClass("ui-state-active").attr("aria-pressed", "false"));
    }, _resetButton: function _resetButton() {
      if (this.type === "input") {
        this.options.label && this.element.val(this.options.label);return;
      }var t = this.buttonElement.removeClass(a),
          n = e("<span></span>", this.document[0]).addClass("ui-button-text").html(this.options.label).appendTo(t.empty()).text(),
          r = this.options.icons,
          i = r.primary && r.secondary,
          s = [];r.primary || r.secondary ? (this.options.text && s.push("ui-button-text-icon" + (i ? "s" : r.primary ? "-primary" : "-secondary")), r.primary && t.prepend("<span class='ui-button-icon-primary ui-icon " + r.primary + "'></span>"), r.secondary && t.append("<span class='ui-button-icon-secondary ui-icon " + r.secondary + "'></span>"), this.options.text || (s.push(i ? "ui-button-icons-only" : "ui-button-icon-only"), this.hasTitle || t.attr("title", e.trim(n)))) : s.push("ui-button-text-only"), t.addClass(s.join(" "));
    } }), e.widget("ui.buttonset", { version: "1.10.0", options: { items: "button, input[type=button], input[type=submit], input[type=reset], input[type=checkbox], input[type=radio], a, :data(ui-button)" }, _create: function _create() {
      this.element.addClass("ui-buttonset");
    }, _init: function _init() {
      this.refresh();
    }, _setOption: function _setOption(e, t) {
      e === "disabled" && this.buttons.button("option", e, t), this._super(e, t);
    }, refresh: function refresh() {
      var t = this.element.css("direction") === "rtl";this.buttons = this.element.find(this.options.items).filter(":ui-button").button("refresh").end().not(":ui-button").button().end().map(function () {
        return e(this).button("widget")[0];
      }).removeClass("ui-corner-all ui-corner-left ui-corner-right").filter(":first").addClass(t ? "ui-corner-right" : "ui-corner-left").end().filter(":last").addClass(t ? "ui-corner-left" : "ui-corner-right").end().end();
    }, _destroy: function _destroy() {
      this.element.removeClass("ui-buttonset"), this.buttons.map(function () {
        return e(this).button("widget")[0];
      }).removeClass("ui-corner-left ui-corner-right").end().button("destroy");
    } });
})(jQuery);(function (e, t) {
  function s() {
    this._curInst = null, this._keyEvent = !1, this._disabledInputs = [], this._datepickerShowing = !1, this._inDialog = !1, this._mainDivId = "ui-datepicker-div", this._inlineClass = "ui-datepicker-inline", this._appendClass = "ui-datepicker-append", this._triggerClass = "ui-datepicker-trigger", this._dialogClass = "ui-datepicker-dialog", this._disableClass = "ui-datepicker-disabled", this._unselectableClass = "ui-datepicker-unselectable", this._currentClass = "ui-datepicker-current-day", this._dayOverClass = "ui-datepicker-days-cell-over", this.regional = [], this.regional[""] = { closeText: "Done", prevText: "Prev", nextText: "Next", currentText: "Today", monthNames: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], monthNamesShort: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], dayNames: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], dayNamesShort: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], dayNamesMin: ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"], weekHeader: "Wk", dateFormat: "mm/dd/yy", firstDay: 0, isRTL: !1, showMonthAfterYear: !1, yearSuffix: "" }, this._defaults = { showOn: "focus", showAnim: "fadeIn", showOptions: {}, defaultDate: null, appendText: "", buttonText: "...", buttonImage: "", buttonImageOnly: !1, hideIfNoPrevNext: !1, navigationAsDateFormat: !1, gotoCurrent: !1, changeMonth: !1, changeYear: !1, yearRange: "c-10:c+10", showOtherMonths: !1, selectOtherMonths: !1, showWeek: !1, calculateWeek: this.iso8601Week, shortYearCutoff: "+10", minDate: null, maxDate: null, duration: "fast", beforeShowDay: null, beforeShow: null, onSelect: null, onChangeMonthYear: null, onClose: null, numberOfMonths: 1, showCurrentAtPos: 0, stepMonths: 1, stepBigMonths: 12, altField: "", altFormat: "", constrainInput: !0, showButtonPanel: !1, autoSize: !1, disabled: !1 }, e.extend(this._defaults, this.regional[""]), this.dpDiv = o(e("<div id='" + this._mainDivId + "' class='ui-datepicker ui-widget ui-widget-content ui-helper-clearfix ui-corner-all'></div>"));
  }function o(t) {
    var n = "button, .ui-datepicker-prev, .ui-datepicker-next, .ui-datepicker-calendar td a";return t.delegate(n, "mouseout", function () {
      e(this).removeClass("ui-state-hover"), this.className.indexOf("ui-datepicker-prev") !== -1 && e(this).removeClass("ui-datepicker-prev-hover"), this.className.indexOf("ui-datepicker-next") !== -1 && e(this).removeClass("ui-datepicker-next-hover");
    }).delegate(n, "mouseover", function () {
      e.datepicker._isDisabledDatepicker(i.inline ? t.parent()[0] : i.input[0]) || (e(this).parents(".ui-datepicker-calendar").find("a").removeClass("ui-state-hover"), e(this).addClass("ui-state-hover"), this.className.indexOf("ui-datepicker-prev") !== -1 && e(this).addClass("ui-datepicker-prev-hover"), this.className.indexOf("ui-datepicker-next") !== -1 && e(this).addClass("ui-datepicker-next-hover"));
    });
  }function u(t, n) {
    e.extend(t, n);for (var r in n) {
      n[r] == null && (t[r] = n[r]);
    }return t;
  }e.extend(e.ui, { datepicker: { version: "1.10.0" } });var n = "datepicker",
      r = new Date().getTime(),
      i;e.extend(s.prototype, { markerClassName: "hasDatepicker", maxRows: 4, _widgetDatepicker: function _widgetDatepicker() {
      return this.dpDiv;
    }, setDefaults: function setDefaults(e) {
      return u(this._defaults, e || {}), this;
    }, _attachDatepicker: function _attachDatepicker(t, n) {
      var r, i, s;r = t.nodeName.toLowerCase(), i = r === "div" || r === "span", t.id || (this.uuid += 1, t.id = "dp" + this.uuid), s = this._newInst(e(t), i), s.settings = e.extend({}, n || {}), r === "input" ? this._connectDatepicker(t, s) : i && this._inlineDatepicker(t, s);
    }, _newInst: function _newInst(t, n) {
      var r = t[0].id.replace(/([^A-Za-z0-9_\-])/g, "\\\\$1");return { id: r, input: t, selectedDay: 0, selectedMonth: 0, selectedYear: 0, drawMonth: 0, drawYear: 0, inline: n, dpDiv: n ? o(e("<div class='" + this._inlineClass + " ui-datepicker ui-widget ui-widget-content ui-helper-clearfix ui-corner-all'></div>")) : this.dpDiv };
    }, _connectDatepicker: function _connectDatepicker(t, r) {
      var i = e(t);r.append = e([]), r.trigger = e([]);if (i.hasClass(this.markerClassName)) return;this._attachments(i, r), i.addClass(this.markerClassName).keydown(this._doKeyDown).keypress(this._doKeyPress).keyup(this._doKeyUp), this._autoSize(r), e.data(t, n, r), r.settings.disabled && this._disableDatepicker(t);
    }, _attachments: function _attachments(t, n) {
      var r,
          i,
          s,
          o = this._get(n, "appendText"),
          u = this._get(n, "isRTL");n.append && n.append.remove(), o && (n.append = e("<span class='" + this._appendClass + "'>" + o + "</span>"), t[u ? "before" : "after"](n.append)), t.unbind("focus", this._showDatepicker), n.trigger && n.trigger.remove(), r = this._get(n, "showOn"), (r === "focus" || r === "both") && t.focus(this._showDatepicker);if (r === "button" || r === "both") i = this._get(n, "buttonText"), s = this._get(n, "buttonImage"), n.trigger = e(this._get(n, "buttonImageOnly") ? e("<img/>").addClass(this._triggerClass).attr({ src: s, alt: i, title: i }) : e("<button type='button'></button>").addClass(this._triggerClass).html(s ? e("<img/>").attr({ src: s, alt: i, title: i }) : i)), t[u ? "before" : "after"](n.trigger), n.trigger.click(function () {
        return e.datepicker._datepickerShowing && e.datepicker._lastInput === t[0] ? e.datepicker._hideDatepicker() : e.datepicker._datepickerShowing && e.datepicker._lastInput !== t[0] ? (e.datepicker._hideDatepicker(), e.datepicker._showDatepicker(t[0])) : e.datepicker._showDatepicker(t[0]), !1;
      });
    }, _autoSize: function _autoSize(e) {
      if (this._get(e, "autoSize") && !e.inline) {
        var t,
            n,
            r,
            i,
            s = new Date(2009, 11, 20),
            o = this._get(e, "dateFormat");o.match(/[DM]/) && (t = function t(e) {
          n = 0, r = 0;for (i = 0; i < e.length; i++) {
            e[i].length > n && (n = e[i].length, r = i);
          }return r;
        }, s.setMonth(t(this._get(e, o.match(/MM/) ? "monthNames" : "monthNamesShort"))), s.setDate(t(this._get(e, o.match(/DD/) ? "dayNames" : "dayNamesShort")) + 20 - s.getDay())), e.input.attr("size", this._formatDate(e, s).length);
      }
    }, _inlineDatepicker: function _inlineDatepicker(t, r) {
      var i = e(t);if (i.hasClass(this.markerClassName)) return;i.addClass(this.markerClassName).append(r.dpDiv), e.data(t, n, r), this._setDate(r, this._getDefaultDate(r), !0), this._updateDatepicker(r), this._updateAlternate(r), r.settings.disabled && this._disableDatepicker(t), r.dpDiv.css("display", "block");
    }, _dialogDatepicker: function _dialogDatepicker(t, r, i, s, o) {
      var a,
          f,
          l,
          c,
          h,
          p = this._dialogInst;return p || (this.uuid += 1, a = "dp" + this.uuid, this._dialogInput = e("<input type='text' id='" + a + "' style='position: absolute; top: -100px; width: 0px;'/>"), this._dialogInput.keydown(this._doKeyDown), e("body").append(this._dialogInput), p = this._dialogInst = this._newInst(this._dialogInput, !1), p.settings = {}, e.data(this._dialogInput[0], n, p)), u(p.settings, s || {}), r = r && r.constructor === Date ? this._formatDate(p, r) : r, this._dialogInput.val(r), this._pos = o ? o.length ? o : [o.pageX, o.pageY] : null, this._pos || (f = document.documentElement.clientWidth, l = document.documentElement.clientHeight, c = document.documentElement.scrollLeft || document.body.scrollLeft, h = document.documentElement.scrollTop || document.body.scrollTop, this._pos = [f / 2 - 100 + c, l / 2 - 150 + h]), this._dialogInput.css("left", this._pos[0] + 20 + "px").css("top", this._pos[1] + "px"), p.settings.onSelect = i, this._inDialog = !0, this.dpDiv.addClass(this._dialogClass), this._showDatepicker(this._dialogInput[0]), e.blockUI && e.blockUI(this.dpDiv), e.data(this._dialogInput[0], n, p), this;
    }, _destroyDatepicker: function _destroyDatepicker(t) {
      var r,
          i = e(t),
          s = e.data(t, n);if (!i.hasClass(this.markerClassName)) return;r = t.nodeName.toLowerCase(), e.removeData(t, n), r === "input" ? (s.append.remove(), s.trigger.remove(), i.removeClass(this.markerClassName).unbind("focus", this._showDatepicker).unbind("keydown", this._doKeyDown).unbind("keypress", this._doKeyPress).unbind("keyup", this._doKeyUp)) : (r === "div" || r === "span") && i.removeClass(this.markerClassName).empty();
    }, _enableDatepicker: function _enableDatepicker(t) {
      var r,
          i,
          s = e(t),
          o = e.data(t, n);if (!s.hasClass(this.markerClassName)) return;r = t.nodeName.toLowerCase();if (r === "input") t.disabled = !1, o.trigger.filter("button").each(function () {
        this.disabled = !1;
      }).end().filter("img").css({ opacity: "1.0", cursor: "" });else if (r === "div" || r === "span") i = s.children("." + this._inlineClass), i.children().removeClass("ui-state-disabled"), i.find("select.ui-datepicker-month, select.ui-datepicker-year").prop("disabled", !1);this._disabledInputs = e.map(this._disabledInputs, function (e) {
        return e === t ? null : e;
      });
    }, _disableDatepicker: function _disableDatepicker(t) {
      var r,
          i,
          s = e(t),
          o = e.data(t, n);if (!s.hasClass(this.markerClassName)) return;r = t.nodeName.toLowerCase();if (r === "input") t.disabled = !0, o.trigger.filter("button").each(function () {
        this.disabled = !0;
      }).end().filter("img").css({ opacity: "0.5", cursor: "default" });else if (r === "div" || r === "span") i = s.children("." + this._inlineClass), i.children().addClass("ui-state-disabled"), i.find("select.ui-datepicker-month, select.ui-datepicker-year").prop("disabled", !0);this._disabledInputs = e.map(this._disabledInputs, function (e) {
        return e === t ? null : e;
      }), this._disabledInputs[this._disabledInputs.length] = t;
    }, _isDisabledDatepicker: function _isDisabledDatepicker(e) {
      if (!e) return !1;for (var t = 0; t < this._disabledInputs.length; t++) {
        if (this._disabledInputs[t] === e) return !0;
      }return !1;
    }, _getInst: function _getInst(t) {
      try {
        return e.data(t, n);
      } catch (r) {
        throw "Missing instance data for this datepicker";
      }
    }, _optionDatepicker: function _optionDatepicker(n, r, i) {
      var s,
          o,
          a,
          f,
          l = this._getInst(n);if (arguments.length === 2 && typeof r == "string") return r === "defaults" ? e.extend({}, e.datepicker._defaults) : l ? r === "all" ? e.extend({}, l.settings) : this._get(l, r) : null;s = r || {}, typeof r == "string" && (s = {}, s[r] = i), l && (this._curInst === l && this._hideDatepicker(), o = this._getDateDatepicker(n, !0), a = this._getMinMaxDate(l, "min"), f = this._getMinMaxDate(l, "max"), u(l.settings, s), a !== null && s.dateFormat !== t && s.minDate === t && (l.settings.minDate = this._formatDate(l, a)), f !== null && s.dateFormat !== t && s.maxDate === t && (l.settings.maxDate = this._formatDate(l, f)), "disabled" in s && (s.disabled ? this._disableDatepicker(n) : this._enableDatepicker(n)), this._attachments(e(n), l), this._autoSize(l), this._setDate(l, o), this._updateAlternate(l), this._updateDatepicker(l));
    }, _changeDatepicker: function _changeDatepicker(e, t, n) {
      this._optionDatepicker(e, t, n);
    }, _refreshDatepicker: function _refreshDatepicker(e) {
      var t = this._getInst(e);t && this._updateDatepicker(t);
    }, _setDateDatepicker: function _setDateDatepicker(e, t) {
      var n = this._getInst(e);n && (this._setDate(n, t), this._updateDatepicker(n), this._updateAlternate(n));
    }, _getDateDatepicker: function _getDateDatepicker(e, t) {
      var n = this._getInst(e);return n && !n.inline && this._setDateFromField(n, t), n ? this._getDate(n) : null;
    }, _doKeyDown: function _doKeyDown(t) {
      var n,
          r,
          i,
          s = e.datepicker._getInst(t.target),
          o = !0,
          u = s.dpDiv.is(".ui-datepicker-rtl");s._keyEvent = !0;if (e.datepicker._datepickerShowing) switch (t.keyCode) {case 9:
          e.datepicker._hideDatepicker(), o = !1;break;case 13:
          return i = e("td." + e.datepicker._dayOverClass + ":not(." + e.datepicker._currentClass + ")", s.dpDiv), i[0] && e.datepicker._selectDay(t.target, s.selectedMonth, s.selectedYear, i[0]), n = e.datepicker._get(s, "onSelect"), n ? (r = e.datepicker._formatDate(s), n.apply(s.input ? s.input[0] : null, [r, s])) : e.datepicker._hideDatepicker(), !1;case 27:
          e.datepicker._hideDatepicker();break;case 33:
          e.datepicker._adjustDate(t.target, t.ctrlKey ? -e.datepicker._get(s, "stepBigMonths") : -e.datepicker._get(s, "stepMonths"), "M");break;case 34:
          e.datepicker._adjustDate(t.target, t.ctrlKey ? +e.datepicker._get(s, "stepBigMonths") : +e.datepicker._get(s, "stepMonths"), "M");break;case 35:
          (t.ctrlKey || t.metaKey) && e.datepicker._clearDate(t.target), o = t.ctrlKey || t.metaKey;break;case 36:
          (t.ctrlKey || t.metaKey) && e.datepicker._gotoToday(t.target), o = t.ctrlKey || t.metaKey;break;case 37:
          (t.ctrlKey || t.metaKey) && e.datepicker._adjustDate(t.target, u ? 1 : -1, "D"), o = t.ctrlKey || t.metaKey, t.originalEvent.altKey && e.datepicker._adjustDate(t.target, t.ctrlKey ? -e.datepicker._get(s, "stepBigMonths") : -e.datepicker._get(s, "stepMonths"), "M");break;case 38:
          (t.ctrlKey || t.metaKey) && e.datepicker._adjustDate(t.target, -7, "D"), o = t.ctrlKey || t.metaKey;break;case 39:
          (t.ctrlKey || t.metaKey) && e.datepicker._adjustDate(t.target, u ? -1 : 1, "D"), o = t.ctrlKey || t.metaKey, t.originalEvent.altKey && e.datepicker._adjustDate(t.target, t.ctrlKey ? +e.datepicker._get(s, "stepBigMonths") : +e.datepicker._get(s, "stepMonths"), "M");break;case 40:
          (t.ctrlKey || t.metaKey) && e.datepicker._adjustDate(t.target, 7, "D"), o = t.ctrlKey || t.metaKey;break;default:
          o = !1;} else t.keyCode === 36 && t.ctrlKey ? e.datepicker._showDatepicker(this) : o = !1;o && (t.preventDefault(), t.stopPropagation());
    }, _doKeyPress: function _doKeyPress(t) {
      var n,
          r,
          i = e.datepicker._getInst(t.target);if (e.datepicker._get(i, "constrainInput")) return n = e.datepicker._possibleChars(e.datepicker._get(i, "dateFormat")), r = String.fromCharCode(t.charCode == null ? t.keyCode : t.charCode), t.ctrlKey || t.metaKey || r < " " || !n || n.indexOf(r) > -1;
    }, _doKeyUp: function _doKeyUp(t) {
      var n,
          r = e.datepicker._getInst(t.target);if (r.input.val() !== r.lastVal) try {
        n = e.datepicker.parseDate(e.datepicker._get(r, "dateFormat"), r.input ? r.input.val() : null, e.datepicker._getFormatConfig(r)), n && (e.datepicker._setDateFromField(r), e.datepicker._updateAlternate(r), e.datepicker._updateDatepicker(r));
      } catch (i) {}return !0;
    }, _showDatepicker: function _showDatepicker(t) {
      t = t.target || t, t.nodeName.toLowerCase() !== "input" && (t = e("input", t.parentNode)[0]);if (e.datepicker._isDisabledDatepicker(t) || e.datepicker._lastInput === t) return;var n, r, i, s, o, a, f;n = e.datepicker._getInst(t), e.datepicker._curInst && e.datepicker._curInst !== n && (e.datepicker._curInst.dpDiv.stop(!0, !0), n && e.datepicker._datepickerShowing && e.datepicker._hideDatepicker(e.datepicker._curInst.input[0])), r = e.datepicker._get(n, "beforeShow"), i = r ? r.apply(t, [t, n]) : {};if (i === !1) return;u(n.settings, i), n.lastVal = null, e.datepicker._lastInput = t, e.datepicker._setDateFromField(n), e.datepicker._inDialog && (t.value = ""), e.datepicker._pos || (e.datepicker._pos = e.datepicker._findPos(t), e.datepicker._pos[1] += t.offsetHeight), s = !1, e(t).parents().each(function () {
        return s |= e(this).css("position") === "fixed", !s;
      }), o = { left: e.datepicker._pos[0], top: e.datepicker._pos[1] }, e.datepicker._pos = null, n.dpDiv.empty(), n.dpDiv.css({ position: "absolute", display: "block", top: "-1000px" }), e.datepicker._updateDatepicker(n), o = e.datepicker._checkOffset(n, o, s), n.dpDiv.css({ position: e.datepicker._inDialog && e.blockUI ? "static" : s ? "fixed" : "absolute", display: "none", left: o.left + "px", top: o.top + "px" }), n.inline || (a = e.datepicker._get(n, "showAnim"), f = e.datepicker._get(n, "duration"), n.dpDiv.zIndex(e(t).zIndex() + 1), e.datepicker._datepickerShowing = !0, e.effects && e.effects.effect[a] ? n.dpDiv.show(a, e.datepicker._get(n, "showOptions"), f) : n.dpDiv[a || "show"](a ? f : null), n.input.is(":visible") && !n.input.is(":disabled") && n.input.focus(), e.datepicker._curInst = n);
    }, _updateDatepicker: function _updateDatepicker(t) {
      this.maxRows = 4, i = t, t.dpDiv.empty().append(this._generateHTML(t)), this._attachHandlers(t), t.dpDiv.find("." + this._dayOverClass + " a").mouseover();var n,
          r = this._getNumberOfMonths(t),
          s = r[1],
          o = 17;t.dpDiv.removeClass("ui-datepicker-multi-2 ui-datepicker-multi-3 ui-datepicker-multi-4").width(""), s > 1 && t.dpDiv.addClass("ui-datepicker-multi-" + s).css("width", o * s + "em"), t.dpDiv[(r[0] !== 1 || r[1] !== 1 ? "add" : "remove") + "Class"]("ui-datepicker-multi"), t.dpDiv[(this._get(t, "isRTL") ? "add" : "remove") + "Class"]("ui-datepicker-rtl"), t === e.datepicker._curInst && e.datepicker._datepickerShowing && t.input && t.input.is(":visible") && !t.input.is(":disabled") && t.input[0] !== document.activeElement && t.input.focus(), t.yearshtml && (n = t.yearshtml, setTimeout(function () {
        n === t.yearshtml && t.yearshtml && t.dpDiv.find("select.ui-datepicker-year:first").replaceWith(t.yearshtml), n = t.yearshtml = null;
      }, 0));
    }, _getBorders: function _getBorders(e) {
      var t = function t(e) {
        return { thin: 1, medium: 2, thick: 3 }[e] || e;
      };return [parseFloat(t(e.css("border-left-width"))), parseFloat(t(e.css("border-top-width")))];
    }, _checkOffset: function _checkOffset(t, n, r) {
      var i = t.dpDiv.outerWidth(),
          s = t.dpDiv.outerHeight(),
          o = t.input ? t.input.outerWidth() : 0,
          u = t.input ? t.input.outerHeight() : 0,
          a = document.documentElement.clientWidth + (r ? 0 : e(document).scrollLeft()),
          f = document.documentElement.clientHeight + (r ? 0 : e(document).scrollTop());return n.left -= this._get(t, "isRTL") ? i - o : 0, n.left -= r && n.left === t.input.offset().left ? e(document).scrollLeft() : 0, n.top -= r && n.top === t.input.offset().top + u ? e(document).scrollTop() : 0, n.left -= Math.min(n.left, n.left + i > a && a > i ? Math.abs(n.left + i - a) : 0), n.top -= Math.min(n.top, n.top + s > f && f > s ? Math.abs(s + u) : 0), n;
    }, _findPos: function _findPos(t) {
      var n,
          r = this._getInst(t),
          i = this._get(r, "isRTL");while (t && (t.type === "hidden" || t.nodeType !== 1 || e.expr.filters.hidden(t))) {
        t = t[i ? "previousSibling" : "nextSibling"];
      }return n = e(t).offset(), [n.left, n.top];
    }, _hideDatepicker: function _hideDatepicker(t) {
      var r,
          i,
          s,
          o,
          u = this._curInst;if (!u || t && u !== e.data(t, n)) return;this._datepickerShowing && (r = this._get(u, "showAnim"), i = this._get(u, "duration"), s = function s() {
        e.datepicker._tidyDialog(u);
      }, e.effects && (e.effects.effect[r] || e.effects[r]) ? u.dpDiv.hide(r, e.datepicker._get(u, "showOptions"), i, s) : u.dpDiv[r === "slideDown" ? "slideUp" : r === "fadeIn" ? "fadeOut" : "hide"](r ? i : null, s), r || s(), this._datepickerShowing = !1, o = this._get(u, "onClose"), o && o.apply(u.input ? u.input[0] : null, [u.input ? u.input.val() : "", u]), this._lastInput = null, this._inDialog && (this._dialogInput.css({ position: "absolute", left: "0", top: "-100px" }), e.blockUI && (e.unblockUI(), e("body").append(this.dpDiv))), this._inDialog = !1);
    }, _tidyDialog: function _tidyDialog(e) {
      e.dpDiv.removeClass(this._dialogClass).unbind(".ui-datepicker-calendar");
    }, _checkExternalClick: function _checkExternalClick(t) {
      if (!e.datepicker._curInst) return;var n = e(t.target),
          r = e.datepicker._getInst(n[0]);(n[0].id !== e.datepicker._mainDivId && n.parents("#" + e.datepicker._mainDivId).length === 0 && !n.hasClass(e.datepicker.markerClassName) && !n.closest("." + e.datepicker._triggerClass).length && e.datepicker._datepickerShowing && (!e.datepicker._inDialog || !e.blockUI) || n.hasClass(e.datepicker.markerClassName) && e.datepicker._curInst !== r) && e.datepicker._hideDatepicker();
    }, _adjustDate: function _adjustDate(t, n, r) {
      var i = e(t),
          s = this._getInst(i[0]);if (this._isDisabledDatepicker(i[0])) return;this._adjustInstDate(s, n + (r === "M" ? this._get(s, "showCurrentAtPos") : 0), r), this._updateDatepicker(s);
    }, _gotoToday: function _gotoToday(t) {
      var n,
          r = e(t),
          i = this._getInst(r[0]);this._get(i, "gotoCurrent") && i.currentDay ? (i.selectedDay = i.currentDay, i.drawMonth = i.selectedMonth = i.currentMonth, i.drawYear = i.selectedYear = i.currentYear) : (n = new Date(), i.selectedDay = n.getDate(), i.drawMonth = i.selectedMonth = n.getMonth(), i.drawYear = i.selectedYear = n.getFullYear()), this._notifyChange(i), this._adjustDate(r);
    }, _selectMonthYear: function _selectMonthYear(t, n, r) {
      var i = e(t),
          s = this._getInst(i[0]);s["selected" + (r === "M" ? "Month" : "Year")] = s["draw" + (r === "M" ? "Month" : "Year")] = parseInt(n.options[n.selectedIndex].value, 10), this._notifyChange(s), this._adjustDate(i);
    }, _selectDay: function _selectDay(t, n, r, i) {
      var s,
          o = e(t);if (e(i).hasClass(this._unselectableClass) || this._isDisabledDatepicker(o[0])) return;s = this._getInst(o[0]), s.selectedDay = s.currentDay = e("a", i).html(), s.selectedMonth = s.currentMonth = n, s.selectedYear = s.currentYear = r, this._selectDate(t, this._formatDate(s, s.currentDay, s.currentMonth, s.currentYear));
    }, _clearDate: function _clearDate(t) {
      var n = e(t);this._selectDate(n, "");
    }, _selectDate: function _selectDate(t, n) {
      var r,
          i = e(t),
          s = this._getInst(i[0]);n = n != null ? n : this._formatDate(s), s.input && s.input.val(n), this._updateAlternate(s), r = this._get(s, "onSelect"), r ? r.apply(s.input ? s.input[0] : null, [n, s]) : s.input && s.input.trigger("change"), s.inline ? this._updateDatepicker(s) : (this._hideDatepicker(), this._lastInput = s.input[0], _typeof(s.input[0]) != "object" && s.input.focus(), this._lastInput = null);
    }, _updateAlternate: function _updateAlternate(t) {
      var n,
          r,
          i,
          s = this._get(t, "altField");s && (n = this._get(t, "altFormat") || this._get(t, "dateFormat"), r = this._getDate(t), i = this.formatDate(n, r, this._getFormatConfig(t)), e(s).each(function () {
        e(this).val(i);
      }));
    }, noWeekends: function noWeekends(e) {
      var t = e.getDay();return [t > 0 && t < 6, ""];
    }, iso8601Week: function iso8601Week(e) {
      var t,
          n = new Date(e.getTime());return n.setDate(n.getDate() + 4 - (n.getDay() || 7)), t = n.getTime(), n.setMonth(0), n.setDate(1), Math.floor(Math.round((t - n) / 864e5) / 7) + 1;
    }, parseDate: function parseDate(t, n, r) {
      if (t == null || n == null) throw "Invalid arguments";n = (typeof n === "undefined" ? "undefined" : _typeof(n)) == "object" ? n.toString() : n + "";if (n === "") return null;var i,
          s,
          o,
          u = 0,
          a = (r ? r.shortYearCutoff : null) || this._defaults.shortYearCutoff,
          f = typeof a != "string" ? a : new Date().getFullYear() % 100 + parseInt(a, 10),
          l = (r ? r.dayNamesShort : null) || this._defaults.dayNamesShort,
          c = (r ? r.dayNames : null) || this._defaults.dayNames,
          h = (r ? r.monthNamesShort : null) || this._defaults.monthNamesShort,
          p = (r ? r.monthNames : null) || this._defaults.monthNames,
          d = -1,
          v = -1,
          m = -1,
          g = -1,
          y = !1,
          b,
          w = function w(e) {
        var n = i + 1 < t.length && t.charAt(i + 1) === e;return n && i++, n;
      },
          E = function E(e) {
        var t = w(e),
            r = e === "@" ? 14 : e === "!" ? 20 : e === "y" && t ? 4 : e === "o" ? 3 : 2,
            i = new RegExp("^\\d{1," + r + "}"),
            s = n.substring(u).match(i);if (!s) throw "Missing number at position " + u;return u += s[0].length, parseInt(s[0], 10);
      },
          S = function S(t, r, i) {
        var s = -1,
            o = e.map(w(t) ? i : r, function (e, t) {
          return [[t, e]];
        }).sort(function (e, t) {
          return -(e[1].length - t[1].length);
        });e.each(o, function (e, t) {
          var r = t[1];if (n.substr(u, r.length).toLowerCase() === r.toLowerCase()) return s = t[0], u += r.length, !1;
        });if (s !== -1) return s + 1;throw "Unknown name at position " + u;
      },
          x = function x() {
        if (n.charAt(u) !== t.charAt(i)) throw "Unexpected literal at position " + u;u++;
      };for (i = 0; i < t.length; i++) {
        if (y) t.charAt(i) === "'" && !w("'") ? y = !1 : x();else switch (t.charAt(i)) {case "d":
            m = E("d");break;case "D":
            S("D", l, c);break;case "o":
            g = E("o");break;case "m":
            v = E("m");break;case "M":
            v = S("M", h, p);break;case "y":
            d = E("y");break;case "@":
            b = new Date(E("@")), d = b.getFullYear(), v = b.getMonth() + 1, m = b.getDate();break;case "!":
            b = new Date((E("!") - this._ticksTo1970) / 1e4), d = b.getFullYear(), v = b.getMonth() + 1, m = b.getDate();break;case "'":
            w("'") ? x() : y = !0;break;default:
            x();}
      }if (u < n.length) {
        o = n.substr(u);if (!/^\s+/.test(o)) throw "Extra/unparsed characters found in date: " + o;
      }d === -1 ? d = new Date().getFullYear() : d < 100 && (d += new Date().getFullYear() - new Date().getFullYear() % 100 + (d <= f ? 0 : -100));if (g > -1) {
        v = 1, m = g;do {
          s = this._getDaysInMonth(d, v - 1);if (m <= s) break;v++, m -= s;
        } while (!0);
      }b = this._daylightSavingAdjust(new Date(d, v - 1, m));if (b.getFullYear() !== d || b.getMonth() + 1 !== v || b.getDate() !== m) throw "Invalid date";return b;
    }, ATOM: "yy-mm-dd", COOKIE: "D, dd M yy", ISO_8601: "yy-mm-dd", RFC_822: "D, d M y", RFC_850: "DD, dd-M-y", RFC_1036: "D, d M y", RFC_1123: "D, d M yy", RFC_2822: "D, d M yy", RSS: "D, d M y", TICKS: "!", TIMESTAMP: "@", W3C: "yy-mm-dd", _ticksTo1970: (718685 + Math.floor(492.5) - Math.floor(19.7) + Math.floor(4.925)) * 24 * 60 * 60 * 1e7, formatDate: function formatDate(e, t, n) {
      if (!t) return "";var r,
          i = (n ? n.dayNamesShort : null) || this._defaults.dayNamesShort,
          s = (n ? n.dayNames : null) || this._defaults.dayNames,
          o = (n ? n.monthNamesShort : null) || this._defaults.monthNamesShort,
          u = (n ? n.monthNames : null) || this._defaults.monthNames,
          a = function a(t) {
        var n = r + 1 < e.length && e.charAt(r + 1) === t;return n && r++, n;
      },
          f = function f(e, t, n) {
        var r = "" + t;if (a(e)) while (r.length < n) {
          r = "0" + r;
        }return r;
      },
          l = function l(e, t, n, r) {
        return a(e) ? r[t] : n[t];
      },
          c = "",
          h = !1;if (t) for (r = 0; r < e.length; r++) {
        if (h) e.charAt(r) === "'" && !a("'") ? h = !1 : c += e.charAt(r);else switch (e.charAt(r)) {case "d":
            c += f("d", t.getDate(), 2);break;case "D":
            c += l("D", t.getDay(), i, s);break;case "o":
            c += f("o", Math.round((new Date(t.getFullYear(), t.getMonth(), t.getDate()).getTime() - new Date(t.getFullYear(), 0, 0).getTime()) / 864e5), 3);break;case "m":
            c += f("m", t.getMonth() + 1, 2);break;case "M":
            c += l("M", t.getMonth(), o, u);break;case "y":
            c += a("y") ? t.getFullYear() : (t.getYear() % 100 < 10 ? "0" : "") + t.getYear() % 100;break;case "@":
            c += t.getTime();break;case "!":
            c += t.getTime() * 1e4 + this._ticksTo1970;break;case "'":
            a("'") ? c += "'" : h = !0;break;default:
            c += e.charAt(r);}
      }return c;
    }, _possibleChars: function _possibleChars(e) {
      var t,
          n = "",
          r = !1,
          i = function i(n) {
        var r = t + 1 < e.length && e.charAt(t + 1) === n;return r && t++, r;
      };for (t = 0; t < e.length; t++) {
        if (r) e.charAt(t) === "'" && !i("'") ? r = !1 : n += e.charAt(t);else switch (e.charAt(t)) {case "d":case "m":case "y":case "@":
            n += "0123456789";break;case "D":case "M":
            return null;case "'":
            i("'") ? n += "'" : r = !0;break;default:
            n += e.charAt(t);}
      }return n;
    }, _get: function _get(e, n) {
      return e.settings[n] !== t ? e.settings[n] : this._defaults[n];
    }, _setDateFromField: function _setDateFromField(e, t) {
      if (e.input.val() === e.lastVal) return;var n = this._get(e, "dateFormat"),
          r = e.lastVal = e.input ? e.input.val() : null,
          i = this._getDefaultDate(e),
          s = i,
          o = this._getFormatConfig(e);try {
        s = this.parseDate(n, r, o) || i;
      } catch (u) {
        r = t ? "" : r;
      }e.selectedDay = s.getDate(), e.drawMonth = e.selectedMonth = s.getMonth(), e.drawYear = e.selectedYear = s.getFullYear(), e.currentDay = r ? s.getDate() : 0, e.currentMonth = r ? s.getMonth() : 0, e.currentYear = r ? s.getFullYear() : 0, this._adjustInstDate(e);
    }, _getDefaultDate: function _getDefaultDate(e) {
      return this._restrictMinMax(e, this._determineDate(e, this._get(e, "defaultDate"), new Date()));
    }, _determineDate: function _determineDate(t, n, r) {
      var i = function i(e) {
        var t = new Date();return t.setDate(t.getDate() + e), t;
      },
          s = function s(n) {
        try {
          return e.datepicker.parseDate(e.datepicker._get(t, "dateFormat"), n, e.datepicker._getFormatConfig(t));
        } catch (r) {}var i = (n.toLowerCase().match(/^c/) ? e.datepicker._getDate(t) : null) || new Date(),
            s = i.getFullYear(),
            o = i.getMonth(),
            u = i.getDate(),
            a = /([+\-]?[0-9]+)\s*(d|D|w|W|m|M|y|Y)?/g,
            f = a.exec(n);while (f) {
          switch (f[2] || "d") {case "d":case "D":
              u += parseInt(f[1], 10);break;case "w":case "W":
              u += parseInt(f[1], 10) * 7;break;case "m":case "M":
              o += parseInt(f[1], 10), u = Math.min(u, e.datepicker._getDaysInMonth(s, o));break;case "y":case "Y":
              s += parseInt(f[1], 10), u = Math.min(u, e.datepicker._getDaysInMonth(s, o));}f = a.exec(n);
        }return new Date(s, o, u);
      },
          o = n == null || n === "" ? r : typeof n == "string" ? s(n) : typeof n == "number" ? isNaN(n) ? r : i(n) : new Date(n.getTime());return o = o && o.toString() === "Invalid Date" ? r : o, o && (o.setHours(0), o.setMinutes(0), o.setSeconds(0), o.setMilliseconds(0)), this._daylightSavingAdjust(o);
    }, _daylightSavingAdjust: function _daylightSavingAdjust(e) {
      return e ? (e.setHours(e.getHours() > 12 ? e.getHours() + 2 : 0), e) : null;
    }, _setDate: function _setDate(e, t, n) {
      var r = !t,
          i = e.selectedMonth,
          s = e.selectedYear,
          o = this._restrictMinMax(e, this._determineDate(e, t, new Date()));e.selectedDay = e.currentDay = o.getDate(), e.drawMonth = e.selectedMonth = e.currentMonth = o.getMonth(), e.drawYear = e.selectedYear = e.currentYear = o.getFullYear(), (i !== e.selectedMonth || s !== e.selectedYear) && !n && this._notifyChange(e), this._adjustInstDate(e), e.input && e.input.val(r ? "" : this._formatDate(e));
    }, _getDate: function _getDate(e) {
      var t = !e.currentYear || e.input && e.input.val() === "" ? null : this._daylightSavingAdjust(new Date(e.currentYear, e.currentMonth, e.currentDay));return t;
    }, _attachHandlers: function _attachHandlers(t) {
      var n = this._get(t, "stepMonths"),
          i = "#" + t.id.replace(/\\\\/g, "\\");t.dpDiv.find("[data-handler]").map(function () {
        var t = { prev: function prev() {
            window["DP_jQuery_" + r].datepicker._adjustDate(i, -n, "M");
          }, next: function next() {
            window["DP_jQuery_" + r].datepicker._adjustDate(i, +n, "M");
          }, hide: function hide() {
            window["DP_jQuery_" + r].datepicker._hideDatepicker();
          }, today: function today() {
            window["DP_jQuery_" + r].datepicker._gotoToday(i);
          }, selectDay: function selectDay() {
            return window["DP_jQuery_" + r].datepicker._selectDay(i, +this.getAttribute("data-month"), +this.getAttribute("data-year"), this), !1;
          }, selectMonth: function selectMonth() {
            return window["DP_jQuery_" + r].datepicker._selectMonthYear(i, this, "M"), !1;
          }, selectYear: function selectYear() {
            return window["DP_jQuery_" + r].datepicker._selectMonthYear(i, this, "Y"), !1;
          } };e(this).bind(this.getAttribute("data-event"), t[this.getAttribute("data-handler")]);
      });
    }, _generateHTML: function _generateHTML(e) {
      var t,
          n,
          r,
          i,
          s,
          o,
          u,
          a,
          f,
          l,
          c,
          h,
          p,
          d,
          v,
          m,
          g,
          y,
          b,
          w,
          E,
          S,
          x,
          T,
          N,
          C,
          k,
          L,
          A,
          O,
          M,
          _,
          D,
          P,
          H,
          B,
          j,
          F,
          I,
          q = new Date(),
          R = this._daylightSavingAdjust(new Date(q.getFullYear(), q.getMonth(), q.getDate())),
          U = this._get(e, "isRTL"),
          z = this._get(e, "showButtonPanel"),
          W = this._get(e, "hideIfNoPrevNext"),
          X = this._get(e, "navigationAsDateFormat"),
          V = this._getNumberOfMonths(e),
          $ = this._get(e, "showCurrentAtPos"),
          J = this._get(e, "stepMonths"),
          K = V[0] !== 1 || V[1] !== 1,
          Q = this._daylightSavingAdjust(e.currentDay ? new Date(e.currentYear, e.currentMonth, e.currentDay) : new Date(9999, 9, 9)),
          G = this._getMinMaxDate(e, "min"),
          Y = this._getMinMaxDate(e, "max"),
          Z = e.drawMonth - $,
          et = e.drawYear;Z < 0 && (Z += 12, et--);if (Y) {
        t = this._daylightSavingAdjust(new Date(Y.getFullYear(), Y.getMonth() - V[0] * V[1] + 1, Y.getDate())), t = G && t < G ? G : t;while (this._daylightSavingAdjust(new Date(et, Z, 1)) > t) {
          Z--, Z < 0 && (Z = 11, et--);
        }
      }e.drawMonth = Z, e.drawYear = et, n = this._get(e, "prevText"), n = X ? this.formatDate(n, this._daylightSavingAdjust(new Date(et, Z - J, 1)), this._getFormatConfig(e)) : n, r = this._canAdjustMonth(e, -1, et, Z) ? "<a class='ui-datepicker-prev ui-corner-all' data-handler='prev' data-event='click' title='" + n + "'><span class='ui-icon ui-icon-circle-triangle-" + (U ? "e" : "w") + "'>" + n + "</span></a>" : W ? "" : "<a class='ui-datepicker-prev ui-corner-all ui-state-disabled' title='" + n + "'><span class='ui-icon ui-icon-circle-triangle-" + (U ? "e" : "w") + "'>" + n + "</span></a>", i = this._get(e, "nextText"), i = X ? this.formatDate(i, this._daylightSavingAdjust(new Date(et, Z + J, 1)), this._getFormatConfig(e)) : i, s = this._canAdjustMonth(e, 1, et, Z) ? "<a class='ui-datepicker-next ui-corner-all' data-handler='next' data-event='click' title='" + i + "'><span class='ui-icon ui-icon-circle-triangle-" + (U ? "w" : "e") + "'>" + i + "</span></a>" : W ? "" : "<a class='ui-datepicker-next ui-corner-all ui-state-disabled' title='" + i + "'><span class='ui-icon ui-icon-circle-triangle-" + (U ? "w" : "e") + "'>" + i + "</span></a>", o = this._get(e, "currentText"), u = this._get(e, "gotoCurrent") && e.currentDay ? Q : R, o = X ? this.formatDate(o, u, this._getFormatConfig(e)) : o, a = e.inline ? "" : "<button type='button' class='ui-datepicker-close ui-state-default ui-priority-primary ui-corner-all' data-handler='hide' data-event='click'>" + this._get(e, "closeText") + "</button>", f = z ? "<div class='ui-datepicker-buttonpane ui-widget-content'>" + (U ? a : "") + (this._isInRange(e, u) ? "<button type='button' class='ui-datepicker-current ui-state-default ui-priority-secondary ui-corner-all' data-handler='today' data-event='click'>" + o + "</button>" : "") + (U ? "" : a) + "</div>" : "", l = parseInt(this._get(e, "firstDay"), 10), l = isNaN(l) ? 0 : l, c = this._get(e, "showWeek"), h = this._get(e, "dayNames"), p = this._get(e, "dayNamesMin"), d = this._get(e, "monthNames"), v = this._get(e, "monthNamesShort"), m = this._get(e, "beforeShowDay"), g = this._get(e, "showOtherMonths"), y = this._get(e, "selectOtherMonths"), b = this._getDefaultDate(e), w = "", E;for (S = 0; S < V[0]; S++) {
        x = "", this.maxRows = 4;for (T = 0; T < V[1]; T++) {
          N = this._daylightSavingAdjust(new Date(et, Z, e.selectedDay)), C = " ui-corner-all", k = "";if (K) {
            k += "<div class='ui-datepicker-group";if (V[1] > 1) switch (T) {case 0:
                k += " ui-datepicker-group-first", C = " ui-corner-" + (U ? "right" : "left");break;case V[1] - 1:
                k += " ui-datepicker-group-last", C = " ui-corner-" + (U ? "left" : "right");break;default:
                k += " ui-datepicker-group-middle", C = "";}k += "'>";
          }k += "<div class='ui-datepicker-header ui-widget-header ui-helper-clearfix" + C + "'>" + (/all|left/.test(C) && S === 0 ? U ? s : r : "") + (/all|right/.test(C) && S === 0 ? U ? r : s : "") + this._generateMonthYearHeader(e, Z, et, G, Y, S > 0 || T > 0, d, v) + "</div><table class='ui-datepicker-calendar'><thead>" + "<tr>", L = c ? "<th class='ui-datepicker-week-col'>" + this._get(e, "weekHeader") + "</th>" : "";for (E = 0; E < 7; E++) {
            A = (E + l) % 7, L += "<th" + ((E + l + 6) % 7 >= 5 ? " class='ui-datepicker-week-end'" : "") + ">" + "<span title='" + h[A] + "'>" + p[A] + "</span></th>";
          }k += L + "</tr></thead><tbody>", O = this._getDaysInMonth(et, Z), et === e.selectedYear && Z === e.selectedMonth && (e.selectedDay = Math.min(e.selectedDay, O)), M = (this._getFirstDayOfMonth(et, Z) - l + 7) % 7, _ = Math.ceil((M + O) / 7), D = K ? this.maxRows > _ ? this.maxRows : _ : _, this.maxRows = D, P = this._daylightSavingAdjust(new Date(et, Z, 1 - M));for (H = 0; H < D; H++) {
            k += "<tr>", B = c ? "<td class='ui-datepicker-week-col'>" + this._get(e, "calculateWeek")(P) + "</td>" : "";for (E = 0; E < 7; E++) {
              j = m ? m.apply(e.input ? e.input[0] : null, [P]) : [!0, ""], F = P.getMonth() !== Z, I = F && !y || !j[0] || G && P < G || Y && P > Y, B += "<td class='" + ((E + l + 6) % 7 >= 5 ? " ui-datepicker-week-end" : "") + (F ? " ui-datepicker-other-month" : "") + (P.getTime() === N.getTime() && Z === e.selectedMonth && e._keyEvent || b.getTime() === P.getTime() && b.getTime() === N.getTime() ? " " + this._dayOverClass : "") + (I ? " " + this._unselectableClass + " ui-state-disabled" : "") + (F && !g ? "" : " " + j[1] + (P.getTime() === Q.getTime() ? " " + this._currentClass : "") + (P.getTime() === R.getTime() ? " ui-datepicker-today" : "")) + "'" + ((!F || g) && j[2] ? " title='" + j[2] + "'" : "") + (I ? "" : " data-handler='selectDay' data-event='click' data-month='" + P.getMonth() + "' data-year='" + P.getFullYear() + "'") + ">" + (F && !g ? "&#xa0;" : I ? "<span class='ui-state-default'>" + P.getDate() + "</span>" : "<a class='ui-state-default" + (P.getTime() === R.getTime() ? " ui-state-highlight" : "") + (P.getTime() === Q.getTime() ? " ui-state-active" : "") + (F ? " ui-priority-secondary" : "") + "' href='#'>" + P.getDate() + "</a>") + "</td>", P.setDate(P.getDate() + 1), P = this._daylightSavingAdjust(P);
            }k += B + "</tr>";
          }Z++, Z > 11 && (Z = 0, et++), k += "</tbody></table>" + (K ? "</div>" + (V[0] > 0 && T === V[1] - 1 ? "<div class='ui-datepicker-row-break'></div>" : "") : ""), x += k;
        }w += x;
      }return w += f, e._keyEvent = !1, w;
    }, _generateMonthYearHeader: function _generateMonthYearHeader(e, t, n, r, i, s, o, u) {
      var a,
          f,
          l,
          c,
          h,
          p,
          d,
          v,
          m = this._get(e, "changeMonth"),
          g = this._get(e, "changeYear"),
          y = this._get(e, "showMonthAfterYear"),
          b = "<div class='ui-datepicker-title'>",
          w = "";if (s || !m) w += "<span class='ui-datepicker-month'>" + o[t] + "</span>";else {
        a = r && r.getFullYear() === n, f = i && i.getFullYear() === n, w += "<select class='ui-datepicker-month' data-handler='selectMonth' data-event='change'>";for (l = 0; l < 12; l++) {
          (!a || l >= r.getMonth()) && (!f || l <= i.getMonth()) && (w += "<option value='" + l + "'" + (l === t ? " selected='selected'" : "") + ">" + u[l] + "</option>");
        }w += "</select>";
      }y || (b += w + (s || !m || !g ? "&#xa0;" : ""));if (!e.yearshtml) {
        e.yearshtml = "";if (s || !g) b += "<span class='ui-datepicker-year'>" + n + "</span>";else {
          c = this._get(e, "yearRange").split(":"), h = new Date().getFullYear(), p = function p(e) {
            var t = e.match(/c[+\-].*/) ? n + parseInt(e.substring(1), 10) : e.match(/[+\-].*/) ? h + parseInt(e, 10) : parseInt(e, 10);return isNaN(t) ? h : t;
          }, d = p(c[0]), v = Math.max(d, p(c[1] || "")), d = r ? Math.max(d, r.getFullYear()) : d, v = i ? Math.min(v, i.getFullYear()) : v, e.yearshtml += "<select class='ui-datepicker-year' data-handler='selectYear' data-event='change'>";for (; d <= v; d++) {
            e.yearshtml += "<option value='" + d + "'" + (d === n ? " selected='selected'" : "") + ">" + d + "</option>";
          }e.yearshtml += "</select>", b += e.yearshtml, e.yearshtml = null;
        }
      }return b += this._get(e, "yearSuffix"), y && (b += (s || !m || !g ? "&#xa0;" : "") + w), b += "</div>", b;
    }, _adjustInstDate: function _adjustInstDate(e, t, n) {
      var r = e.drawYear + (n === "Y" ? t : 0),
          i = e.drawMonth + (n === "M" ? t : 0),
          s = Math.min(e.selectedDay, this._getDaysInMonth(r, i)) + (n === "D" ? t : 0),
          o = this._restrictMinMax(e, this._daylightSavingAdjust(new Date(r, i, s)));e.selectedDay = o.getDate(), e.drawMonth = e.selectedMonth = o.getMonth(), e.drawYear = e.selectedYear = o.getFullYear(), (n === "M" || n === "Y") && this._notifyChange(e);
    }, _restrictMinMax: function _restrictMinMax(e, t) {
      var n = this._getMinMaxDate(e, "min"),
          r = this._getMinMaxDate(e, "max"),
          i = n && t < n ? n : t;return r && i > r ? r : i;
    }, _notifyChange: function _notifyChange(e) {
      var t = this._get(e, "onChangeMonthYear");t && t.apply(e.input ? e.input[0] : null, [e.selectedYear, e.selectedMonth + 1, e]);
    }, _getNumberOfMonths: function _getNumberOfMonths(e) {
      var t = this._get(e, "numberOfMonths");return t == null ? [1, 1] : typeof t == "number" ? [1, t] : t;
    }, _getMinMaxDate: function _getMinMaxDate(e, t) {
      return this._determineDate(e, this._get(e, t + "Date"), null);
    }, _getDaysInMonth: function _getDaysInMonth(e, t) {
      return 32 - this._daylightSavingAdjust(new Date(e, t, 32)).getDate();
    }, _getFirstDayOfMonth: function _getFirstDayOfMonth(e, t) {
      return new Date(e, t, 1).getDay();
    }, _canAdjustMonth: function _canAdjustMonth(e, t, n, r) {
      var i = this._getNumberOfMonths(e),
          s = this._daylightSavingAdjust(new Date(n, r + (t < 0 ? t : i[0] * i[1]), 1));return t < 0 && s.setDate(this._getDaysInMonth(s.getFullYear(), s.getMonth())), this._isInRange(e, s);
    }, _isInRange: function _isInRange(e, t) {
      var n,
          r,
          i = this._getMinMaxDate(e, "min"),
          s = this._getMinMaxDate(e, "max"),
          o = null,
          u = null,
          a = this._get(e, "yearRange");return a && (n = a.split(":"), r = new Date().getFullYear(), o = parseInt(n[0], 10) + r, u = parseInt(n[1], 10) + r), (!i || t.getTime() >= i.getTime()) && (!s || t.getTime() <= s.getTime()) && (!o || t.getFullYear() >= o) && (!u || t.getFullYear() <= u);
    }, _getFormatConfig: function _getFormatConfig(e) {
      var t = this._get(e, "shortYearCutoff");return t = typeof t != "string" ? t : new Date().getFullYear() % 100 + parseInt(t, 10), { shortYearCutoff: t, dayNamesShort: this._get(e, "dayNamesShort"), dayNames: this._get(e, "dayNames"), monthNamesShort: this._get(e, "monthNamesShort"), monthNames: this._get(e, "monthNames") };
    }, _formatDate: function _formatDate(e, t, n, r) {
      t || (e.currentDay = e.selectedDay, e.currentMonth = e.selectedMonth, e.currentYear = e.selectedYear);var i = t ? (typeof t === "undefined" ? "undefined" : _typeof(t)) == "object" ? t : this._daylightSavingAdjust(new Date(r, n, t)) : this._daylightSavingAdjust(new Date(e.currentYear, e.currentMonth, e.currentDay));return this.formatDate(this._get(e, "dateFormat"), i, this._getFormatConfig(e));
    } }), e.fn.datepicker = function (t) {
    if (!this.length) return this;e.datepicker.initialized || (e(document).mousedown(e.datepicker._checkExternalClick), e.datepicker.initialized = !0), e("#" + e.datepicker._mainDivId).length === 0 && e("body").append(e.datepicker.dpDiv);var n = Array.prototype.slice.call(arguments, 1);return typeof t != "string" || t !== "isDisabled" && t !== "getDate" && t !== "widget" ? t === "option" && arguments.length === 2 && typeof arguments[1] == "string" ? e.datepicker["_" + t + "Datepicker"].apply(e.datepicker, [this[0]].concat(n)) : this.each(function () {
      typeof t == "string" ? e.datepicker["_" + t + "Datepicker"].apply(e.datepicker, [this].concat(n)) : e.datepicker._attachDatepicker(this, t);
    }) : e.datepicker["_" + t + "Datepicker"].apply(e.datepicker, [this[0]].concat(n));
  }, e.datepicker = new s(), e.datepicker.initialized = !1, e.datepicker.uuid = new Date().getTime(), e.datepicker.version = "1.10.0", window["DP_jQuery_" + r] = e;
})(jQuery);(function (e, t) {
  var n = { buttons: !0, height: !0, maxHeight: !0, maxWidth: !0, minHeight: !0, minWidth: !0, width: !0 },
      r = { maxHeight: !0, maxWidth: !0, minHeight: !0, minWidth: !0 };e.widget("ui.dialog", { version: "1.10.0", options: { appendTo: "body", autoOpen: !0, buttons: [], closeOnEscape: !0, closeText: "close", dialogClass: "", draggable: !0, hide: null, height: "auto", maxHeight: null, maxWidth: null, minHeight: 150, minWidth: 150, modal: !1, position: { my: "center", at: "center", of: window, collision: "fit", using: function using(t) {
          var n = e(this).css(t).offset().top;n < 0 && e(this).css("top", t.top - n);
        } }, resizable: !0, show: null, title: null, width: 300, beforeClose: null, close: null, drag: null, dragStart: null, dragStop: null, focus: null, open: null, resize: null, resizeStart: null, resizeStop: null }, _create: function _create() {
      this.originalCss = { display: this.element[0].style.display, width: this.element[0].style.width, minHeight: this.element[0].style.minHeight, maxHeight: this.element[0].style.maxHeight, height: this.element[0].style.height }, this.originalPosition = { parent: this.element.parent(), index: this.element.parent().children().index(this.element) }, this.originalTitle = this.element.attr("title"), this.options.title = this.options.title || this.originalTitle, this._createWrapper(), this.element.show().removeAttr("title").addClass("ui-dialog-content ui-widget-content").appendTo(this.uiDialog), this._createTitlebar(), this._createButtonPane(), this.options.draggable && e.fn.draggable && this._makeDraggable(), this.options.resizable && e.fn.resizable && this._makeResizable(), this._isOpen = !1;
    }, _init: function _init() {
      this.options.autoOpen && this.open();
    }, _appendTo: function _appendTo() {
      var t = this.options.appendTo;return t && (t.jquery || t.nodeType) ? e(t) : this.document.find(t || "body").eq(0);
    }, _destroy: function _destroy() {
      var e,
          t = this.originalPosition;this._destroyOverlay(), this.element.removeUniqueId().removeClass("ui-dialog-content ui-widget-content").css(this.originalCss).detach(), this.uiDialog.stop(!0, !0).remove(), this.originalTitle && this.element.attr("title", this.originalTitle), e = t.parent.children().eq(t.index), e.length && e[0] !== this.element[0] ? e.before(this.element) : t.parent.append(this.element);
    }, widget: function widget() {
      return this.uiDialog;
    }, disable: e.noop, enable: e.noop, close: function close(t) {
      var n = this;if (!this._isOpen || this._trigger("beforeClose", t) === !1) return;this._isOpen = !1, this._destroyOverlay(), this.opener.filter(":focusable").focus().length || e(this.document[0].activeElement).blur(), this._hide(this.uiDialog, this.options.hide, function () {
        n._trigger("close", t);
      });
    }, isOpen: function isOpen() {
      return this._isOpen;
    }, moveToTop: function moveToTop() {
      this._moveToTop();
    }, _moveToTop: function _moveToTop(e, t) {
      var n = !!this.uiDialog.nextAll(":visible").insertBefore(this.uiDialog).length;return n && !t && this._trigger("focus", e), n;
    }, open: function open() {
      if (this._isOpen) {
        this._moveToTop() && this._focusTabbable();return;
      }this.opener = e(this.document[0].activeElement), this._size(), this._position(), this._createOverlay(), this._moveToTop(null, !0), this._show(this.uiDialog, this.options.show), this._focusTabbable(), this._isOpen = !0, this._trigger("open"), this._trigger("focus");
    }, _focusTabbable: function _focusTabbable() {
      var e = this.element.find("[autofocus]");e.length || (e = this.element.find(":tabbable")), e.length || (e = this.uiDialogButtonPane.find(":tabbable")), e.length || (e = this.uiDialogTitlebarClose.filter(":tabbable")), e.length || (e = this.uiDialog), e.eq(0).focus();
    }, _keepFocus: function _keepFocus(t) {
      function n() {
        var t = this.document[0].activeElement,
            n = this.uiDialog[0] === t || e.contains(this.uiDialog[0], t);n || this._focusTabbable();
      }t.preventDefault(), n.call(this), this._delay(n);
    }, _createWrapper: function _createWrapper() {
      this.uiDialog = e("<div>").addClass("ui-dialog ui-widget ui-widget-content ui-corner-all ui-front " + this.options.dialogClass).hide().attr({ tabIndex: -1, role: "dialog" }).appendTo(this._appendTo()), this._on(this.uiDialog, { keydown: function keydown(t) {
          if (this.options.closeOnEscape && !t.isDefaultPrevented() && t.keyCode && t.keyCode === e.ui.keyCode.ESCAPE) {
            t.preventDefault(), this.close(t);return;
          }if (t.keyCode !== e.ui.keyCode.TAB) return;var n = this.uiDialog.find(":tabbable"),
              r = n.filter(":first"),
              i = n.filter(":last");t.target !== i[0] && t.target !== this.uiDialog[0] || !!t.shiftKey ? (t.target === r[0] || t.target === this.uiDialog[0]) && t.shiftKey && (i.focus(1), t.preventDefault()) : (r.focus(1), t.preventDefault());
        }, mousedown: function mousedown(e) {
          this._moveToTop(e) && this._focusTabbable();
        } }), this.element.find("[aria-describedby]").length || this.uiDialog.attr({ "aria-describedby": this.element.uniqueId().attr("id") });
    }, _createTitlebar: function _createTitlebar() {
      var t;this.uiDialogTitlebar = e("<div>").addClass("ui-dialog-titlebar ui-widget-header ui-corner-all ui-helper-clearfix").prependTo(this.uiDialog), this._on(this.uiDialogTitlebar, { mousedown: function mousedown(t) {
          e(t.target).closest(".ui-dialog-titlebar-close") || this.uiDialog.focus();
        } }), this.uiDialogTitlebarClose = e("<button></button>").button({ label: this.options.closeText, icons: { primary: "ui-icon-closethick" }, text: !1 }).addClass("ui-dialog-titlebar-close").appendTo(this.uiDialogTitlebar), this._on(this.uiDialogTitlebarClose, { click: function click(e) {
          e.preventDefault(), this.close(e);
        } }), t = e("<span>").uniqueId().addClass("ui-dialog-title").prependTo(this.uiDialogTitlebar), this._title(t), this.uiDialog.attr({ "aria-labelledby": t.attr("id") });
    }, _title: function _title(e) {
      this.options.title || e.html("&#160;"), e.text(this.options.title);
    }, _createButtonPane: function _createButtonPane() {
      this.uiDialogButtonPane = e("<div>").addClass("ui-dialog-buttonpane ui-widget-content ui-helper-clearfix"), this.uiButtonSet = e("<div>").addClass("ui-dialog-buttonset").appendTo(this.uiDialogButtonPane), this._createButtons();
    }, _createButtons: function _createButtons() {
      var t = this,
          n = this.options.buttons;this.uiDialogButtonPane.remove(), this.uiButtonSet.empty();if (e.isEmptyObject(n)) {
        this.uiDialog.removeClass("ui-dialog-buttons");return;
      }e.each(n, function (n, r) {
        var i, s;r = e.isFunction(r) ? { click: r, text: n } : r, r = e.extend({ type: "button" }, r), i = r.click, r.click = function () {
          i.apply(t.element[0], arguments);
        }, s = { icons: r.icons, text: r.showText }, delete r.icons, delete r.showText, e("<button></button>", r).button(s).appendTo(t.uiButtonSet);
      }), this.uiDialog.addClass("ui-dialog-buttons"), this.uiDialogButtonPane.appendTo(this.uiDialog);
    }, _makeDraggable: function _makeDraggable() {
      function r(e) {
        return { position: e.position, offset: e.offset };
      }var t = this,
          n = this.options;this.uiDialog.draggable({ cancel: ".ui-dialog-content, .ui-dialog-titlebar-close", handle: ".ui-dialog-titlebar", containment: "document", start: function start(n, i) {
          e(this).addClass("ui-dialog-dragging"), t._trigger("dragStart", n, r(i));
        }, drag: function drag(e, n) {
          t._trigger("drag", e, r(n));
        }, stop: function stop(i, s) {
          n.position = [s.position.left - t.document.scrollLeft(), s.position.top - t.document.scrollTop()], e(this).removeClass("ui-dialog-dragging"), t._trigger("dragStop", i, r(s));
        } });
    }, _makeResizable: function _makeResizable() {
      function o(e) {
        return { originalPosition: e.originalPosition, originalSize: e.originalSize, position: e.position, size: e.size };
      }var t = this,
          n = this.options,
          r = n.resizable,
          i = this.uiDialog.css("position"),
          s = typeof r == "string" ? r : "n,e,s,w,se,sw,ne,nw";this.uiDialog.resizable({ cancel: ".ui-dialog-content", containment: "document", alsoResize: this.element, maxWidth: n.maxWidth, maxHeight: n.maxHeight, minWidth: n.minWidth, minHeight: this._minHeight(), handles: s, start: function start(n, r) {
          e(this).addClass("ui-dialog-resizing"), t._trigger("resizeStart", n, o(r));
        }, resize: function resize(e, n) {
          t._trigger("resize", e, o(n));
        }, stop: function stop(r, i) {
          n.height = e(this).height(), n.width = e(this).width(), e(this).removeClass("ui-dialog-resizing"), t._trigger("resizeStop", r, o(i));
        } }).css("position", i);
    }, _minHeight: function _minHeight() {
      var e = this.options;return e.height === "auto" ? e.minHeight : Math.min(e.minHeight, e.height);
    }, _position: function _position() {
      var e = this.uiDialog.is(":visible");e || this.uiDialog.show(), this.uiDialog.position(this.options.position), e || this.uiDialog.hide();
    }, _setOptions: function _setOptions(t) {
      var i = this,
          s = !1,
          o = {};e.each(t, function (e, t) {
        i._setOption(e, t), e in n && (s = !0), e in r && (o[e] = t);
      }), s && (this._size(), this._position()), this.uiDialog.is(":data(ui-resizable)") && this.uiDialog.resizable("option", o);
    }, _setOption: function _setOption(e, t) {
      var n,
          r,
          i = this.uiDialog;e === "dialogClass" && i.removeClass(this.options.dialogClass).addClass(t);if (e === "disabled") return;this._super(e, t), e === "appendTo" && this.uiDialog.appendTo(this._appendTo()), e === "buttons" && this._createButtons(), e === "closeText" && this.uiDialogTitlebarClose.button({ label: "" + t }), e === "draggable" && (n = i.is(":data(ui-draggable)"), n && !t && i.draggable("destroy"), !n && t && this._makeDraggable()), e === "position" && this._position(), e === "resizable" && (r = i.is(":data(ui-resizable)"), r && !t && i.resizable("destroy"), r && typeof t == "string" && i.resizable("option", "handles", t), !r && t !== !1 && this._makeResizable()), e === "title" && this._title(this.uiDialogTitlebar.find(".ui-dialog-title"));
    }, _size: function _size() {
      var e,
          t,
          n,
          r = this.options;this.element.show().css({ width: "auto", minHeight: 0, maxHeight: "none", height: 0 }), r.minWidth > r.width && (r.width = r.minWidth), e = this.uiDialog.css({ height: "auto", width: r.width }).outerHeight(), t = Math.max(0, r.minHeight - e), n = typeof r.maxHeight == "number" ? Math.max(0, r.maxHeight - e) : "none", r.height === "auto" ? this.element.css({ minHeight: t, maxHeight: n, height: "auto" }) : this.element.height(Math.max(0, r.height - e)), this.uiDialog.is(":data(ui-resizable)") && this.uiDialog.resizable("option", "minHeight", this._minHeight());
    }, _createOverlay: function _createOverlay() {
      if (!this.options.modal) return;e.ui.dialog.overlayInstances || this._delay(function () {
        e.ui.dialog.overlayInstances && this._on(this.document, { focusin: function focusin(t) {
            e(t.target).closest(".ui-dialog").length || (t.preventDefault(), e(".ui-dialog:visible:last .ui-dialog-content").data("ui-dialog")._focusTabbable());
          } });
      }), this.overlay = e("<div>").addClass("ui-widget-overlay ui-front").appendTo(this.document[0].body), this._on(this.overlay, { mousedown: "_keepFocus" }), e.ui.dialog.overlayInstances++;
    }, _destroyOverlay: function _destroyOverlay() {
      if (!this.options.modal) return;e.ui.dialog.overlayInstances--, e.ui.dialog.overlayInstances || this._off(this.document, "focusin"), this.overlay.remove();
    } }), e.ui.dialog.overlayInstances = 0, e.uiBackCompat !== !1 && e.widget("ui.dialog", e.ui.dialog, { _position: function _position() {
      var t = this.options.position,
          n = [],
          r = [0, 0],
          i;if (t) {
        if (typeof t == "string" || (typeof t === "undefined" ? "undefined" : _typeof(t)) == "object" && "0" in t) n = t.split ? t.split(" ") : [t[0], t[1]], n.length === 1 && (n[1] = n[0]), e.each(["left", "top"], function (e, t) {
          +n[e] === n[e] && (r[e] = n[e], n[e] = t);
        }), t = { my: n[0] + (r[0] < 0 ? r[0] : "+" + r[0]) + " " + n[1] + (r[1] < 0 ? r[1] : "+" + r[1]), at: n.join(" ") };t = e.extend({}, e.ui.dialog.prototype.options.position, t);
      } else t = e.ui.dialog.prototype.options.position;i = this.uiDialog.is(":visible"), i || this.uiDialog.show(), this.uiDialog.position(t), i || this.uiDialog.hide();
    } });
})(jQuery);(function (e, t) {
  e.widget("ui.menu", { version: "1.10.0", defaultElement: "<ul>", delay: 300, options: { icons: { submenu: "ui-icon-carat-1-e" }, menus: "ul", position: { my: "left top", at: "right top" }, role: "menu", blur: null, focus: null, select: null }, _create: function _create() {
      this.activeMenu = this.element, this.mouseHandled = !1, this.element.uniqueId().addClass("ui-menu ui-widget ui-widget-content ui-corner-all").toggleClass("ui-menu-icons", !!this.element.find(".ui-icon").length).attr({ role: this.options.role, tabIndex: 0 }).bind("click" + this.eventNamespace, e.proxy(function (e) {
        this.options.disabled && e.preventDefault();
      }, this)), this.options.disabled && this.element.addClass("ui-state-disabled").attr("aria-disabled", "true"), this._on({ "mousedown .ui-menu-item > a": function mousedownUiMenuItemA(e) {
          e.preventDefault();
        }, "click .ui-state-disabled > a": function clickUiStateDisabledA(e) {
          e.preventDefault();
        }, "click .ui-menu-item:has(a)": function clickUiMenuItemHasA(t) {
          var n = e(t.target).closest(".ui-menu-item");!this.mouseHandled && n.not(".ui-state-disabled").length && (this.mouseHandled = !0, this.select(t), n.has(".ui-menu").length ? this.expand(t) : this.element.is(":focus") || (this.element.trigger("focus", [!0]), this.active && this.active.parents(".ui-menu").length === 1 && clearTimeout(this.timer)));
        }, "mouseenter .ui-menu-item": function mouseenterUiMenuItem(t) {
          var n = e(t.currentTarget);n.siblings().children(".ui-state-active").removeClass("ui-state-active"), this.focus(t, n);
        }, mouseleave: "collapseAll", "mouseleave .ui-menu": "collapseAll", focus: function focus(e, t) {
          var n = this.active || this.element.children(".ui-menu-item").eq(0);t || this.focus(e, n);
        }, blur: function blur(t) {
          this._delay(function () {
            e.contains(this.element[0], this.document[0].activeElement) || this.collapseAll(t);
          });
        }, keydown: "_keydown" }), this.refresh(), this._on(this.document, { click: function click(t) {
          e(t.target).closest(".ui-menu").length || this.collapseAll(t), this.mouseHandled = !1;
        } });
    }, _destroy: function _destroy() {
      this.element.removeAttr("aria-activedescendant").find(".ui-menu").addBack().removeClass("ui-menu ui-widget ui-widget-content ui-corner-all ui-menu-icons").removeAttr("role").removeAttr("tabIndex").removeAttr("aria-labelledby").removeAttr("aria-expanded").removeAttr("aria-hidden").removeAttr("aria-disabled").removeUniqueId().show(), this.element.find(".ui-menu-item").removeClass("ui-menu-item").removeAttr("role").removeAttr("aria-disabled").children("a").removeUniqueId().removeClass("ui-corner-all ui-state-hover").removeAttr("tabIndex").removeAttr("role").removeAttr("aria-haspopup").children().each(function () {
        var t = e(this);t.data("ui-menu-submenu-carat") && t.remove();
      }), this.element.find(".ui-menu-divider").removeClass("ui-menu-divider ui-widget-content");
    }, _keydown: function _keydown(t) {
      function a(e) {
        return e.replace(/[\-\[\]{}()*+?.,\\\^$|#\s]/g, "\\$&");
      }var n,
          r,
          i,
          s,
          o,
          u = !0;switch (t.keyCode) {case e.ui.keyCode.PAGE_UP:
          this.previousPage(t);break;case e.ui.keyCode.PAGE_DOWN:
          this.nextPage(t);break;case e.ui.keyCode.HOME:
          this._move("first", "first", t);break;case e.ui.keyCode.END:
          this._move("last", "last", t);break;case e.ui.keyCode.UP:
          this.previous(t);break;case e.ui.keyCode.DOWN:
          this.next(t);break;case e.ui.keyCode.LEFT:
          this.collapse(t);break;case e.ui.keyCode.RIGHT:
          this.active && !this.active.is(".ui-state-disabled") && this.expand(t);break;case e.ui.keyCode.ENTER:case e.ui.keyCode.SPACE:
          this._activate(t);break;case e.ui.keyCode.ESCAPE:
          this.collapse(t);break;default:
          u = !1, r = this.previousFilter || "", i = String.fromCharCode(t.keyCode), s = !1, clearTimeout(this.filterTimer), i === r ? s = !0 : i = r + i, o = new RegExp("^" + a(i), "i"), n = this.activeMenu.children(".ui-menu-item").filter(function () {
            return o.test(e(this).children("a").text());
          }), n = s && n.index(this.active.next()) !== -1 ? this.active.nextAll(".ui-menu-item") : n, n.length || (i = String.fromCharCode(t.keyCode), o = new RegExp("^" + a(i), "i"), n = this.activeMenu.children(".ui-menu-item").filter(function () {
            return o.test(e(this).children("a").text());
          })), n.length ? (this.focus(t, n), n.length > 1 ? (this.previousFilter = i, this.filterTimer = this._delay(function () {
            delete this.previousFilter;
          }, 1e3)) : delete this.previousFilter) : delete this.previousFilter;}u && t.preventDefault();
    }, _activate: function _activate(e) {
      this.active.is(".ui-state-disabled") || (this.active.children("a[aria-haspopup='true']").length ? this.expand(e) : this.select(e));
    }, refresh: function refresh() {
      var t,
          n = this.options.icons.submenu,
          r = this.element.find(this.options.menus);r.filter(":not(.ui-menu)").addClass("ui-menu ui-widget ui-widget-content ui-corner-all").hide().attr({ role: this.options.role, "aria-hidden": "true", "aria-expanded": "false" }).each(function () {
        var t = e(this),
            r = t.prev("a"),
            i = e("<span>").addClass("ui-menu-icon ui-icon " + n).data("ui-menu-submenu-carat", !0);r.attr("aria-haspopup", "true").prepend(i), t.attr("aria-labelledby", r.attr("id"));
      }), t = r.add(this.element), t.children(":not(.ui-menu-item):has(a)").addClass("ui-menu-item").attr("role", "presentation").children("a").uniqueId().addClass("ui-corner-all").attr({ tabIndex: -1, role: this._itemRole() }), t.children(":not(.ui-menu-item)").each(function () {
        var t = e(this);/[^\-—–\s]/.test(t.text()) || t.addClass("ui-widget-content ui-menu-divider");
      }), t.children(".ui-state-disabled").attr("aria-disabled", "true"), this.active && !e.contains(this.element[0], this.active[0]) && this.blur();
    }, _itemRole: function _itemRole() {
      return { menu: "menuitem", listbox: "option" }[this.options.role];
    }, _setOption: function _setOption(e, t) {
      e === "icons" && this.element.find(".ui-menu-icon").removeClass(this.options.icons.submenu).addClass(t.submenu), this._super(e, t);
    }, focus: function focus(e, t) {
      var n, r;this.blur(e, e && e.type === "focus"), this._scrollIntoView(t), this.active = t.first(), r = this.active.children("a").addClass("ui-state-focus"), this.options.role && this.element.attr("aria-activedescendant", r.attr("id")), this.active.parent().closest(".ui-menu-item").children("a:first").addClass("ui-state-active"), e && e.type === "keydown" ? this._close() : this.timer = this._delay(function () {
        this._close();
      }, this.delay), n = t.children(".ui-menu"), n.length && /^mouse/.test(e.type) && this._startOpening(n), this.activeMenu = t.parent(), this._trigger("focus", e, { item: t });
    }, _scrollIntoView: function _scrollIntoView(t) {
      var n, r, i, s, o, u;this._hasScroll() && (n = parseFloat(e.css(this.activeMenu[0], "borderTopWidth")) || 0, r = parseFloat(e.css(this.activeMenu[0], "paddingTop")) || 0, i = t.offset().top - this.activeMenu.offset().top - n - r, s = this.activeMenu.scrollTop(), o = this.activeMenu.height(), u = t.height(), i < 0 ? this.activeMenu.scrollTop(s + i) : i + u > o && this.activeMenu.scrollTop(s + i - o + u));
    }, blur: function blur(e, t) {
      t || clearTimeout(this.timer);if (!this.active) return;this.active.children("a").removeClass("ui-state-focus"), this.active = null, this._trigger("blur", e, { item: this.active });
    }, _startOpening: function _startOpening(e) {
      clearTimeout(this.timer);if (e.attr("aria-hidden") !== "true") return;this.timer = this._delay(function () {
        this._close(), this._open(e);
      }, this.delay);
    }, _open: function _open(t) {
      var n = e.extend({ of: this.active }, this.options.position);clearTimeout(this.timer), this.element.find(".ui-menu").not(t.parents(".ui-menu")).hide().attr("aria-hidden", "true"), t.show().removeAttr("aria-hidden").attr("aria-expanded", "true").position(n);
    }, collapseAll: function collapseAll(t, n) {
      clearTimeout(this.timer), this.timer = this._delay(function () {
        var r = n ? this.element : e(t && t.target).closest(this.element.find(".ui-menu"));r.length || (r = this.element), this._close(r), this.blur(t), this.activeMenu = r;
      }, this.delay);
    }, _close: function _close(e) {
      e || (e = this.active ? this.active.parent() : this.element), e.find(".ui-menu").hide().attr("aria-hidden", "true").attr("aria-expanded", "false").end().find("a.ui-state-active").removeClass("ui-state-active");
    }, collapse: function collapse(e) {
      var t = this.active && this.active.parent().closest(".ui-menu-item", this.element);t && t.length && (this._close(), this.focus(e, t));
    }, expand: function expand(e) {
      var t = this.active && this.active.children(".ui-menu ").children(".ui-menu-item").first();t && t.length && (this._open(t.parent()), this._delay(function () {
        this.focus(e, t);
      }));
    }, next: function next(e) {
      this._move("next", "first", e);
    }, previous: function previous(e) {
      this._move("prev", "last", e);
    }, isFirstItem: function isFirstItem() {
      return this.active && !this.active.prevAll(".ui-menu-item").length;
    }, isLastItem: function isLastItem() {
      return this.active && !this.active.nextAll(".ui-menu-item").length;
    }, _move: function _move(e, t, n) {
      var r;this.active && (e === "first" || e === "last" ? r = this.active[e === "first" ? "prevAll" : "nextAll"](".ui-menu-item").eq(-1) : r = this.active[e + "All"](".ui-menu-item").eq(0));if (!r || !r.length || !this.active) r = this.activeMenu.children(".ui-menu-item")[t]();this.focus(n, r);
    }, nextPage: function nextPage(t) {
      var n, r, i;if (!this.active) {
        this.next(t);return;
      }if (this.isLastItem()) return;this._hasScroll() ? (r = this.active.offset().top, i = this.element.height(), this.active.nextAll(".ui-menu-item").each(function () {
        return n = e(this), n.offset().top - r - i < 0;
      }), this.focus(t, n)) : this.focus(t, this.activeMenu.children(".ui-menu-item")[this.active ? "last" : "first"]());
    }, previousPage: function previousPage(t) {
      var n, r, i;if (!this.active) {
        this.next(t);return;
      }if (this.isFirstItem()) return;this._hasScroll() ? (r = this.active.offset().top, i = this.element.height(), this.active.prevAll(".ui-menu-item").each(function () {
        return n = e(this), n.offset().top - r + i > 0;
      }), this.focus(t, n)) : this.focus(t, this.activeMenu.children(".ui-menu-item").first());
    }, _hasScroll: function _hasScroll() {
      return this.element.outerHeight() < this.element.prop("scrollHeight");
    }, select: function select(t) {
      this.active = this.active || e(t.target).closest(".ui-menu-item");var n = { item: this.active };this.active.has(".ui-menu").length || this.collapseAll(t, !0), this._trigger("select", t, n);
    } });
})(jQuery);(function (e, t) {
  e.widget("ui.progressbar", { version: "1.10.0", options: { max: 100, value: 0, change: null, complete: null }, min: 0, _create: function _create() {
      this.oldValue = this.options.value = this._constrainedValue(), this.element.addClass("ui-progressbar ui-widget ui-widget-content ui-corner-all").attr({ role: "progressbar", "aria-valuemin": this.min }), this.valueDiv = e("<div class='ui-progressbar-value ui-widget-header ui-corner-left'></div>").appendTo(this.element), this._refreshValue();
    }, _destroy: function _destroy() {
      this.element.removeClass("ui-progressbar ui-widget ui-widget-content ui-corner-all").removeAttr("role").removeAttr("aria-valuemin").removeAttr("aria-valuemax").removeAttr("aria-valuenow"), this.valueDiv.remove();
    }, value: function value(e) {
      if (e === t) return this.options.value;this.options.value = this._constrainedValue(e), this._refreshValue();
    }, _constrainedValue: function _constrainedValue(e) {
      return e === t && (e = this.options.value), this.indeterminate = e === !1, typeof e != "number" && (e = 0), this.indeterminate ? !1 : Math.min(this.options.max, Math.max(this.min, e));
    }, _setOptions: function _setOptions(e) {
      var t = e.value;delete e.value, this._super(e), this.options.value = this._constrainedValue(t), this._refreshValue();
    }, _setOption: function _setOption(e, t) {
      e === "max" && (t = Math.max(this.min, t)), this._super(e, t);
    }, _percentage: function _percentage() {
      return this.indeterminate ? 100 : 100 * (this.options.value - this.min) / (this.options.max - this.min);
    }, _refreshValue: function _refreshValue() {
      var t = this.options.value,
          n = this._percentage();this.valueDiv.toggle(this.indeterminate || t > this.min).toggleClass("ui-corner-right", t === this.options.max).width(n.toFixed(0) + "%"), this.element.toggleClass("ui-progressbar-indeterminate", this.indeterminate), this.indeterminate ? (this.element.removeAttr("aria-valuenow"), this.overlayDiv || (this.overlayDiv = e("<div class='ui-progressbar-overlay'></div>").appendTo(this.valueDiv))) : (this.element.attr({ "aria-valuemax": this.options.max, "aria-valuenow": t }), this.overlayDiv && (this.overlayDiv.remove(), this.overlayDiv = null)), this.oldValue !== t && (this.oldValue = t, this._trigger("change")), t === this.options.max && this._trigger("complete");
    } });
})(jQuery);(function (e, t) {
  var n = 5;e.widget("ui.slider", e.ui.mouse, { version: "1.10.0", widgetEventPrefix: "slide", options: { animate: !1, distance: 0, max: 100, min: 0, orientation: "horizontal", range: !1, step: 1, value: 0, values: null, change: null, slide: null, start: null, stop: null }, _create: function _create() {
      var t,
          n,
          r = this.options,
          i = this.element.find(".ui-slider-handle").addClass("ui-state-default ui-corner-all"),
          s = "<a class='ui-slider-handle ui-state-default ui-corner-all' href='#'></a>",
          o = [];this._keySliding = !1, this._mouseSliding = !1, this._animateOff = !0, this._handleIndex = null, this._detectOrientation(), this._mouseInit(), this.element.addClass("ui-slider ui-slider-" + this.orientation + " ui-widget" + " ui-widget-content" + " ui-corner-all"), this.range = e([]), r.range && (r.range === !0 && (r.values ? r.values.length && r.values.length !== 2 ? r.values = [r.values[0], r.values[0]] : e.isArray(r.values) && (r.values = r.values.slice(0)) : r.values = [this._valueMin(), this._valueMin()]), this.range = e("<div></div>").appendTo(this.element).addClass("ui-slider-range ui-widget-header" + (r.range === "min" || r.range === "max" ? " ui-slider-range-" + r.range : ""))), n = r.values && r.values.length || 1;for (t = i.length; t < n; t++) {
        o.push(s);
      }this.handles = i.add(e(o.join("")).appendTo(this.element)), this.handle = this.handles.eq(0), this.handles.add(this.range).filter("a").click(function (e) {
        e.preventDefault();
      }).mouseenter(function () {
        r.disabled || e(this).addClass("ui-state-hover");
      }).mouseleave(function () {
        e(this).removeClass("ui-state-hover");
      }).focus(function () {
        r.disabled ? e(this).blur() : (e(".ui-slider .ui-state-focus").removeClass("ui-state-focus"), e(this).addClass("ui-state-focus"));
      }).blur(function () {
        e(this).removeClass("ui-state-focus");
      }), this.handles.each(function (t) {
        e(this).data("ui-slider-handle-index", t);
      }), this._setOption("disabled", r.disabled), this._on(this.handles, this._handleEvents), this._refreshValue(), this._animateOff = !1;
    }, _destroy: function _destroy() {
      this.handles.remove(), this.range.remove(), this.element.removeClass("ui-slider ui-slider-horizontal ui-slider-vertical ui-widget ui-widget-content ui-corner-all"), this._mouseDestroy();
    }, _mouseCapture: function _mouseCapture(t) {
      var n,
          r,
          i,
          s,
          o,
          u,
          a,
          f,
          l = this,
          c = this.options;return c.disabled ? !1 : (this.elementSize = { width: this.element.outerWidth(), height: this.element.outerHeight() }, this.elementOffset = this.element.offset(), n = { x: t.pageX, y: t.pageY }, r = this._normValueFromMouse(n), i = this._valueMax() - this._valueMin() + 1, this.handles.each(function (t) {
        var n = Math.abs(r - l.values(t));if (i > n || i === n && (t === l._lastChangedValue || l.values(t) === c.min)) i = n, s = e(this), o = t;
      }), u = this._start(t, o), u === !1 ? !1 : (this._mouseSliding = !0, this._handleIndex = o, s.addClass("ui-state-active").focus(), a = s.offset(), f = !e(t.target).parents().addBack().is(".ui-slider-handle"), this._clickOffset = f ? { left: 0, top: 0 } : { left: t.pageX - a.left - s.width() / 2, top: t.pageY - a.top - s.height() / 2 - (parseInt(s.css("borderTopWidth"), 10) || 0) - (parseInt(s.css("borderBottomWidth"), 10) || 0) + (parseInt(s.css("marginTop"), 10) || 0) }, this.handles.hasClass("ui-state-hover") || this._slide(t, o, r), this._animateOff = !0, !0));
    }, _mouseStart: function _mouseStart() {
      return !0;
    }, _mouseDrag: function _mouseDrag(e) {
      var t = { x: e.pageX, y: e.pageY },
          n = this._normValueFromMouse(t);return this._slide(e, this._handleIndex, n), !1;
    }, _mouseStop: function _mouseStop(e) {
      return this.handles.removeClass("ui-state-active"), this._mouseSliding = !1, this._stop(e, this._handleIndex), this._change(e, this._handleIndex), this._handleIndex = null, this._clickOffset = null, this._animateOff = !1, !1;
    }, _detectOrientation: function _detectOrientation() {
      this.orientation = this.options.orientation === "vertical" ? "vertical" : "horizontal";
    }, _normValueFromMouse: function _normValueFromMouse(e) {
      var t, n, r, i, s;return this.orientation === "horizontal" ? (t = this.elementSize.width, n = e.x - this.elementOffset.left - (this._clickOffset ? this._clickOffset.left : 0)) : (t = this.elementSize.height, n = e.y - this.elementOffset.top - (this._clickOffset ? this._clickOffset.top : 0)), r = n / t, r > 1 && (r = 1), r < 0 && (r = 0), this.orientation === "vertical" && (r = 1 - r), i = this._valueMax() - this._valueMin(), s = this._valueMin() + r * i, this._trimAlignValue(s);
    }, _start: function _start(e, t) {
      var n = { handle: this.handles[t], value: this.value() };return this.options.values && this.options.values.length && (n.value = this.values(t), n.values = this.values()), this._trigger("start", e, n);
    }, _slide: function _slide(e, t, n) {
      var r, i, s;this.options.values && this.options.values.length ? (r = this.values(t ? 0 : 1), this.options.values.length === 2 && this.options.range === !0 && (t === 0 && n > r || t === 1 && n < r) && (n = r), n !== this.values(t) && (i = this.values(), i[t] = n, s = this._trigger("slide", e, { handle: this.handles[t], value: n, values: i }), r = this.values(t ? 0 : 1), s !== !1 && this.values(t, n, !0))) : n !== this.value() && (s = this._trigger("slide", e, { handle: this.handles[t], value: n }), s !== !1 && this.value(n));
    }, _stop: function _stop(e, t) {
      var n = { handle: this.handles[t], value: this.value() };this.options.values && this.options.values.length && (n.value = this.values(t), n.values = this.values()), this._trigger("stop", e, n);
    }, _change: function _change(e, t) {
      if (!this._keySliding && !this._mouseSliding) {
        var n = { handle: this.handles[t], value: this.value() };this.options.values && this.options.values.length && (n.value = this.values(t), n.values = this.values()), this._lastChangedValue = t, this._trigger("change", e, n);
      }
    }, value: function value(e) {
      if (arguments.length) {
        this.options.value = this._trimAlignValue(e), this._refreshValue(), this._change(null, 0);return;
      }return this._value();
    }, values: function values(t, n) {
      var r, i, s;if (arguments.length > 1) {
        this.options.values[t] = this._trimAlignValue(n), this._refreshValue(), this._change(null, t);return;
      }if (!arguments.length) return this._values();if (!e.isArray(arguments[0])) return this.options.values && this.options.values.length ? this._values(t) : this.value();r = this.options.values, i = arguments[0];for (s = 0; s < r.length; s += 1) {
        r[s] = this._trimAlignValue(i[s]), this._change(null, s);
      }this._refreshValue();
    }, _setOption: function _setOption(t, n) {
      var r,
          i = 0;e.isArray(this.options.values) && (i = this.options.values.length), e.Widget.prototype._setOption.apply(this, arguments);switch (t) {case "disabled":
          n ? (this.handles.filter(".ui-state-focus").blur(), this.handles.removeClass("ui-state-hover"), this.handles.prop("disabled", !0)) : this.handles.prop("disabled", !1);break;case "orientation":
          this._detectOrientation(), this.element.removeClass("ui-slider-horizontal ui-slider-vertical").addClass("ui-slider-" + this.orientation), this._refreshValue();break;case "value":
          this._animateOff = !0, this._refreshValue(), this._change(null, 0), this._animateOff = !1;break;case "values":
          this._animateOff = !0, this._refreshValue();for (r = 0; r < i; r += 1) {
            this._change(null, r);
          }this._animateOff = !1;break;case "min":case "max":
          this._animateOff = !0, this._refreshValue(), this._animateOff = !1;}
    }, _value: function _value() {
      var e = this.options.value;return e = this._trimAlignValue(e), e;
    }, _values: function _values(e) {
      var t, n, r;if (arguments.length) return t = this.options.values[e], t = this._trimAlignValue(t), t;n = this.options.values.slice();for (r = 0; r < n.length; r += 1) {
        n[r] = this._trimAlignValue(n[r]);
      }return n;
    }, _trimAlignValue: function _trimAlignValue(e) {
      if (e <= this._valueMin()) return this._valueMin();if (e >= this._valueMax()) return this._valueMax();var t = this.options.step > 0 ? this.options.step : 1,
          n = (e - this._valueMin()) % t,
          r = e - n;return Math.abs(n) * 2 >= t && (r += n > 0 ? t : -t), parseFloat(r.toFixed(5));
    }, _valueMin: function _valueMin() {
      return this.options.min;
    }, _valueMax: function _valueMax() {
      return this.options.max;
    }, _refreshValue: function _refreshValue() {
      var t,
          n,
          r,
          i,
          s,
          o = this.options.range,
          u = this.options,
          a = this,
          f = this._animateOff ? !1 : u.animate,
          l = {};this.options.values && this.options.values.length ? this.handles.each(function (r) {
        n = (a.values(r) - a._valueMin()) / (a._valueMax() - a._valueMin()) * 100, l[a.orientation === "horizontal" ? "left" : "bottom"] = n + "%", e(this).stop(1, 1)[f ? "animate" : "css"](l, u.animate), a.options.range === !0 && (a.orientation === "horizontal" ? (r === 0 && a.range.stop(1, 1)[f ? "animate" : "css"]({ left: n + "%" }, u.animate), r === 1 && a.range[f ? "animate" : "css"]({ width: n - t + "%" }, { queue: !1, duration: u.animate })) : (r === 0 && a.range.stop(1, 1)[f ? "animate" : "css"]({ bottom: n + "%" }, u.animate), r === 1 && a.range[f ? "animate" : "css"]({ height: n - t + "%" }, { queue: !1, duration: u.animate }))), t = n;
      }) : (r = this.value(), i = this._valueMin(), s = this._valueMax(), n = s !== i ? (r - i) / (s - i) * 100 : 0, l[this.orientation === "horizontal" ? "left" : "bottom"] = n + "%", this.handle.stop(1, 1)[f ? "animate" : "css"](l, u.animate), o === "min" && this.orientation === "horizontal" && this.range.stop(1, 1)[f ? "animate" : "css"]({ width: n + "%" }, u.animate), o === "max" && this.orientation === "horizontal" && this.range[f ? "animate" : "css"]({ width: 100 - n + "%" }, { queue: !1, duration: u.animate }), o === "min" && this.orientation === "vertical" && this.range.stop(1, 1)[f ? "animate" : "css"]({ height: n + "%" }, u.animate), o === "max" && this.orientation === "vertical" && this.range[f ? "animate" : "css"]({ height: 100 - n + "%" }, { queue: !1, duration: u.animate }));
    }, _handleEvents: { keydown: function keydown(t) {
        var r,
            i,
            s,
            o,
            u = e(t.target).data("ui-slider-handle-index");switch (t.keyCode) {case e.ui.keyCode.HOME:case e.ui.keyCode.END:case e.ui.keyCode.PAGE_UP:case e.ui.keyCode.PAGE_DOWN:case e.ui.keyCode.UP:case e.ui.keyCode.RIGHT:case e.ui.keyCode.DOWN:case e.ui.keyCode.LEFT:
            t.preventDefault();if (!this._keySliding) {
              this._keySliding = !0, e(t.target).addClass("ui-state-active"), r = this._start(t, u);if (r === !1) return;
            }}o = this.options.step, this.options.values && this.options.values.length ? i = s = this.values(u) : i = s = this.value();switch (t.keyCode) {case e.ui.keyCode.HOME:
            s = this._valueMin();break;case e.ui.keyCode.END:
            s = this._valueMax();break;case e.ui.keyCode.PAGE_UP:
            s = this._trimAlignValue(i + (this._valueMax() - this._valueMin()) / n);break;case e.ui.keyCode.PAGE_DOWN:
            s = this._trimAlignValue(i - (this._valueMax() - this._valueMin()) / n);break;case e.ui.keyCode.UP:case e.ui.keyCode.RIGHT:
            if (i === this._valueMax()) return;s = this._trimAlignValue(i + o);break;case e.ui.keyCode.DOWN:case e.ui.keyCode.LEFT:
            if (i === this._valueMin()) return;s = this._trimAlignValue(i - o);}this._slide(t, u, s);
      }, keyup: function keyup(t) {
        var n = e(t.target).data("ui-slider-handle-index");this._keySliding && (this._keySliding = !1, this._stop(t, n), this._change(t, n), e(t.target).removeClass("ui-state-active"));
      } } });
})(jQuery);(function (e) {
  function t(e) {
    return function () {
      var t = this.element.val();e.apply(this, arguments), this._refresh(), t !== this.element.val() && this._trigger("change");
    };
  }e.widget("ui.spinner", { version: "1.10.0", defaultElement: "<input>", widgetEventPrefix: "spin", options: { culture: null, icons: { down: "ui-icon-triangle-1-s", up: "ui-icon-triangle-1-n" }, incremental: !0, max: null, min: null, numberFormat: null, page: 10, step: 1, change: null, spin: null, start: null, stop: null }, _create: function _create() {
      this._setOption("max", this.options.max), this._setOption("min", this.options.min), this._setOption("step", this.options.step), this._value(this.element.val(), !0), this._draw(), this._on(this._events), this._refresh(), this._on(this.window, { beforeunload: function beforeunload() {
          this.element.removeAttr("autocomplete");
        } });
    }, _getCreateOptions: function _getCreateOptions() {
      var t = {},
          n = this.element;return e.each(["min", "max", "step"], function (e, r) {
        var i = n.attr(r);i !== undefined && i.length && (t[r] = i);
      }), t;
    }, _events: { keydown: function keydown(e) {
        this._start(e) && this._keydown(e) && e.preventDefault();
      }, keyup: "_stop", focus: function focus() {
        this.previous = this.element.val();
      }, blur: function blur(e) {
        if (this.cancelBlur) {
          delete this.cancelBlur;return;
        }this._refresh(), this.previous !== this.element.val() && this._trigger("change", e);
      }, mousewheel: function mousewheel(e, t) {
        if (!t) return;if (!this.spinning && !this._start(e)) return !1;this._spin((t > 0 ? 1 : -1) * this.options.step, e), clearTimeout(this.mousewheelTimer), this.mousewheelTimer = this._delay(function () {
          this.spinning && this._stop(e);
        }, 100), e.preventDefault();
      }, "mousedown .ui-spinner-button": function mousedownUiSpinnerButton(t) {
        function r() {
          var e = this.element[0] === this.document[0].activeElement;e || (this.element.focus(), this.previous = n, this._delay(function () {
            this.previous = n;
          }));
        }var n;n = this.element[0] === this.document[0].activeElement ? this.previous : this.element.val(), t.preventDefault(), r.call(this), this.cancelBlur = !0, this._delay(function () {
          delete this.cancelBlur, r.call(this);
        });if (this._start(t) === !1) return;this._repeat(null, e(t.currentTarget).hasClass("ui-spinner-up") ? 1 : -1, t);
      }, "mouseup .ui-spinner-button": "_stop", "mouseenter .ui-spinner-button": function mouseenterUiSpinnerButton(t) {
        if (!e(t.currentTarget).hasClass("ui-state-active")) return;if (this._start(t) === !1) return !1;this._repeat(null, e(t.currentTarget).hasClass("ui-spinner-up") ? 1 : -1, t);
      }, "mouseleave .ui-spinner-button": "_stop" }, _draw: function _draw() {
      var e = this.uiSpinner = this.element.addClass("ui-spinner-input").attr("autocomplete", "off").wrap(this._uiSpinnerHtml()).parent().append(this._buttonHtml());this.element.attr("role", "spinbutton"), this.buttons = e.find(".ui-spinner-button").attr("tabIndex", -1).button().removeClass("ui-corner-all"), this.buttons.height() > Math.ceil(e.height() * .5) && e.height() > 0 && e.height(e.height()), this.options.disabled && this.disable();
    }, _keydown: function _keydown(t) {
      var n = this.options,
          r = e.ui.keyCode;switch (t.keyCode) {case r.UP:
          return this._repeat(null, 1, t), !0;case r.DOWN:
          return this._repeat(null, -1, t), !0;case r.PAGE_UP:
          return this._repeat(null, n.page, t), !0;case r.PAGE_DOWN:
          return this._repeat(null, -n.page, t), !0;}return !1;
    }, _uiSpinnerHtml: function _uiSpinnerHtml() {
      return "<span class='ui-spinner ui-widget ui-widget-content ui-corner-all'></span>";
    }, _buttonHtml: function _buttonHtml() {
      return "<a class='ui-spinner-button ui-spinner-up ui-corner-tr'><span class='ui-icon " + this.options.icons.up + "'>&#9650;</span>" + "</a>" + "<a class='ui-spinner-button ui-spinner-down ui-corner-br'>" + "<span class='ui-icon " + this.options.icons.down + "'>&#9660;</span>" + "</a>";
    }, _start: function _start(e) {
      return !this.spinning && this._trigger("start", e) === !1 ? !1 : (this.counter || (this.counter = 1), this.spinning = !0, !0);
    }, _repeat: function _repeat(e, t, n) {
      e = e || 500, clearTimeout(this.timer), this.timer = this._delay(function () {
        this._repeat(40, t, n);
      }, e), this._spin(t * this.options.step, n);
    }, _spin: function _spin(e, t) {
      var n = this.value() || 0;this.counter || (this.counter = 1), n = this._adjustValue(n + e * this._increment(this.counter));if (!this.spinning || this._trigger("spin", t, { value: n }) !== !1) this._value(n), this.counter++;
    }, _increment: function _increment(t) {
      var n = this.options.incremental;return n ? e.isFunction(n) ? n(t) : Math.floor(t * t * t / 5e4 - t * t / 500 + 17 * t / 200 + 1) : 1;
    }, _precision: function _precision() {
      var e = this._precisionOf(this.options.step);return this.options.min !== null && (e = Math.max(e, this._precisionOf(this.options.min))), e;
    }, _precisionOf: function _precisionOf(e) {
      var t = e.toString(),
          n = t.indexOf(".");return n === -1 ? 0 : t.length - n - 1;
    }, _adjustValue: function _adjustValue(e) {
      var t,
          n,
          r = this.options;return t = r.min !== null ? r.min : 0, n = e - t, n = Math.round(n / r.step) * r.step, e = t + n, e = parseFloat(e.toFixed(this._precision())), r.max !== null && e > r.max ? r.max : r.min !== null && e < r.min ? r.min : e;
    }, _stop: function _stop(e) {
      if (!this.spinning) return;clearTimeout(this.timer), clearTimeout(this.mousewheelTimer), this.counter = 0, this.spinning = !1, this._trigger("stop", e);
    }, _setOption: function _setOption(e, t) {
      if (e === "culture" || e === "numberFormat") {
        var n = this._parse(this.element.val());this.options[e] = t, this.element.val(this._format(n));return;
      }(e === "max" || e === "min" || e === "step") && typeof t == "string" && (t = this._parse(t)), e === "icons" && (this.buttons.first().find(".ui-icon").removeClass(this.options.icons.up).addClass(t.up), this.buttons.last().find(".ui-icon").removeClass(this.options.icons.down).addClass(t.down)), this._super(e, t), e === "disabled" && (t ? (this.element.prop("disabled", !0), this.buttons.button("disable")) : (this.element.prop("disabled", !1), this.buttons.button("enable")));
    }, _setOptions: t(function (e) {
      this._super(e), this._value(this.element.val());
    }), _parse: function _parse(e) {
      return typeof e == "string" && e !== "" && (e = window.Globalize && this.options.numberFormat ? Globalize.parseFloat(e, 10, this.options.culture) : +e), e === "" || isNaN(e) ? null : e;
    }, _format: function _format(e) {
      return e === "" ? "" : window.Globalize && this.options.numberFormat ? Globalize.format(e, this.options.numberFormat, this.options.culture) : e;
    }, _refresh: function _refresh() {
      this.element.attr({ "aria-valuemin": this.options.min, "aria-valuemax": this.options.max, "aria-valuenow": this._parse(this.element.val()) });
    }, _value: function _value(e, t) {
      var n;e !== "" && (n = this._parse(e), n !== null && (t || (n = this._adjustValue(n)), e = this._format(n))), this.element.val(e), this._refresh();
    }, _destroy: function _destroy() {
      this.element.removeClass("ui-spinner-input").prop("disabled", !1).removeAttr("autocomplete").removeAttr("role").removeAttr("aria-valuemin").removeAttr("aria-valuemax").removeAttr("aria-valuenow"), this.uiSpinner.replaceWith(this.element);
    }, stepUp: t(function (e) {
      this._stepUp(e);
    }), _stepUp: function _stepUp(e) {
      this._start() && (this._spin((e || 1) * this.options.step), this._stop());
    }, stepDown: t(function (e) {
      this._stepDown(e);
    }), _stepDown: function _stepDown(e) {
      this._start() && (this._spin((e || 1) * -this.options.step), this._stop());
    }, pageUp: t(function (e) {
      this._stepUp((e || 1) * this.options.page);
    }), pageDown: t(function (e) {
      this._stepDown((e || 1) * this.options.page);
    }), value: function value(e) {
      if (!arguments.length) return this._parse(this.element.val());t(this._value).call(this, e);
    }, widget: function widget() {
      return this.uiSpinner;
    } });
})(jQuery);(function (e, t) {
  function i() {
    return ++n;
  }function s(e) {
    return e.hash.length > 1 && decodeURIComponent(e.href.replace(r, "")) === decodeURIComponent(location.href.replace(r, ""));
  }var n = 0,
      r = /#.*$/;e.widget("ui.tabs", { version: "1.10.0", delay: 300, options: { active: null, collapsible: !1, event: "click", heightStyle: "content", hide: null, show: null, activate: null, beforeActivate: null, beforeLoad: null, load: null }, _create: function _create() {
      var t = this,
          n = this.options;this.running = !1, this.element.addClass("ui-tabs ui-widget ui-widget-content ui-corner-all").toggleClass("ui-tabs-collapsible", n.collapsible).delegate(".ui-tabs-nav > li", "mousedown" + this.eventNamespace, function (t) {
        e(this).is(".ui-state-disabled") && t.preventDefault();
      }).delegate(".ui-tabs-anchor", "focus" + this.eventNamespace, function () {
        e(this).closest("li").is(".ui-state-disabled") && this.blur();
      }), this._processTabs(), n.active = this._initialActive(), e.isArray(n.disabled) && (n.disabled = e.unique(n.disabled.concat(e.map(this.tabs.filter(".ui-state-disabled"), function (e) {
        return t.tabs.index(e);
      }))).sort()), this.options.active !== !1 && this.anchors.length ? this.active = this._findActive(n.active) : this.active = e(), this._refresh(), this.active.length && this.load(n.active);
    }, _initialActive: function _initialActive() {
      var t = this.options.active,
          n = this.options.collapsible,
          r = location.hash.substring(1);if (t === null) {
        r && this.tabs.each(function (n, i) {
          if (e(i).attr("aria-controls") === r) return t = n, !1;
        }), t === null && (t = this.tabs.index(this.tabs.filter(".ui-tabs-active")));if (t === null || t === -1) t = this.tabs.length ? 0 : !1;
      }return t !== !1 && (t = this.tabs.index(this.tabs.eq(t)), t === -1 && (t = n ? !1 : 0)), !n && t === !1 && this.anchors.length && (t = 0), t;
    }, _getCreateEventData: function _getCreateEventData() {
      return { tab: this.active, panel: this.active.length ? this._getPanelForTab(this.active) : e() };
    }, _tabKeydown: function _tabKeydown(t) {
      var n = e(this.document[0].activeElement).closest("li"),
          r = this.tabs.index(n),
          i = !0;if (this._handlePageNav(t)) return;switch (t.keyCode) {case e.ui.keyCode.RIGHT:case e.ui.keyCode.DOWN:
          r++;break;case e.ui.keyCode.UP:case e.ui.keyCode.LEFT:
          i = !1, r--;break;case e.ui.keyCode.END:
          r = this.anchors.length - 1;break;case e.ui.keyCode.HOME:
          r = 0;break;case e.ui.keyCode.SPACE:
          t.preventDefault(), clearTimeout(this.activating), this._activate(r);return;case e.ui.keyCode.ENTER:
          t.preventDefault(), clearTimeout(this.activating), this._activate(r === this.options.active ? !1 : r);return;default:
          return;}t.preventDefault(), clearTimeout(this.activating), r = this._focusNextTab(r, i), t.ctrlKey || (n.attr("aria-selected", "false"), this.tabs.eq(r).attr("aria-selected", "true"), this.activating = this._delay(function () {
        this.option("active", r);
      }, this.delay));
    }, _panelKeydown: function _panelKeydown(t) {
      if (this._handlePageNav(t)) return;t.ctrlKey && t.keyCode === e.ui.keyCode.UP && (t.preventDefault(), this.active.focus());
    }, _handlePageNav: function _handlePageNav(t) {
      if (t.altKey && t.keyCode === e.ui.keyCode.PAGE_UP) return this._activate(this._focusNextTab(this.options.active - 1, !1)), !0;if (t.altKey && t.keyCode === e.ui.keyCode.PAGE_DOWN) return this._activate(this._focusNextTab(this.options.active + 1, !0)), !0;
    }, _findNextTab: function _findNextTab(t, n) {
      function i() {
        return t > r && (t = 0), t < 0 && (t = r), t;
      }var r = this.tabs.length - 1;while (e.inArray(i(), this.options.disabled) !== -1) {
        t = n ? t + 1 : t - 1;
      }return t;
    }, _focusNextTab: function _focusNextTab(e, t) {
      return e = this._findNextTab(e, t), this.tabs.eq(e).focus(), e;
    }, _setOption: function _setOption(e, t) {
      if (e === "active") {
        this._activate(t);return;
      }if (e === "disabled") {
        this._setupDisabled(t);return;
      }this._super(e, t), e === "collapsible" && (this.element.toggleClass("ui-tabs-collapsible", t), !t && this.options.active === !1 && this._activate(0)), e === "event" && this._setupEvents(t), e === "heightStyle" && this._setupHeightStyle(t);
    }, _tabId: function _tabId(e) {
      return e.attr("aria-controls") || "ui-tabs-" + i();
    }, _sanitizeSelector: function _sanitizeSelector(e) {
      return e ? e.replace(/[!"$%&'()*+,.\/:;<=>?@\[\]\^`{|}~]/g, "\\$&") : "";
    }, refresh: function refresh() {
      var t = this.options,
          n = this.tablist.children(":has(a[href])");t.disabled = e.map(n.filter(".ui-state-disabled"), function (e) {
        return n.index(e);
      }), this._processTabs(), t.active === !1 || !this.anchors.length ? (t.active = !1, this.active = e()) : this.active.length && !e.contains(this.tablist[0], this.active[0]) ? this.tabs.length === t.disabled.length ? (t.active = !1, this.active = e()) : this._activate(this._findNextTab(Math.max(0, t.active - 1), !1)) : t.active = this.tabs.index(this.active), this._refresh();
    }, _refresh: function _refresh() {
      this._setupDisabled(this.options.disabled), this._setupEvents(this.options.event), this._setupHeightStyle(this.options.heightStyle), this.tabs.not(this.active).attr({ "aria-selected": "false", tabIndex: -1 }), this.panels.not(this._getPanelForTab(this.active)).hide().attr({ "aria-expanded": "false", "aria-hidden": "true" }), this.active.length ? (this.active.addClass("ui-tabs-active ui-state-active").attr({ "aria-selected": "true", tabIndex: 0 }), this._getPanelForTab(this.active).show().attr({ "aria-expanded": "true", "aria-hidden": "false" })) : this.tabs.eq(0).attr("tabIndex", 0);
    }, _processTabs: function _processTabs() {
      var t = this;this.tablist = this._getList().addClass("ui-tabs-nav ui-helper-reset ui-helper-clearfix ui-widget-header ui-corner-all").attr("role", "tablist"), this.tabs = this.tablist.find("> li:has(a[href])").addClass("ui-state-default ui-corner-top").attr({ role: "tab", tabIndex: -1 }), this.anchors = this.tabs.map(function () {
        return e("a", this)[0];
      }).addClass("ui-tabs-anchor").attr({ role: "presentation", tabIndex: -1 }), this.panels = e(), this.anchors.each(function (n, r) {
        var i,
            o,
            u,
            a = e(r).uniqueId().attr("id"),
            f = e(r).closest("li"),
            l = f.attr("aria-controls");s(r) ? (i = r.hash, o = t.element.find(t._sanitizeSelector(i))) : (u = t._tabId(f), i = "#" + u, o = t.element.find(i), o.length || (o = t._createPanel(u), o.insertAfter(t.panels[n - 1] || t.tablist)), o.attr("aria-live", "polite")), o.length && (t.panels = t.panels.add(o)), l && f.data("ui-tabs-aria-controls", l), f.attr({ "aria-controls": i.substring(1), "aria-labelledby": a }), o.attr("aria-labelledby", a);
      }), this.panels.addClass("ui-tabs-panel ui-widget-content ui-corner-bottom").attr("role", "tabpanel");
    }, _getList: function _getList() {
      return this.element.find("ol,ul").eq(0);
    }, _createPanel: function _createPanel(t) {
      return e("<div>").attr("id", t).addClass("ui-tabs-panel ui-widget-content ui-corner-bottom").data("ui-tabs-destroy", !0);
    }, _setupDisabled: function _setupDisabled(t) {
      e.isArray(t) && (t.length ? t.length === this.anchors.length && (t = !0) : t = !1);for (var n = 0, r; r = this.tabs[n]; n++) {
        t === !0 || e.inArray(n, t) !== -1 ? e(r).addClass("ui-state-disabled").attr("aria-disabled", "true") : e(r).removeClass("ui-state-disabled").removeAttr("aria-disabled");
      }this.options.disabled = t;
    }, _setupEvents: function _setupEvents(t) {
      var n = { click: function click(e) {
          e.preventDefault();
        } };t && e.each(t.split(" "), function (e, t) {
        n[t] = "_eventHandler";
      }), this._off(this.anchors.add(this.tabs).add(this.panels)), this._on(this.anchors, n), this._on(this.tabs, { keydown: "_tabKeydown" }), this._on(this.panels, { keydown: "_panelKeydown" }), this._focusable(this.tabs), this._hoverable(this.tabs);
    }, _setupHeightStyle: function _setupHeightStyle(t) {
      var n,
          r = this.element.parent();t === "fill" ? (n = r.height(), n -= this.element.outerHeight() - this.element.height(), this.element.siblings(":visible").each(function () {
        var t = e(this),
            r = t.css("position");if (r === "absolute" || r === "fixed") return;n -= t.outerHeight(!0);
      }), this.element.children().not(this.panels).each(function () {
        n -= e(this).outerHeight(!0);
      }), this.panels.each(function () {
        e(this).height(Math.max(0, n - e(this).innerHeight() + e(this).height()));
      }).css("overflow", "auto")) : t === "auto" && (n = 0, this.panels.each(function () {
        n = Math.max(n, e(this).height("").height());
      }).height(n));
    }, _eventHandler: function _eventHandler(t) {
      var n = this.options,
          r = this.active,
          i = e(t.currentTarget),
          s = i.closest("li"),
          o = s[0] === r[0],
          u = o && n.collapsible,
          a = u ? e() : this._getPanelForTab(s),
          f = r.length ? this._getPanelForTab(r) : e(),
          l = { oldTab: r, oldPanel: f, newTab: u ? e() : s, newPanel: a };t.preventDefault();if (s.hasClass("ui-state-disabled") || s.hasClass("ui-tabs-loading") || this.running || o && !n.collapsible || this._trigger("beforeActivate", t, l) === !1) return;n.active = u ? !1 : this.tabs.index(s), this.active = o ? e() : s, this.xhr && this.xhr.abort(), !f.length && !a.length && e.error("jQuery UI Tabs: Mismatching fragment identifier."), a.length && this.load(this.tabs.index(s), t), this._toggle(t, l);
    }, _toggle: function _toggle(t, n) {
      function o() {
        r.running = !1, r._trigger("activate", t, n);
      }function u() {
        n.newTab.closest("li").addClass("ui-tabs-active ui-state-active"), i.length && r.options.show ? r._show(i, r.options.show, o) : (i.show(), o());
      }var r = this,
          i = n.newPanel,
          s = n.oldPanel;this.running = !0, s.length && this.options.hide ? this._hide(s, this.options.hide, function () {
        n.oldTab.closest("li").removeClass("ui-tabs-active ui-state-active"), u();
      }) : (n.oldTab.closest("li").removeClass("ui-tabs-active ui-state-active"), s.hide(), u()), s.attr({ "aria-expanded": "false", "aria-hidden": "true" }), n.oldTab.attr("aria-selected", "false"), i.length && s.length ? n.oldTab.attr("tabIndex", -1) : i.length && this.tabs.filter(function () {
        return e(this).attr("tabIndex") === 0;
      }).attr("tabIndex", -1), i.attr({ "aria-expanded": "true", "aria-hidden": "false" }), n.newTab.attr({ "aria-selected": "true", tabIndex: 0 });
    }, _activate: function _activate(t) {
      var n,
          r = this._findActive(t);if (r[0] === this.active[0]) return;r.length || (r = this.active), n = r.find(".ui-tabs-anchor")[0], this._eventHandler({ target: n, currentTarget: n, preventDefault: e.noop });
    }, _findActive: function _findActive(t) {
      return t === !1 ? e() : this.tabs.eq(t);
    }, _getIndex: function _getIndex(e) {
      return typeof e == "string" && (e = this.anchors.index(this.anchors.filter("[href$='" + e + "']"))), e;
    }, _destroy: function _destroy() {
      this.xhr && this.xhr.abort(), this.element.removeClass("ui-tabs ui-widget ui-widget-content ui-corner-all ui-tabs-collapsible"), this.tablist.removeClass("ui-tabs-nav ui-helper-reset ui-helper-clearfix ui-widget-header ui-corner-all").removeAttr("role"), this.anchors.removeClass("ui-tabs-anchor").removeAttr("role").removeAttr("tabIndex").removeUniqueId(), this.tabs.add(this.panels).each(function () {
        e.data(this, "ui-tabs-destroy") ? e(this).remove() : e(this).removeClass("ui-state-default ui-state-active ui-state-disabled ui-corner-top ui-corner-bottom ui-widget-content ui-tabs-active ui-tabs-panel").removeAttr("tabIndex").removeAttr("aria-live").removeAttr("aria-busy").removeAttr("aria-selected").removeAttr("aria-labelledby").removeAttr("aria-hidden").removeAttr("aria-expanded").removeAttr("role");
      }), this.tabs.each(function () {
        var t = e(this),
            n = t.data("ui-tabs-aria-controls");n ? t.attr("aria-controls", n).removeData("ui-tabs-aria-controls") : t.removeAttr("aria-controls");
      }), this.panels.show(), this.options.heightStyle !== "content" && this.panels.css("height", "");
    }, enable: function enable(n) {
      var r = this.options.disabled;if (r === !1) return;n === t ? r = !1 : (n = this._getIndex(n), e.isArray(r) ? r = e.map(r, function (e) {
        return e !== n ? e : null;
      }) : r = e.map(this.tabs, function (e, t) {
        return t !== n ? t : null;
      })), this._setupDisabled(r);
    }, disable: function disable(n) {
      var r = this.options.disabled;if (r === !0) return;if (n === t) r = !0;else {
        n = this._getIndex(n);if (e.inArray(n, r) !== -1) return;e.isArray(r) ? r = e.merge([n], r).sort() : r = [n];
      }this._setupDisabled(r);
    }, load: function load(t, n) {
      t = this._getIndex(t);var r = this,
          i = this.tabs.eq(t),
          o = i.find(".ui-tabs-anchor"),
          u = this._getPanelForTab(i),
          a = { tab: i, panel: u };if (s(o[0])) return;this.xhr = e.ajax(this._ajaxSettings(o, n, a)), this.xhr && this.xhr.statusText !== "canceled" && (i.addClass("ui-tabs-loading"), u.attr("aria-busy", "true"), this.xhr.success(function (e) {
        setTimeout(function () {
          u.html(e), r._trigger("load", n, a);
        }, 1);
      }).complete(function (e, t) {
        setTimeout(function () {
          t === "abort" && r.panels.stop(!1, !0), i.removeClass("ui-tabs-loading"), u.removeAttr("aria-busy"), e === r.xhr && delete r.xhr;
        }, 1);
      }));
    }, _ajaxSettings: function _ajaxSettings(t, n, r) {
      var i = this;return { url: t.attr("href"), beforeSend: function beforeSend(t, s) {
          return i._trigger("beforeLoad", n, e.extend({ jqXHR: t, ajaxSettings: s }, r));
        } };
    }, _getPanelForTab: function _getPanelForTab(t) {
      var n = e(t).attr("aria-controls");return this.element.find(this._sanitizeSelector("#" + n));
    } });
})(jQuery);(function (e) {
  function n(t, n) {
    var r = (t.attr("aria-describedby") || "").split(/\s+/);r.push(n), t.data("ui-tooltip-id", n).attr("aria-describedby", e.trim(r.join(" ")));
  }function r(t) {
    var n = t.data("ui-tooltip-id"),
        r = (t.attr("aria-describedby") || "").split(/\s+/),
        i = e.inArray(n, r);i !== -1 && r.splice(i, 1), t.removeData("ui-tooltip-id"), r = e.trim(r.join(" ")), r ? t.attr("aria-describedby", r) : t.removeAttr("aria-describedby");
  }var t = 0;e.widget("ui.tooltip", { version: "1.10.0", options: { content: function content() {
        var t = e(this).attr("title") || "";return e("<a>").text(t).html();
      }, hide: !0, items: "[title]:not([disabled])", position: { my: "left top+15", at: "left bottom", collision: "flipfit flip" }, show: !0, tooltipClass: null, track: !1, close: null, open: null }, _create: function _create() {
      this._on({ mouseover: "open", focusin: "open" }), this.tooltips = {}, this.parents = {}, this.options.disabled && this._disable();
    }, _setOption: function _setOption(t, n) {
      var r = this;if (t === "disabled") {
        this[n ? "_disable" : "_enable"](), this.options[t] = n;return;
      }this._super(t, n), t === "content" && e.each(this.tooltips, function (e, t) {
        r._updateContent(t);
      });
    }, _disable: function _disable() {
      var t = this;e.each(this.tooltips, function (n, r) {
        var i = e.Event("blur");i.target = i.currentTarget = r[0], t.close(i, !0);
      }), this.element.find(this.options.items).addBack().each(function () {
        var t = e(this);t.is("[title]") && t.data("ui-tooltip-title", t.attr("title")).attr("title", "");
      });
    }, _enable: function _enable() {
      this.element.find(this.options.items).addBack().each(function () {
        var t = e(this);t.data("ui-tooltip-title") && t.attr("title", t.data("ui-tooltip-title"));
      });
    }, open: function open(t) {
      var n = this,
          r = e(t ? t.target : this.element).closest(this.options.items);if (!r.length || r.data("ui-tooltip-id")) return;r.attr("title") && r.data("ui-tooltip-title", r.attr("title")), r.data("ui-tooltip-open", !0), t && t.type === "mouseover" && r.parents().each(function () {
        var t = e(this),
            r;t.data("ui-tooltip-open") && (r = e.Event("blur"), r.target = r.currentTarget = this, n.close(r, !0)), t.attr("title") && (t.uniqueId(), n.parents[this.id] = { element: this, title: t.attr("title") }, t.attr("title", ""));
      }), this._updateContent(r, t);
    }, _updateContent: function _updateContent(e, t) {
      var n,
          r = this.options.content,
          i = this,
          s = t ? t.type : null;if (typeof r == "string") return this._open(t, e, r);n = r.call(e[0], function (n) {
        if (!e.data("ui-tooltip-open")) return;i._delay(function () {
          t && (t.type = s), this._open(t, e, n);
        });
      }), n && this._open(t, e, n);
    }, _open: function _open(t, r, i) {
      function f(e) {
        a.of = e;if (s.is(":hidden")) return;s.position(a);
      }var s,
          o,
          u,
          a = e.extend({}, this.options.position);if (!i) return;s = this._find(r);if (s.length) {
        s.find(".ui-tooltip-content").html(i);return;
      }r.is("[title]") && (t && t.type === "mouseover" ? r.attr("title", "") : r.removeAttr("title")), s = this._tooltip(r), n(r, s.attr("id")), s.find(".ui-tooltip-content").html(i), this.options.track && t && /^mouse/.test(t.type) ? (this._on(this.document, { mousemove: f }), f(t)) : s.position(e.extend({ of: r }, this.options.position)), s.hide(), this._show(s, this.options.show), this.options.show && this.options.show.delay && (u = this.delayedShow = setInterval(function () {
        s.is(":visible") && (f(a.of), clearInterval(u));
      }, e.fx.interval)), this._trigger("open", t, { tooltip: s }), o = { keyup: function keyup(t) {
          if (t.keyCode === e.ui.keyCode.ESCAPE) {
            var n = e.Event(t);n.currentTarget = r[0], this.close(n, !0);
          }
        }, remove: function remove() {
          this._removeTooltip(s);
        } };if (!t || t.type === "mouseover") o.mouseleave = "close";if (!t || t.type === "focusin") o.focusout = "close";this._on(!0, r, o);
    }, close: function close(t) {
      var n = this,
          i = e(t ? t.currentTarget : this.element),
          s = this._find(i);if (this.closing) return;clearInterval(this.delayedShow), i.data("ui-tooltip-title") && i.attr("title", i.data("ui-tooltip-title")), r(i), s.stop(!0), this._hide(s, this.options.hide, function () {
        n._removeTooltip(e(this));
      }), i.removeData("ui-tooltip-open"), this._off(i, "mouseleave focusout keyup"), i[0] !== this.element[0] && this._off(i, "remove"), this._off(this.document, "mousemove"), t && t.type === "mouseleave" && e.each(this.parents, function (t, r) {
        e(r.element).attr("title", r.title), delete n.parents[t];
      }), this.closing = !0, this._trigger("close", t, { tooltip: s }), this.closing = !1;
    }, _tooltip: function _tooltip(n) {
      var r = "ui-tooltip-" + t++,
          i = e("<div>").attr({ id: r, role: "tooltip" }).addClass("ui-tooltip ui-widget ui-corner-all ui-widget-content " + (this.options.tooltipClass || ""));return e("<div>").addClass("ui-tooltip-content").appendTo(i), i.appendTo(this.document[0].body), this.tooltips[r] = n, i;
    }, _find: function _find(t) {
      var n = t.data("ui-tooltip-id");return n ? e("#" + n) : e();
    }, _removeTooltip: function _removeTooltip(e) {
      e.remove(), delete this.tooltips[e.attr("id")];
    }, _destroy: function _destroy() {
      var t = this;e.each(this.tooltips, function (n, r) {
        var i = e.Event("blur");i.target = i.currentTarget = r[0], t.close(i, !0), e("#" + n).remove(), r.data("ui-tooltip-title") && (r.attr("title", r.data("ui-tooltip-title")), r.removeData("ui-tooltip-title"));
      });
    } });
})(jQuery);jQuery.effects || function (e, t) {
  var n = "ui-effects-";e.effects = { effect: {} }, function (e, t) {
    function h(e, t, n) {
      var r = u[t.type] || {};return e == null ? n || !t.def ? null : t.def : (e = r.floor ? ~~e : parseFloat(e), isNaN(e) ? t.def : r.mod ? (e + r.mod) % r.mod : 0 > e ? 0 : r.max < e ? r.max : e);
    }function p(t) {
      var n = s(),
          r = n._rgba = [];return t = t.toLowerCase(), c(i, function (e, i) {
        var s,
            u = i.re.exec(t),
            a = u && i.parse(u),
            f = i.space || "rgba";if (a) return s = n[f](a), n[o[f].cache] = s[o[f].cache], r = n._rgba = s._rgba, !1;
      }), r.length ? (r.join() === "0,0,0,0" && e.extend(r, l.transparent), n) : l[t];
    }function d(e, t, n) {
      return n = (n + 1) % 1, n * 6 < 1 ? e + (t - e) * n * 6 : n * 2 < 1 ? t : n * 3 < 2 ? e + (t - e) * (2 / 3 - n) * 6 : e;
    }var n = "backgroundColor borderBottomColor borderLeftColor borderRightColor borderTopColor color columnRuleColor outlineColor textDecorationColor textEmphasisColor",
        r = /^([\-+])=\s*(\d+\.?\d*)/,
        i = [{ re: /rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(?:,\s*(\d?(?:\.\d+)?)\s*)?\)/, parse: function parse(e) {
        return [e[1], e[2], e[3], e[4]];
      } }, { re: /rgba?\(\s*(\d+(?:\.\d+)?)\%\s*,\s*(\d+(?:\.\d+)?)\%\s*,\s*(\d+(?:\.\d+)?)\%\s*(?:,\s*(\d?(?:\.\d+)?)\s*)?\)/, parse: function parse(e) {
        return [e[1] * 2.55, e[2] * 2.55, e[3] * 2.55, e[4]];
      } }, { re: /#([a-f0-9]{2})([a-f0-9]{2})([a-f0-9]{2})/, parse: function parse(e) {
        return [parseInt(e[1], 16), parseInt(e[2], 16), parseInt(e[3], 16)];
      } }, { re: /#([a-f0-9])([a-f0-9])([a-f0-9])/, parse: function parse(e) {
        return [parseInt(e[1] + e[1], 16), parseInt(e[2] + e[2], 16), parseInt(e[3] + e[3], 16)];
      } }, { re: /hsla?\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\%\s*,\s*(\d+(?:\.\d+)?)\%\s*(?:,\s*(\d?(?:\.\d+)?)\s*)?\)/, space: "hsla", parse: function parse(e) {
        return [e[1], e[2] / 100, e[3] / 100, e[4]];
      } }],
        s = e.Color = function (t, n, r, i) {
      return new e.Color.fn.parse(t, n, r, i);
    },
        o = { rgba: { props: { red: { idx: 0, type: "byte" }, green: { idx: 1, type: "byte" }, blue: { idx: 2, type: "byte" } } }, hsla: { props: { hue: { idx: 0, type: "degrees" }, saturation: { idx: 1, type: "percent" }, lightness: { idx: 2, type: "percent" } } } },
        u = { "byte": { floor: !0, max: 255 }, percent: { max: 1 }, degrees: { mod: 360, floor: !0 } },
        a = s.support = {},
        f = e("<p>")[0],
        l,
        c = e.each;f.style.cssText = "background-color:rgba(1,1,1,.5)", a.rgba = f.style.backgroundColor.indexOf("rgba") > -1, c(o, function (e, t) {
      t.cache = "_" + e, t.props.alpha = { idx: 3, type: "percent", def: 1 };
    }), s.fn = e.extend(s.prototype, { parse: function parse(n, r, i, u) {
        if (n === t) return this._rgba = [null, null, null, null], this;if (n.jquery || n.nodeType) n = e(n).css(r), r = t;var a = this,
            f = e.type(n),
            d = this._rgba = [];r !== t && (n = [n, r, i, u], f = "array");if (f === "string") return this.parse(p(n) || l._default);if (f === "array") return c(o.rgba.props, function (e, t) {
          d[t.idx] = h(n[t.idx], t);
        }), this;if (f === "object") return n instanceof s ? c(o, function (e, t) {
          n[t.cache] && (a[t.cache] = n[t.cache].slice());
        }) : c(o, function (t, r) {
          var i = r.cache;c(r.props, function (e, t) {
            if (!a[i] && r.to) {
              if (e === "alpha" || n[e] == null) return;a[i] = r.to(a._rgba);
            }a[i][t.idx] = h(n[e], t, !0);
          }), a[i] && e.inArray(null, a[i].slice(0, 3)) < 0 && (a[i][3] = 1, r.from && (a._rgba = r.from(a[i])));
        }), this;
      }, is: function is(e) {
        var t = s(e),
            n = !0,
            r = this;return c(o, function (e, i) {
          var s,
              o = t[i.cache];return o && (s = r[i.cache] || i.to && i.to(r._rgba) || [], c(i.props, function (e, t) {
            if (o[t.idx] != null) return n = o[t.idx] === s[t.idx], n;
          })), n;
        }), n;
      }, _space: function _space() {
        var e = [],
            t = this;return c(o, function (n, r) {
          t[r.cache] && e.push(n);
        }), e.pop();
      }, transition: function transition(e, t) {
        var n = s(e),
            r = n._space(),
            i = o[r],
            a = this.alpha() === 0 ? s("transparent") : this,
            f = a[i.cache] || i.to(a._rgba),
            l = f.slice();return n = n[i.cache], c(i.props, function (e, r) {
          var i = r.idx,
              s = f[i],
              o = n[i],
              a = u[r.type] || {};if (o === null) return;s === null ? l[i] = o : (a.mod && (o - s > a.mod / 2 ? s += a.mod : s - o > a.mod / 2 && (s -= a.mod)), l[i] = h((o - s) * t + s, r));
        }), this[r](l);
      }, blend: function blend(t) {
        if (this._rgba[3] === 1) return this;var n = this._rgba.slice(),
            r = n.pop(),
            i = s(t)._rgba;return s(e.map(n, function (e, t) {
          return (1 - r) * i[t] + r * e;
        }));
      }, toRgbaString: function toRgbaString() {
        var t = "rgba(",
            n = e.map(this._rgba, function (e, t) {
          return e == null ? t > 2 ? 1 : 0 : e;
        });return n[3] === 1 && (n.pop(), t = "rgb("), t + n.join() + ")";
      }, toHslaString: function toHslaString() {
        var t = "hsla(",
            n = e.map(this.hsla(), function (e, t) {
          return e == null && (e = t > 2 ? 1 : 0), t && t < 3 && (e = Math.round(e * 100) + "%"), e;
        });return n[3] === 1 && (n.pop(), t = "hsl("), t + n.join() + ")";
      }, toHexString: function toHexString(t) {
        var n = this._rgba.slice(),
            r = n.pop();return t && n.push(~~(r * 255)), "#" + e.map(n, function (e) {
          return e = (e || 0).toString(16), e.length === 1 ? "0" + e : e;
        }).join("");
      }, toString: function toString() {
        return this._rgba[3] === 0 ? "transparent" : this.toRgbaString();
      } }), s.fn.parse.prototype = s.fn, o.hsla.to = function (e) {
      if (e[0] == null || e[1] == null || e[2] == null) return [null, null, null, e[3]];var t = e[0] / 255,
          n = e[1] / 255,
          r = e[2] / 255,
          i = e[3],
          s = Math.max(t, n, r),
          o = Math.min(t, n, r),
          u = s - o,
          a = s + o,
          f = a * .5,
          l,
          c;return o === s ? l = 0 : t === s ? l = 60 * (n - r) / u + 360 : n === s ? l = 60 * (r - t) / u + 120 : l = 60 * (t - n) / u + 240, u === 0 ? c = 0 : f <= .5 ? c = u / a : c = u / (2 - a), [Math.round(l) % 360, c, f, i == null ? 1 : i];
    }, o.hsla.from = function (e) {
      if (e[0] == null || e[1] == null || e[2] == null) return [null, null, null, e[3]];var t = e[0] / 360,
          n = e[1],
          r = e[2],
          i = e[3],
          s = r <= .5 ? r * (1 + n) : r + n - r * n,
          o = 2 * r - s;return [Math.round(d(o, s, t + 1 / 3) * 255), Math.round(d(o, s, t) * 255), Math.round(d(o, s, t - 1 / 3) * 255), i];
    }, c(o, function (n, i) {
      var o = i.props,
          u = i.cache,
          a = i.to,
          f = i.from;s.fn[n] = function (n) {
        a && !this[u] && (this[u] = a(this._rgba));if (n === t) return this[u].slice();var r,
            i = e.type(n),
            l = i === "array" || i === "object" ? n : arguments,
            p = this[u].slice();return c(o, function (e, t) {
          var n = l[i === "object" ? e : t.idx];n == null && (n = p[t.idx]), p[t.idx] = h(n, t);
        }), f ? (r = s(f(p)), r[u] = p, r) : s(p);
      }, c(o, function (t, i) {
        if (s.fn[t]) return;s.fn[t] = function (s) {
          var o = e.type(s),
              u = t === "alpha" ? this._hsla ? "hsla" : "rgba" : n,
              a = this[u](),
              f = a[i.idx],
              l;return o === "undefined" ? f : (o === "function" && (s = s.call(this, f), o = e.type(s)), s == null && i.empty ? this : (o === "string" && (l = r.exec(s), l && (s = f + parseFloat(l[2]) * (l[1] === "+" ? 1 : -1))), a[i.idx] = s, this[u](a)));
        };
      });
    }), s.hook = function (t) {
      var n = t.split(" ");c(n, function (t, n) {
        e.cssHooks[n] = { set: function set(t, r) {
            var i,
                o,
                u = "";if (r !== "transparent" && (e.type(r) !== "string" || (i = p(r)))) {
              r = s(i || r);if (!a.rgba && r._rgba[3] !== 1) {
                o = n === "backgroundColor" ? t.parentNode : t;while ((u === "" || u === "transparent") && o && o.style) {
                  try {
                    u = e.css(o, "backgroundColor"), o = o.parentNode;
                  } catch (f) {}
                }r = r.blend(u && u !== "transparent" ? u : "_default");
              }r = r.toRgbaString();
            }try {
              t.style[n] = r;
            } catch (f) {}
          } }, e.fx.step[n] = function (t) {
          t.colorInit || (t.start = s(t.elem, n), t.end = s(t.end), t.colorInit = !0), e.cssHooks[n].set(t.elem, t.start.transition(t.end, t.pos));
        };
      });
    }, s.hook(n), e.cssHooks.borderColor = { expand: function expand(e) {
        var t = {};return c(["Top", "Right", "Bottom", "Left"], function (n, r) {
          t["border" + r + "Color"] = e;
        }), t;
      } }, l = e.Color.names = { aqua: "#00ffff", black: "#000000", blue: "#0000ff", fuchsia: "#ff00ff", gray: "#808080", green: "#008000", lime: "#00ff00", maroon: "#800000", navy: "#000080", olive: "#808000", purple: "#800080", red: "#ff0000", silver: "#c0c0c0", teal: "#008080", white: "#ffffff", yellow: "#ffff00", transparent: [null, null, null, 0], _default: "#ffffff" };
  }(jQuery), function () {
    function i(t) {
      var n,
          r,
          i = t.ownerDocument.defaultView ? t.ownerDocument.defaultView.getComputedStyle(t, null) : t.currentStyle,
          s = {};if (i && i.length && i[0] && i[i[0]]) {
        r = i.length;while (r--) {
          n = i[r], typeof i[n] == "string" && (s[e.camelCase(n)] = i[n]);
        }
      } else for (n in i) {
        typeof i[n] == "string" && (s[n] = i[n]);
      }return s;
    }function s(t, n) {
      var i = {},
          s,
          o;for (s in n) {
        o = n[s], t[s] !== o && !r[s] && (e.fx.step[s] || !isNaN(parseFloat(o))) && (i[s] = o);
      }return i;
    }var n = ["add", "remove", "toggle"],
        r = { border: 1, borderBottom: 1, borderColor: 1, borderLeft: 1, borderRight: 1, borderTop: 1, borderWidth: 1, margin: 1, padding: 1 };e.each(["borderLeftStyle", "borderRightStyle", "borderBottomStyle", "borderTopStyle"], function (t, n) {
      e.fx.step[n] = function (e) {
        if (e.end !== "none" && !e.setAttr || e.pos === 1 && !e.setAttr) jQuery.style(e.elem, n, e.end), e.setAttr = !0;
      };
    }), e.fn.addBack || (e.fn.addBack = function (e) {
      return this.add(e == null ? this.prevObject : this.prevObject.filter(e));
    }), e.effects.animateClass = function (t, r, o, u) {
      var a = e.speed(r, o, u);return this.queue(function () {
        var r = e(this),
            o = r.attr("class") || "",
            u,
            f = a.children ? r.find("*").addBack() : r;f = f.map(function () {
          var t = e(this);return { el: t, start: i(this) };
        }), u = function u() {
          e.each(n, function (e, n) {
            t[n] && r[n + "Class"](t[n]);
          });
        }, u(), f = f.map(function () {
          return this.end = i(this.el[0]), this.diff = s(this.start, this.end), this;
        }), r.attr("class", o), f = f.map(function () {
          var t = this,
              n = e.Deferred(),
              r = e.extend({}, a, { queue: !1, complete: function complete() {
              n.resolve(t);
            } });return this.el.animate(this.diff, r), n.promise();
        }), e.when.apply(e, f.get()).done(function () {
          u(), e.each(arguments, function () {
            var t = this.el;e.each(this.diff, function (e) {
              t.css(e, "");
            });
          }), a.complete.call(r[0]);
        });
      });
    }, e.fn.extend({ _addClass: e.fn.addClass, addClass: function addClass(t, n, r, i) {
        return n ? e.effects.animateClass.call(this, { add: t }, n, r, i) : this._addClass(t);
      }, _removeClass: e.fn.removeClass, removeClass: function removeClass(t, n, r, i) {
        return n ? e.effects.animateClass.call(this, { remove: t }, n, r, i) : this._removeClass(t);
      }, _toggleClass: e.fn.toggleClass, toggleClass: function toggleClass(n, r, i, s, o) {
        return typeof r == "boolean" || r === t ? i ? e.effects.animateClass.call(this, r ? { add: n } : { remove: n }, i, s, o) : this._toggleClass(n, r) : e.effects.animateClass.call(this, { toggle: n }, r, i, s);
      }, switchClass: function switchClass(t, n, r, i, s) {
        return e.effects.animateClass.call(this, { add: n, remove: t }, r, i, s);
      } });
  }(), function () {
    function r(t, n, r, i) {
      e.isPlainObject(t) && (n = t, t = t.effect), t = { effect: t }, n == null && (n = {}), e.isFunction(n) && (i = n, r = null, n = {});if (typeof n == "number" || e.fx.speeds[n]) i = r, r = n, n = {};return e.isFunction(r) && (i = r, r = null), n && e.extend(t, n), r = r || n.duration, t.duration = e.fx.off ? 0 : typeof r == "number" ? r : r in e.fx.speeds ? e.fx.speeds[r] : e.fx.speeds._default, t.complete = i || n.complete, t;
    }function i(t) {
      return !t || typeof t == "number" || e.fx.speeds[t] ? !0 : typeof t == "string" && !e.effects.effect[t];
    }e.extend(e.effects, { version: "1.10.0", save: function save(e, t) {
        for (var r = 0; r < t.length; r++) {
          t[r] !== null && e.data(n + t[r], e[0].style[t[r]]);
        }
      }, restore: function restore(e, r) {
        var i, s;for (s = 0; s < r.length; s++) {
          r[s] !== null && (i = e.data(n + r[s]), i === t && (i = ""), e.css(r[s], i));
        }
      }, setMode: function setMode(e, t) {
        return t === "toggle" && (t = e.is(":hidden") ? "show" : "hide"), t;
      }, getBaseline: function getBaseline(e, t) {
        var n, r;switch (e[0]) {case "top":
            n = 0;break;case "middle":
            n = .5;break;case "bottom":
            n = 1;break;default:
            n = e[0] / t.height;}switch (e[1]) {case "left":
            r = 0;break;case "center":
            r = .5;break;case "right":
            r = 1;break;default:
            r = e[1] / t.width;}return { x: r, y: n };
      }, createWrapper: function createWrapper(t) {
        if (t.parent().is(".ui-effects-wrapper")) return t.parent();var n = { width: t.outerWidth(!0), height: t.outerHeight(!0), "float": t.css("float") },
            r = e("<div></div>").addClass("ui-effects-wrapper").css({ fontSize: "100%", background: "transparent", border: "none", margin: 0, padding: 0 }),
            i = { width: t.width(), height: t.height() },
            s = document.activeElement;try {
          s.id;
        } catch (o) {
          s = document.body;
        }return t.wrap(r), (t[0] === s || e.contains(t[0], s)) && e(s).focus(), r = t.parent(), t.css("position") === "static" ? (r.css({ position: "relative" }), t.css({ position: "relative" })) : (e.extend(n, { position: t.css("position"), zIndex: t.css("z-index") }), e.each(["top", "left", "bottom", "right"], function (e, r) {
          n[r] = t.css(r), isNaN(parseInt(n[r], 10)) && (n[r] = "auto");
        }), t.css({ position: "relative", top: 0, left: 0, right: "auto", bottom: "auto" })), t.css(i), r.css(n).show();
      }, removeWrapper: function removeWrapper(t) {
        var n = document.activeElement;return t.parent().is(".ui-effects-wrapper") && (t.parent().replaceWith(t), (t[0] === n || e.contains(t[0], n)) && e(n).focus()), t;
      }, setTransition: function setTransition(t, n, r, i) {
        return i = i || {}, e.each(n, function (e, n) {
          var s = t.cssUnit(n);s[0] > 0 && (i[n] = s[0] * r + s[1]);
        }), i;
      } }), e.fn.extend({ effect: function effect() {
        function o(n) {
          function u() {
            e.isFunction(i) && i.call(r[0]), e.isFunction(n) && n();
          }var r = e(this),
              i = t.complete,
              o = t.mode;(r.is(":hidden") ? o === "hide" : o === "show") ? u() : s.call(r[0], t, u);
        }var t = r.apply(this, arguments),
            n = t.mode,
            i = t.queue,
            s = e.effects.effect[t.effect];return e.fx.off || !s ? n ? this[n](t.duration, t.complete) : this.each(function () {
          t.complete && t.complete.call(this);
        }) : i === !1 ? this.each(o) : this.queue(i || "fx", o);
      }, _show: e.fn.show, show: function show(e) {
        if (i(e)) return this._show.apply(this, arguments);var t = r.apply(this, arguments);return t.mode = "show", this.effect.call(this, t);
      }, _hide: e.fn.hide, hide: function hide(e) {
        if (i(e)) return this._hide.apply(this, arguments);var t = r.apply(this, arguments);return t.mode = "hide", this.effect.call(this, t);
      }, __toggle: e.fn.toggle, toggle: function toggle(t) {
        if (i(t) || typeof t == "boolean" || e.isFunction(t)) return this.__toggle.apply(this, arguments);var n = r.apply(this, arguments);return n.mode = "toggle", this.effect.call(this, n);
      }, cssUnit: function cssUnit(t) {
        var n = this.css(t),
            r = [];return e.each(["em", "px", "%", "pt"], function (e, t) {
          n.indexOf(t) > 0 && (r = [parseFloat(n), t]);
        }), r;
      } });
  }(), function () {
    var t = {};e.each(["Quad", "Cubic", "Quart", "Quint", "Expo"], function (e, n) {
      t[n] = function (t) {
        return Math.pow(t, e + 2);
      };
    }), e.extend(t, { Sine: function Sine(e) {
        return 1 - Math.cos(e * Math.PI / 2);
      }, Circ: function Circ(e) {
        return 1 - Math.sqrt(1 - e * e);
      }, Elastic: function Elastic(e) {
        return e === 0 || e === 1 ? e : -Math.pow(2, 8 * (e - 1)) * Math.sin(((e - 1) * 80 - 7.5) * Math.PI / 15);
      }, Back: function Back(e) {
        return e * e * (3 * e - 2);
      }, Bounce: function Bounce(e) {
        var t,
            n = 4;while (e < ((t = Math.pow(2, --n)) - 1) / 11) {}return 1 / Math.pow(4, 3 - n) - 7.5625 * Math.pow((t * 3 - 2) / 22 - e, 2);
      } }), e.each(t, function (t, n) {
      e.easing["easeIn" + t] = n, e.easing["easeOut" + t] = function (e) {
        return 1 - n(1 - e);
      }, e.easing["easeInOut" + t] = function (e) {
        return e < .5 ? n(e * 2) / 2 : 1 - n(e * -2 + 2) / 2;
      };
    });
  }();
}(jQuery);(function (e, t) {
  var n = /up|down|vertical/,
      r = /up|left|vertical|horizontal/;e.effects.effect.blind = function (t, i) {
    var s = e(this),
        o = ["position", "top", "bottom", "left", "right", "height", "width"],
        u = e.effects.setMode(s, t.mode || "hide"),
        a = t.direction || "up",
        f = n.test(a),
        l = f ? "height" : "width",
        c = f ? "top" : "left",
        h = r.test(a),
        p = {},
        d = u === "show",
        v,
        m,
        g;s.parent().is(".ui-effects-wrapper") ? e.effects.save(s.parent(), o) : e.effects.save(s, o), s.show(), v = e.effects.createWrapper(s).css({ overflow: "hidden" }), m = v[l](), g = parseFloat(v.css(c)) || 0, p[l] = d ? m : 0, h || (s.css(f ? "bottom" : "right", 0).css(f ? "top" : "left", "auto").css({ position: "absolute" }), p[c] = d ? g : m + g), d && (v.css(l, 0), h || v.css(c, g + m)), v.animate(p, { duration: t.duration, easing: t.easing, queue: !1, complete: function complete() {
        u === "hide" && s.hide(), e.effects.restore(s, o), e.effects.removeWrapper(s), i();
      } });
  };
})(jQuery);(function (e, t) {
  e.effects.effect.bounce = function (t, n) {
    var r = e(this),
        i = ["position", "top", "bottom", "left", "right", "height", "width"],
        s = e.effects.setMode(r, t.mode || "effect"),
        o = s === "hide",
        u = s === "show",
        a = t.direction || "up",
        f = t.distance,
        l = t.times || 5,
        c = l * 2 + (u || o ? 1 : 0),
        h = t.duration / c,
        p = t.easing,
        d = a === "up" || a === "down" ? "top" : "left",
        v = a === "up" || a === "left",
        m,
        g,
        y,
        b = r.queue(),
        w = b.length;(u || o) && i.push("opacity"), e.effects.save(r, i), r.show(), e.effects.createWrapper(r), f || (f = r[d === "top" ? "outerHeight" : "outerWidth"]() / 3), u && (y = { opacity: 1 }, y[d] = 0, r.css("opacity", 0).css(d, v ? -f * 2 : f * 2).animate(y, h, p)), o && (f /= Math.pow(2, l - 1)), y = {}, y[d] = 0;for (m = 0; m < l; m++) {
      g = {}, g[d] = (v ? "-=" : "+=") + f, r.animate(g, h, p).animate(y, h, p), f = o ? f * 2 : f / 2;
    }o && (g = { opacity: 0 }, g[d] = (v ? "-=" : "+=") + f, r.animate(g, h, p)), r.queue(function () {
      o && r.hide(), e.effects.restore(r, i), e.effects.removeWrapper(r), n();
    }), w > 1 && b.splice.apply(b, [1, 0].concat(b.splice(w, c + 1))), r.dequeue();
  };
})(jQuery);(function (e, t) {
  e.effects.effect.clip = function (t, n) {
    var r = e(this),
        i = ["position", "top", "bottom", "left", "right", "height", "width"],
        s = e.effects.setMode(r, t.mode || "hide"),
        o = s === "show",
        u = t.direction || "vertical",
        a = u === "vertical",
        f = a ? "height" : "width",
        l = a ? "top" : "left",
        c = {},
        h,
        p,
        d;e.effects.save(r, i), r.show(), h = e.effects.createWrapper(r).css({ overflow: "hidden" }), p = r[0].tagName === "IMG" ? h : r, d = p[f](), o && (p.css(f, 0), p.css(l, d / 2)), c[f] = o ? d : 0, c[l] = o ? 0 : d / 2, p.animate(c, { queue: !1, duration: t.duration, easing: t.easing, complete: function complete() {
        o || r.hide(), e.effects.restore(r, i), e.effects.removeWrapper(r), n();
      } });
  };
})(jQuery);(function (e, t) {
  e.effects.effect.drop = function (t, n) {
    var r = e(this),
        i = ["position", "top", "bottom", "left", "right", "opacity", "height", "width"],
        s = e.effects.setMode(r, t.mode || "hide"),
        o = s === "show",
        u = t.direction || "left",
        a = u === "up" || u === "down" ? "top" : "left",
        f = u === "up" || u === "left" ? "pos" : "neg",
        l = { opacity: o ? 1 : 0 },
        c;e.effects.save(r, i), r.show(), e.effects.createWrapper(r), c = t.distance || r[a === "top" ? "outerHeight" : "outerWidth"](!0) / 2, o && r.css("opacity", 0).css(a, f === "pos" ? -c : c), l[a] = (o ? f === "pos" ? "+=" : "-=" : f === "pos" ? "-=" : "+=") + c, r.animate(l, { queue: !1, duration: t.duration, easing: t.easing, complete: function complete() {
        s === "hide" && r.hide(), e.effects.restore(r, i), e.effects.removeWrapper(r), n();
      } });
  };
})(jQuery);(function (e, t) {
  e.effects.effect.explode = function (t, n) {
    function y() {
      c.push(this), c.length === r * i && b();
    }function b() {
      s.css({ visibility: "visible" }), e(c).remove(), u || s.hide(), n();
    }var r = t.pieces ? Math.round(Math.sqrt(t.pieces)) : 3,
        i = r,
        s = e(this),
        o = e.effects.setMode(s, t.mode || "hide"),
        u = o === "show",
        a = s.show().css("visibility", "hidden").offset(),
        f = Math.ceil(s.outerWidth() / i),
        l = Math.ceil(s.outerHeight() / r),
        c = [],
        h,
        p,
        d,
        v,
        m,
        g;for (h = 0; h < r; h++) {
      v = a.top + h * l, g = h - (r - 1) / 2;for (p = 0; p < i; p++) {
        d = a.left + p * f, m = p - (i - 1) / 2, s.clone().appendTo("body").wrap("<div></div>").css({ position: "absolute", visibility: "visible", left: -p * f, top: -h * l }).parent().addClass("ui-effects-explode").css({ position: "absolute", overflow: "hidden", width: f, height: l, left: d + (u ? m * f : 0), top: v + (u ? g * l : 0), opacity: u ? 0 : 1 }).animate({ left: d + (u ? 0 : m * f), top: v + (u ? 0 : g * l), opacity: u ? 1 : 0 }, t.duration || 500, t.easing, y);
      }
    }
  };
})(jQuery);(function (e, t) {
  e.effects.effect.fade = function (t, n) {
    var r = e(this),
        i = e.effects.setMode(r, t.mode || "toggle");r.animate({ opacity: i }, { queue: !1, duration: t.duration, easing: t.easing, complete: n });
  };
})(jQuery);(function (e, t) {
  e.effects.effect.fold = function (t, n) {
    var r = e(this),
        i = ["position", "top", "bottom", "left", "right", "height", "width"],
        s = e.effects.setMode(r, t.mode || "hide"),
        o = s === "show",
        u = s === "hide",
        a = t.size || 15,
        f = /([0-9]+)%/.exec(a),
        l = !!t.horizFirst,
        c = o !== l,
        h = c ? ["width", "height"] : ["height", "width"],
        p = t.duration / 2,
        d,
        v,
        m = {},
        g = {};e.effects.save(r, i), r.show(), d = e.effects.createWrapper(r).css({ overflow: "hidden" }), v = c ? [d.width(), d.height()] : [d.height(), d.width()], f && (a = parseInt(f[1], 10) / 100 * v[u ? 0 : 1]), o && d.css(l ? { height: 0, width: a } : { height: a, width: 0 }), m[h[0]] = o ? v[0] : a, g[h[1]] = o ? v[1] : 0, d.animate(m, p, t.easing).animate(g, p, t.easing, function () {
      u && r.hide(), e.effects.restore(r, i), e.effects.removeWrapper(r), n();
    });
  };
})(jQuery);(function (e, t) {
  e.effects.effect.highlight = function (t, n) {
    var r = e(this),
        i = ["backgroundImage", "backgroundColor", "opacity"],
        s = e.effects.setMode(r, t.mode || "show"),
        o = { backgroundColor: r.css("backgroundColor") };s === "hide" && (o.opacity = 0), e.effects.save(r, i), r.show().css({ backgroundImage: "none", backgroundColor: t.color || "#ffff99" }).animate(o, { queue: !1, duration: t.duration, easing: t.easing, complete: function complete() {
        s === "hide" && r.hide(), e.effects.restore(r, i), n();
      } });
  };
})(jQuery);(function (e, t) {
  e.effects.effect.pulsate = function (t, n) {
    var r = e(this),
        i = e.effects.setMode(r, t.mode || "show"),
        s = i === "show",
        o = i === "hide",
        u = s || i === "hide",
        a = (t.times || 5) * 2 + (u ? 1 : 0),
        f = t.duration / a,
        l = 0,
        c = r.queue(),
        h = c.length,
        p;if (s || !r.is(":visible")) r.css("opacity", 0).show(), l = 1;for (p = 1; p < a; p++) {
      r.animate({ opacity: l }, f, t.easing), l = 1 - l;
    }r.animate({ opacity: l }, f, t.easing), r.queue(function () {
      o && r.hide(), n();
    }), h > 1 && c.splice.apply(c, [1, 0].concat(c.splice(h, a + 1))), r.dequeue();
  };
})(jQuery);(function (e, t) {
  e.effects.effect.puff = function (t, n) {
    var r = e(this),
        i = e.effects.setMode(r, t.mode || "hide"),
        s = i === "hide",
        o = parseInt(t.percent, 10) || 150,
        u = o / 100,
        a = { height: r.height(), width: r.width(), outerHeight: r.outerHeight(), outerWidth: r.outerWidth() };e.extend(t, { effect: "scale", queue: !1, fade: !0, mode: i, complete: n, percent: s ? o : 100, from: s ? a : { height: a.height * u, width: a.width * u, outerHeight: a.outerHeight * u, outerWidth: a.outerWidth * u } }), r.effect(t);
  }, e.effects.effect.scale = function (t, n) {
    var r = e(this),
        i = e.extend(!0, {}, t),
        s = e.effects.setMode(r, t.mode || "effect"),
        o = parseInt(t.percent, 10) || (parseInt(t.percent, 10) === 0 ? 0 : s === "hide" ? 0 : 100),
        u = t.direction || "both",
        a = t.origin,
        f = { height: r.height(), width: r.width(), outerHeight: r.outerHeight(), outerWidth: r.outerWidth() },
        l = { y: u !== "horizontal" ? o / 100 : 1, x: u !== "vertical" ? o / 100 : 1 };i.effect = "size", i.queue = !1, i.complete = n, s !== "effect" && (i.origin = a || ["middle", "center"], i.restore = !0), i.from = t.from || (s === "show" ? { height: 0, width: 0, outerHeight: 0, outerWidth: 0 } : f), i.to = { height: f.height * l.y, width: f.width * l.x, outerHeight: f.outerHeight * l.y, outerWidth: f.outerWidth * l.x }, i.fade && (s === "show" && (i.from.opacity = 0, i.to.opacity = 1), s === "hide" && (i.from.opacity = 1, i.to.opacity = 0)), r.effect(i);
  }, e.effects.effect.size = function (t, n) {
    var r,
        i,
        s,
        o = e(this),
        u = ["position", "top", "bottom", "left", "right", "width", "height", "overflow", "opacity"],
        a = ["position", "top", "bottom", "left", "right", "overflow", "opacity"],
        f = ["width", "height", "overflow"],
        l = ["fontSize"],
        c = ["borderTopWidth", "borderBottomWidth", "paddingTop", "paddingBottom"],
        h = ["borderLeftWidth", "borderRightWidth", "paddingLeft", "paddingRight"],
        p = e.effects.setMode(o, t.mode || "effect"),
        d = t.restore || p !== "effect",
        v = t.scale || "both",
        m = t.origin || ["middle", "center"],
        g = o.css("position"),
        y = d ? u : a,
        b = { height: 0, width: 0, outerHeight: 0, outerWidth: 0 };p === "show" && o.show(), r = { height: o.height(), width: o.width(), outerHeight: o.outerHeight(), outerWidth: o.outerWidth() }, t.mode === "toggle" && p === "show" ? (o.from = t.to || b, o.to = t.from || r) : (o.from = t.from || (p === "show" ? b : r), o.to = t.to || (p === "hide" ? b : r)), s = { from: { y: o.from.height / r.height, x: o.from.width / r.width }, to: { y: o.to.height / r.height, x: o.to.width / r.width } };if (v === "box" || v === "both") s.from.y !== s.to.y && (y = y.concat(c), o.from = e.effects.setTransition(o, c, s.from.y, o.from), o.to = e.effects.setTransition(o, c, s.to.y, o.to)), s.from.x !== s.to.x && (y = y.concat(h), o.from = e.effects.setTransition(o, h, s.from.x, o.from), o.to = e.effects.setTransition(o, h, s.to.x, o.to));(v === "content" || v === "both") && s.from.y !== s.to.y && (y = y.concat(l).concat(f), o.from = e.effects.setTransition(o, l, s.from.y, o.from), o.to = e.effects.setTransition(o, l, s.to.y, o.to)), e.effects.save(o, y), o.show(), e.effects.createWrapper(o), o.css("overflow", "hidden").css(o.from), m && (i = e.effects.getBaseline(m, r), o.from.top = (r.outerHeight - o.outerHeight()) * i.y, o.from.left = (r.outerWidth - o.outerWidth()) * i.x, o.to.top = (r.outerHeight - o.to.outerHeight) * i.y, o.to.left = (r.outerWidth - o.to.outerWidth) * i.x), o.css(o.from);if (v === "content" || v === "both") c = c.concat(["marginTop", "marginBottom"]).concat(l), h = h.concat(["marginLeft", "marginRight"]), f = u.concat(c).concat(h), o.find("*[width]").each(function () {
      var n = e(this),
          r = { height: n.height(), width: n.width(), outerHeight: n.outerHeight(), outerWidth: n.outerWidth() };d && e.effects.save(n, f), n.from = { height: r.height * s.from.y, width: r.width * s.from.x, outerHeight: r.outerHeight * s.from.y, outerWidth: r.outerWidth * s.from.x }, n.to = { height: r.height * s.to.y, width: r.width * s.to.x, outerHeight: r.height * s.to.y, outerWidth: r.width * s.to.x }, s.from.y !== s.to.y && (n.from = e.effects.setTransition(n, c, s.from.y, n.from), n.to = e.effects.setTransition(n, c, s.to.y, n.to)), s.from.x !== s.to.x && (n.from = e.effects.setTransition(n, h, s.from.x, n.from), n.to = e.effects.setTransition(n, h, s.to.x, n.to)), n.css(n.from), n.animate(n.to, t.duration, t.easing, function () {
        d && e.effects.restore(n, f);
      });
    });o.animate(o.to, { queue: !1, duration: t.duration, easing: t.easing, complete: function complete() {
        o.to.opacity === 0 && o.css("opacity", o.from.opacity), p === "hide" && o.hide(), e.effects.restore(o, y), d || (g === "static" ? o.css({ position: "relative", top: o.to.top, left: o.to.left }) : e.each(["top", "left"], function (e, t) {
          o.css(t, function (t, n) {
            var r = parseInt(n, 10),
                i = e ? o.to.left : o.to.top;return n === "auto" ? i + "px" : r + i + "px";
          });
        })), e.effects.removeWrapper(o), n();
      } });
  };
})(jQuery);(function (e, t) {
  e.effects.effect.shake = function (t, n) {
    var r = e(this),
        i = ["position", "top", "bottom", "left", "right", "height", "width"],
        s = e.effects.setMode(r, t.mode || "effect"),
        o = t.direction || "left",
        u = t.distance || 20,
        a = t.times || 3,
        f = a * 2 + 1,
        l = Math.round(t.duration / f),
        c = o === "up" || o === "down" ? "top" : "left",
        h = o === "up" || o === "left",
        p = {},
        d = {},
        v = {},
        m,
        g = r.queue(),
        y = g.length;e.effects.save(r, i), r.show(), e.effects.createWrapper(r), p[c] = (h ? "-=" : "+=") + u, d[c] = (h ? "+=" : "-=") + u * 2, v[c] = (h ? "-=" : "+=") + u * 2, r.animate(p, l, t.easing);for (m = 1; m < a; m++) {
      r.animate(d, l, t.easing).animate(v, l, t.easing);
    }r.animate(d, l, t.easing).animate(p, l / 2, t.easing).queue(function () {
      s === "hide" && r.hide(), e.effects.restore(r, i), e.effects.removeWrapper(r), n();
    }), y > 1 && g.splice.apply(g, [1, 0].concat(g.splice(y, f + 1))), r.dequeue();
  };
})(jQuery);(function (e, t) {
  e.effects.effect.slide = function (t, n) {
    var r = e(this),
        i = ["position", "top", "bottom", "left", "right", "width", "height"],
        s = e.effects.setMode(r, t.mode || "show"),
        o = s === "show",
        u = t.direction || "left",
        a = u === "up" || u === "down" ? "top" : "left",
        f = u === "up" || u === "left",
        l,
        c = {};e.effects.save(r, i), r.show(), l = t.distance || r[a === "top" ? "outerHeight" : "outerWidth"](!0), e.effects.createWrapper(r).css({ overflow: "hidden" }), o && r.css(a, f ? isNaN(l) ? "-" + l : -l : l), c[a] = (o ? f ? "+=" : "-=" : f ? "-=" : "+=") + l, r.animate(c, { queue: !1, duration: t.duration, easing: t.easing, complete: function complete() {
        s === "hide" && r.hide(), e.effects.restore(r, i), e.effects.removeWrapper(r), n();
      } });
  };
})(jQuery);(function (e, t) {
  e.effects.effect.transfer = function (t, n) {
    var r = e(this),
        i = e(t.to),
        s = i.css("position") === "fixed",
        o = e("body"),
        u = s ? o.scrollTop() : 0,
        a = s ? o.scrollLeft() : 0,
        f = i.offset(),
        l = { top: f.top - u, left: f.left - a, height: i.innerHeight(), width: i.innerWidth() },
        c = r.offset(),
        h = e("<div class='ui-effects-transfer'></div>").appendTo(document.body).addClass(t.className).css({ top: c.top - u, left: c.left - a, height: r.innerHeight(), width: r.innerWidth(), position: s ? "fixed" : "absolute" }).animate(l, t.duration, t.easing, function () {
      h.remove(), n();
    });
  };
})(jQuery);
/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(0)))

/***/ }),

/***/ "./common/static/js/vendor/jquery.cookie.js":
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(jQuery) {/*!
 * jQuery Cookie Plugin
 * https://github.com/carhartl/jquery-cookie
 *
 * Copyright 2011, Klaus Hartl
 * Dual licensed under the MIT or GPL Version 2 licenses.
 * http://www.opensource.org/licenses/mit-license.php
 * http://www.opensource.org/licenses/GPL-2.0
 */
(function ($) {
    $.cookie = function (key, value, options) {

        // key and at least value given, set cookie...
        if (arguments.length > 1 && (!/Object/.test(Object.prototype.toString.call(value)) || value === null || value === undefined)) {
            options = $.extend({}, options);

            if (value === null || value === undefined) {
                options.expires = -1;
            }

            if (typeof options.expires === 'number') {
                var days = options.expires,
                    t = options.expires = new Date();
                t.setDate(t.getDate() + days);
            }

            value = String(value);

            return document.cookie = [encodeURIComponent(key), '=', options.raw ? value : encodeURIComponent(value), options.expires ? '; expires=' + options.expires.toUTCString() : '', // use expires attribute, max-age is not supported by IE
            options.path ? '; path=' + options.path : '', options.domain ? '; domain=' + options.domain : '', options.secure ? '; secure' : ''].join('');
        }

        // key and possibly options given, get cookie...
        options = value || {};
        var decode = options.raw ? function (s) {
            return s;
        } : decodeURIComponent;

        var pairs = document.cookie.split('; ');
        for (var i = 0, pair; pair = pairs[i] && pairs[i].split('='); i++) {
            if (decode(pair[0]) === key) return decode(pair[1] || ''); // IE saves cookies with empty string as "c; ", e.g. without "=" as opposed to EOMB, thus pair[1] may be undefined
        }
        return null;
    };
})(jQuery);
/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(0)))

/***/ }),

/***/ "./common/static/js/vendor/jquery.form.js":
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(jQuery) {var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; };

/*!
 * jQuery Form Plugin
 * version: 3.18 (28-SEP-2012)
 * @requires jQuery v1.5 or later
 *
 * Examples and documentation at: http://malsup.com/jquery/form/
 * Project repository: https://github.com/malsup/form
 * Dual licensed under the MIT and GPL licenses:
 *    http://malsup.github.com/mit-license.txt
 *    http://malsup.github.com/gpl-license-v2.txt
 */
/*global ActiveXObject alert */
;(function ($) {
    "use strict";

    /*
        Usage Note:
        -----------
        Do not use both ajaxSubmit and ajaxForm on the same form.  These
        functions are mutually exclusive.  Use ajaxSubmit if you want
        to bind your own submit handler to the form.  For example,
    
        $(document).ready(function() {
            $('#myForm').on('submit', function(e) {
                e.preventDefault(); // <-- important
                $(this).ajaxSubmit({
                    target: '#output'
                });
            });
        });
    
        Use ajaxForm when you want the plugin to manage all the event binding
        for you.  For example,
    
        $(document).ready(function() {
            $('#myForm').ajaxForm({
                target: '#output'
            });
        });
        
        You can also use ajaxForm with delegation (requires jQuery v1.7+), so the
        form does not have to exist when you invoke ajaxForm:
    
        $('#myForm').ajaxForm({
            delegation: true,
            target: '#output'
        });
        
        When using ajaxForm, the ajaxSubmit function will be invoked for you
        at the appropriate time.
    */

    /**
     * Feature detection
     */

    var feature = {};
    feature.fileapi = $("<input type='file'/>").get(0).files !== undefined;
    feature.formdata = window.FormData !== undefined;

    /**
     * ajaxSubmit() provides a mechanism for immediately submitting
     * an HTML form using AJAX.
     */
    $.fn.ajaxSubmit = function (options) {
        /*jshint scripturl:true */

        // fast fail if nothing selected (http://dev.jquery.com/ticket/2752)
        if (!this.length) {
            log('ajaxSubmit: skipping submit process - no element selected');
            return this;
        }

        var method,
            action,
            url,
            $form = this;

        if (typeof options == 'function') {
            options = { success: options };
        }

        method = this.attr('method');
        action = this.attr('action');
        url = typeof action === 'string' ? $.trim(action) : '';
        url = url || window.location.href || '';
        if (url) {
            // clean url (don't include hash vaue)
            url = (url.match(/^([^#]+)/) || [])[1];
        }

        options = $.extend(true, {
            url: url,
            success: $.ajaxSettings.success,
            type: method || 'GET',
            iframeSrc: /^https/i.test(window.location.href || '') ? 'javascript:false' : 'about:blank'
        }, options);

        // hook for manipulating the form data before it is extracted;
        // convenient for use with rich editors like tinyMCE or FCKEditor
        var veto = {};
        this.trigger('form-pre-serialize', [this, options, veto]);
        if (veto.veto) {
            log('ajaxSubmit: submit vetoed via form-pre-serialize trigger');
            return this;
        }

        // provide opportunity to alter form data before it is serialized
        if (options.beforeSerialize && options.beforeSerialize(this, options) === false) {
            log('ajaxSubmit: submit aborted via beforeSerialize callback');
            return this;
        }

        var traditional = options.traditional;
        if (traditional === undefined) {
            traditional = $.ajaxSettings.traditional;
        }

        var elements = [];
        var qx,
            a = this.formToArray(options.semantic, elements);
        if (options.data) {
            options.extraData = options.data;
            qx = $.param(options.data, traditional);
        }

        // give pre-submit callback an opportunity to abort the submit
        if (options.beforeSubmit && options.beforeSubmit(a, this, options) === false) {
            log('ajaxSubmit: submit aborted via beforeSubmit callback');
            return this;
        }

        // fire vetoable 'validate' event
        this.trigger('form-submit-validate', [a, this, options, veto]);
        if (veto.veto) {
            log('ajaxSubmit: submit vetoed via form-submit-validate trigger');
            return this;
        }

        var q = $.param(a, traditional);
        if (qx) {
            q = q ? q + '&' + qx : qx;
        }
        if (options.type.toUpperCase() == 'GET') {
            options.url += (options.url.indexOf('?') >= 0 ? '&' : '?') + q;
            options.data = null; // data is null for 'get'
        } else {
            options.data = q; // data is the query string for 'post'
        }

        var callbacks = [];
        if (options.resetForm) {
            callbacks.push(function () {
                $form.resetForm();
            });
        }
        if (options.clearForm) {
            callbacks.push(function () {
                $form.clearForm(options.includeHidden);
            });
        }

        // perform a load on the target only if dataType is not provided
        if (!options.dataType && options.target) {
            var oldSuccess = options.success || function () {};
            callbacks.push(function (data) {
                var fn = options.replaceTarget ? 'replaceWith' : 'html';
                $(options.target)[fn](data).each(oldSuccess, arguments);
            });
        } else if (options.success) {
            callbacks.push(options.success);
        }

        options.success = function (data, status, xhr) {
            // jQuery 1.4+ passes xhr as 3rd arg
            var context = options.context || this; // jQuery 1.4+ supports scope context 
            for (var i = 0, max = callbacks.length; i < max; i++) {
                callbacks[i].apply(context, [data, status, xhr || $form, $form]);
            }
        };

        // are there files to upload?
        var fileInputs = $('input:file:enabled[value]', this); // [value] (issue #113)
        var hasFileInputs = fileInputs.length > 0;
        var mp = 'multipart/form-data';
        var multipart = $form.attr('enctype') == mp || $form.attr('encoding') == mp;

        var fileAPI = feature.fileapi && feature.formdata;
        log("fileAPI :" + fileAPI);
        var shouldUseFrame = (hasFileInputs || multipart) && !fileAPI;

        var jqxhr;

        // options.iframe allows user to force iframe mode
        // 06-NOV-09: now defaulting to iframe mode if file input is detected
        if (options.iframe !== false && (options.iframe || shouldUseFrame)) {
            // hack to fix Safari hang (thanks to Tim Molendijk for this)
            // see:  http://groups.google.com/group/jquery-dev/browse_thread/thread/36395b7ab510dd5d
            if (options.closeKeepAlive) {
                $.get(options.closeKeepAlive, function () {
                    jqxhr = fileUploadIframe(a);
                });
            } else {
                jqxhr = fileUploadIframe(a);
            }
        } else if ((hasFileInputs || multipart) && fileAPI) {
            jqxhr = fileUploadXhr(a);
        } else {
            jqxhr = $.ajax(options);
        }

        $form.removeData('jqxhr').data('jqxhr', jqxhr);

        // clear element array
        for (var k = 0; k < elements.length; k++) {
            elements[k] = null;
        } // fire 'notify' event
        this.trigger('form-submit-notify', [this, options]);
        return this;

        // utility fn for deep serialization
        function deepSerialize(extraData) {
            var serialized = $.param(extraData).split('&');
            var len = serialized.length;
            var result = {};
            var i, part;
            for (i = 0; i < len; i++) {
                part = serialized[i].split('=');
                result[decodeURIComponent(part[0])] = decodeURIComponent(part[1]);
            }
            return result;
        }

        // XMLHttpRequest Level 2 file uploads (big hat tip to francois2metz)
        function fileUploadXhr(a) {
            var formdata = new FormData();

            for (var i = 0; i < a.length; i++) {
                formdata.append(a[i].name, a[i].value);
            }

            if (options.extraData) {
                var serializedData = deepSerialize(options.extraData);
                for (var p in serializedData) {
                    if (serializedData.hasOwnProperty(p)) formdata.append(p, serializedData[p]);
                }
            }

            options.data = null;

            var s = $.extend(true, {}, $.ajaxSettings, options, {
                contentType: false,
                processData: false,
                cache: false,
                type: method || 'POST'
            });

            if (options.uploadProgress) {
                // workaround because jqXHR does not expose upload property
                s.xhr = function () {
                    var xhr = jQuery.ajaxSettings.xhr();
                    if (xhr.upload) {
                        xhr.upload.onprogress = function (event) {
                            var percent = 0;
                            var position = event.loaded || event.position; /*event.position is deprecated*/
                            var total = event.total;
                            if (event.lengthComputable) {
                                percent = Math.ceil(position / total * 100);
                            }
                            options.uploadProgress(event, position, total, percent);
                        };
                    }
                    return xhr;
                };
            }

            s.data = null;
            var beforeSend = s.beforeSend;
            s.beforeSend = function (xhr, o) {
                o.data = formdata;
                if (beforeSend) beforeSend.call(this, xhr, o);
            };
            return $.ajax(s);
        }

        // private function for handling file uploads (hat tip to YAHOO!)
        function fileUploadIframe(a) {
            var form = $form[0],
                el,
                i,
                s,
                g,
                id,
                $io,
                io,
                xhr,
                sub,
                n,
                timedOut,
                timeoutHandle;
            var useProp = !!$.fn.prop;
            var deferred = $.Deferred();

            if ($(':input[name=submit],:input[id=submit]', form).length) {
                // if there is an input with a name or id of 'submit' then we won't be
                // able to invoke the submit fn on the form (at least not x-browser)
                alert('Error: Form elements must not have name or id of "submit".');
                deferred.reject();
                return deferred;
            }

            if (a) {
                // ensure that every serialized input is still enabled
                for (i = 0; i < elements.length; i++) {
                    el = $(elements[i]);
                    if (useProp) el.prop('disabled', false);else el.removeAttr('disabled');
                }
            }

            s = $.extend(true, {}, $.ajaxSettings, options);
            s.context = s.context || s;
            id = 'jqFormIO' + new Date().getTime();
            if (s.iframeTarget) {
                $io = $(s.iframeTarget);
                n = $io.attr('name');
                if (!n) $io.attr('name', id);else id = n;
            } else {
                $io = $('<iframe name="' + id + '" src="' + s.iframeSrc + '" />');
                $io.css({ position: 'absolute', top: '-1000px', left: '-1000px' });
            }
            io = $io[0];

            xhr = { // mock object
                aborted: 0,
                responseText: null,
                responseXML: null,
                status: 0,
                statusText: 'n/a',
                getAllResponseHeaders: function getAllResponseHeaders() {},
                getResponseHeader: function getResponseHeader() {},
                setRequestHeader: function setRequestHeader() {},
                abort: function abort(status) {
                    var e = status === 'timeout' ? 'timeout' : 'aborted';
                    log('aborting upload... ' + e);
                    this.aborted = 1;
                    // #214
                    if (io.contentWindow.document.execCommand) {
                        try {
                            // #214
                            io.contentWindow.document.execCommand('Stop');
                        } catch (ignore) {}
                    }
                    $io.attr('src', s.iframeSrc); // abort op in progress
                    xhr.error = e;
                    if (s.error) s.error.call(s.context, xhr, e, status);
                    if (g) $.event.trigger("ajaxError", [xhr, s, e]);
                    if (s.complete) s.complete.call(s.context, xhr, e);
                }
            };

            g = s.global;
            // trigger ajax global events so that activity/block indicators work like normal
            if (g && 0 === $.active++) {
                $.event.trigger("ajaxStart");
            }
            if (g) {
                $.event.trigger("ajaxSend", [xhr, s]);
            }

            if (s.beforeSend && s.beforeSend.call(s.context, xhr, s) === false) {
                if (s.global) {
                    $.active--;
                }
                deferred.reject();
                return deferred;
            }
            if (xhr.aborted) {
                deferred.reject();
                return deferred;
            }

            // add submitting element to data if we know it
            sub = form.clk;
            if (sub) {
                n = sub.name;
                if (n && !sub.disabled) {
                    s.extraData = s.extraData || {};
                    s.extraData[n] = sub.value;
                    if (sub.type == "image") {
                        s.extraData[n + '.x'] = form.clk_x;
                        s.extraData[n + '.y'] = form.clk_y;
                    }
                }
            }

            var CLIENT_TIMEOUT_ABORT = 1;
            var SERVER_ABORT = 2;

            function getDoc(frame) {
                var doc = frame.contentWindow ? frame.contentWindow.document : frame.contentDocument ? frame.contentDocument : frame.document;
                return doc;
            }

            // Rails CSRF hack (thanks to Yvan Barthelemy)
            var csrf_token = $('meta[name=csrf-token]').attr('content');
            var csrf_param = $('meta[name=csrf-param]').attr('content');
            if (csrf_param && csrf_token) {
                s.extraData = s.extraData || {};
                s.extraData[csrf_param] = csrf_token;
            }

            // take a breath so that pending repaints get some cpu time before the upload starts
            function doSubmit() {
                // make sure form attrs are set
                var t = $form.attr('target'),
                    a = $form.attr('action');

                // update form attrs in IE friendly way
                form.setAttribute('target', id);
                if (!method) {
                    form.setAttribute('method', 'POST');
                }
                if (a != s.url) {
                    form.setAttribute('action', s.url);
                }

                // ie borks in some cases when setting encoding
                if (!s.skipEncodingOverride && (!method || /post/i.test(method))) {
                    $form.attr({
                        encoding: 'multipart/form-data',
                        enctype: 'multipart/form-data'
                    });
                }

                // support timout
                if (s.timeout) {
                    timeoutHandle = setTimeout(function () {
                        timedOut = true;cb(CLIENT_TIMEOUT_ABORT);
                    }, s.timeout);
                }

                // look for server aborts
                function checkState() {
                    try {
                        var state = getDoc(io).readyState;
                        log('state = ' + state);
                        if (state && state.toLowerCase() == 'uninitialized') setTimeout(checkState, 50);
                    } catch (e) {
                        log('Server abort: ', e, ' (', e.name, ')');
                        cb(SERVER_ABORT);
                        if (timeoutHandle) clearTimeout(timeoutHandle);
                        timeoutHandle = undefined;
                    }
                }

                // add "extra" data to form if provided in options
                var extraInputs = [];
                try {
                    if (s.extraData) {
                        for (var n in s.extraData) {
                            if (s.extraData.hasOwnProperty(n)) {
                                // if using the $.param format that allows for multiple values with the same name
                                if ($.isPlainObject(s.extraData[n]) && s.extraData[n].hasOwnProperty('name') && s.extraData[n].hasOwnProperty('value')) {
                                    extraInputs.push($('<input type="hidden" name="' + s.extraData[n].name + '">').attr('value', s.extraData[n].value).appendTo(form)[0]);
                                } else {
                                    extraInputs.push($('<input type="hidden" name="' + n + '">').attr('value', s.extraData[n]).appendTo(form)[0]);
                                }
                            }
                        }
                    }

                    if (!s.iframeTarget) {
                        // add iframe to doc and submit the form
                        $io.appendTo('body');
                        if (io.attachEvent) io.attachEvent('onload', cb);else io.addEventListener('load', cb, false);
                    }
                    setTimeout(checkState, 15);
                    form.submit();
                } finally {
                    // reset attrs and remove "extra" input elements
                    form.setAttribute('action', a);
                    if (t) {
                        form.setAttribute('target', t);
                    } else {
                        $form.removeAttr('target');
                    }
                    $(extraInputs).remove();
                }
            }

            if (s.forceSync) {
                doSubmit();
            } else {
                setTimeout(doSubmit, 10); // this lets dom updates render
            }

            var data,
                doc,
                domCheckCount = 50,
                callbackProcessed;

            function cb(e) {
                if (xhr.aborted || callbackProcessed) {
                    return;
                }
                try {
                    doc = getDoc(io);
                } catch (ex) {
                    log('cannot access response document: ', ex);
                    e = SERVER_ABORT;
                }
                if (e === CLIENT_TIMEOUT_ABORT && xhr) {
                    xhr.abort('timeout');
                    deferred.reject(xhr, 'timeout');
                    return;
                } else if (e == SERVER_ABORT && xhr) {
                    xhr.abort('server abort');
                    deferred.reject(xhr, 'error', 'server abort');
                    return;
                }

                if (!doc || doc.location.href == s.iframeSrc) {
                    // response not received yet
                    if (!timedOut) return;
                }
                if (io.detachEvent) io.detachEvent('onload', cb);else io.removeEventListener('load', cb, false);

                var status = 'success',
                    errMsg;
                try {
                    if (timedOut) {
                        throw 'timeout';
                    }

                    var isXml = s.dataType == 'xml' || doc.XMLDocument || $.isXMLDoc(doc);
                    log('isXml=' + isXml);
                    if (!isXml && window.opera && (doc.body === null || !doc.body.innerHTML)) {
                        if (--domCheckCount) {
                            // in some browsers (Opera) the iframe DOM is not always traversable when
                            // the onload callback fires, so we loop a bit to accommodate
                            log('requeing onLoad callback, DOM not available');
                            setTimeout(cb, 250);
                            return;
                        }
                        // let this fall through because server response could be an empty document
                        //log('Could not access iframe DOM after mutiple tries.');
                        //throw 'DOMException: not available';
                    }

                    //log('response detected');
                    var docRoot = doc.body ? doc.body : doc.documentElement;
                    xhr.responseText = docRoot ? docRoot.innerHTML : null;
                    xhr.responseXML = doc.XMLDocument ? doc.XMLDocument : doc;
                    if (isXml) s.dataType = 'xml';
                    xhr.getResponseHeader = function (header) {
                        var headers = { 'content-type': s.dataType };
                        return headers[header];
                    };
                    // support for XHR 'status' & 'statusText' emulation :
                    if (docRoot) {
                        xhr.status = Number(docRoot.getAttribute('status')) || xhr.status;
                        xhr.statusText = docRoot.getAttribute('statusText') || xhr.statusText;
                    }

                    var dt = (s.dataType || '').toLowerCase();
                    var scr = /(json|script|text)/.test(dt);
                    if (scr || s.textarea) {
                        // see if user embedded response in textarea
                        var ta = doc.getElementsByTagName('textarea')[0];
                        if (ta) {
                            xhr.responseText = ta.value;
                            // support for XHR 'status' & 'statusText' emulation :
                            xhr.status = Number(ta.getAttribute('status')) || xhr.status;
                            xhr.statusText = ta.getAttribute('statusText') || xhr.statusText;
                        } else if (scr) {
                            // account for browsers injecting pre around json response
                            var pre = doc.getElementsByTagName('pre')[0];
                            var b = doc.getElementsByTagName('body')[0];
                            if (pre) {
                                xhr.responseText = pre.textContent ? pre.textContent : pre.innerText;
                            } else if (b) {
                                xhr.responseText = b.textContent ? b.textContent : b.innerText;
                            }
                        }
                    } else if (dt == 'xml' && !xhr.responseXML && xhr.responseText) {
                        xhr.responseXML = toXml(xhr.responseText);
                    }

                    try {
                        data = httpData(xhr, dt, s);
                    } catch (e) {
                        status = 'parsererror';
                        xhr.error = errMsg = e || status;
                    }
                } catch (e) {
                    log('error caught: ', e);
                    status = 'error';
                    xhr.error = errMsg = e || status;
                }

                if (xhr.aborted) {
                    log('upload aborted');
                    status = null;
                }

                if (xhr.status) {
                    // we've set xhr.status
                    status = xhr.status >= 200 && xhr.status < 300 || xhr.status === 304 ? 'success' : 'error';
                }

                // ordering of these callbacks/triggers is odd, but that's how $.ajax does it
                if (status === 'success') {
                    if (s.success) s.success.call(s.context, data, 'success', xhr);
                    deferred.resolve(xhr.responseText, 'success', xhr);
                    if (g) $.event.trigger("ajaxSuccess", [xhr, s]);
                } else if (status) {
                    if (errMsg === undefined) errMsg = xhr.statusText;
                    if (s.error) s.error.call(s.context, xhr, status, errMsg);
                    deferred.reject(xhr, 'error', errMsg);
                    if (g) $.event.trigger("ajaxError", [xhr, s, errMsg]);
                }

                if (g) $.event.trigger("ajaxComplete", [xhr, s]);

                if (g && ! --$.active) {
                    $.event.trigger("ajaxStop");
                }

                if (s.complete) s.complete.call(s.context, xhr, status);

                callbackProcessed = true;
                if (s.timeout) clearTimeout(timeoutHandle);

                // clean up
                setTimeout(function () {
                    if (!s.iframeTarget) $io.remove();
                    xhr.responseXML = null;
                }, 100);
            }

            var toXml = $.parseXML || function (s, doc) {
                // use parseXML if available (jQuery 1.5+)
                if (window.ActiveXObject) {
                    doc = new ActiveXObject('Microsoft.XMLDOM');
                    doc.async = 'false';
                    doc.loadXML(s);
                } else {
                    doc = new DOMParser().parseFromString(s, 'text/xml');
                }
                return doc && doc.documentElement && doc.documentElement.nodeName != 'parsererror' ? doc : null;
            };
            var parseJSON = $.parseJSON || function (s) {
                /*jslint evil:true */
                return window['eval']('(' + s + ')');
            };

            var httpData = function httpData(xhr, type, s) {
                // mostly lifted from jq1.4.4

                var ct = xhr.getResponseHeader('content-type') || '',
                    xml = type === 'xml' || !type && ct.indexOf('xml') >= 0,
                    data = xml ? xhr.responseXML : xhr.responseText;

                if (xml && data.documentElement.nodeName === 'parsererror') {
                    if ($.error) $.error('parsererror');
                }
                if (s && s.dataFilter) {
                    data = s.dataFilter(data, type);
                }
                if (typeof data === 'string') {
                    if (type === 'json' || !type && ct.indexOf('json') >= 0) {
                        data = parseJSON(data);
                    } else if (type === "script" || !type && ct.indexOf("javascript") >= 0) {
                        $.globalEval(data);
                    }
                }
                return data;
            };

            return deferred;
        }
    };

    /**
     * ajaxForm() provides a mechanism for fully automating form submission.
     *
     * The advantages of using this method instead of ajaxSubmit() are:
     *
     * 1: This method will include coordinates for <input type="image" /> elements (if the element
     *    is used to submit the form).
     * 2. This method will include the submit element's name/value data (for the element that was
     *    used to submit the form).
     * 3. This method binds the submit() method to the form for you.
     *
     * The options argument for ajaxForm works exactly as it does for ajaxSubmit.  ajaxForm merely
     * passes the options argument along after properly binding events for submit elements and
     * the form itself.
     */
    $.fn.ajaxForm = function (options) {
        options = options || {};
        options.delegation = options.delegation && $.isFunction($.fn.on);

        // in jQuery 1.3+ we can fix mistakes with the ready state
        if (!options.delegation && this.length === 0) {
            var o = { s: this.selector, c: this.context };
            if (!$.isReady && o.s) {
                log('DOM not ready, queuing ajaxForm');
                $(function () {
                    $(o.s, o.c).ajaxForm(options);
                });
                return this;
            }
            // is your DOM ready?  http://docs.jquery.com/Tutorials:Introducing_$(document).ready()
            log('terminating; zero elements found by selector' + ($.isReady ? '' : ' (DOM not ready)'));
            return this;
        }

        if (options.delegation) {
            $(document).off('submit.form-plugin', this.selector, doAjaxSubmit).off('click.form-plugin', this.selector, captureSubmittingElement).on('submit.form-plugin', this.selector, options, doAjaxSubmit).on('click.form-plugin', this.selector, options, captureSubmittingElement);
            return this;
        }

        return this.ajaxFormUnbind().bind('submit.form-plugin', options, doAjaxSubmit).bind('click.form-plugin', options, captureSubmittingElement);
    };

    // private event handlers    
    function doAjaxSubmit(e) {
        /*jshint validthis:true */
        var options = e.data;
        if (!e.isDefaultPrevented()) {
            // if event has been canceled, don't proceed
            e.preventDefault();
            $(this).ajaxSubmit(options);
        }
    }

    function captureSubmittingElement(e) {
        /*jshint validthis:true */
        var target = e.target;
        var $el = $(target);
        if (!$el.is(":submit,input:image")) {
            // is this a child element of the submit el?  (ex: a span within a button)
            var t = $el.closest(':submit');
            if (t.length === 0) {
                return;
            }
            target = t[0];
        }
        var form = this;
        form.clk = target;
        if (target.type == 'image') {
            if (e.offsetX !== undefined) {
                form.clk_x = e.offsetX;
                form.clk_y = e.offsetY;
            } else if (typeof $.fn.offset == 'function') {
                var offset = $el.offset();
                form.clk_x = e.pageX - offset.left;
                form.clk_y = e.pageY - offset.top;
            } else {
                form.clk_x = e.pageX - target.offsetLeft;
                form.clk_y = e.pageY - target.offsetTop;
            }
        }
        // clear form vars
        setTimeout(function () {
            form.clk = form.clk_x = form.clk_y = null;
        }, 100);
    }

    // ajaxFormUnbind unbinds the event handlers that were bound by ajaxForm
    $.fn.ajaxFormUnbind = function () {
        return this.unbind('submit.form-plugin click.form-plugin');
    };

    /**
     * formToArray() gathers form element data into an array of objects that can
     * be passed to any of the following ajax functions: $.get, $.post, or load.
     * Each object in the array has both a 'name' and 'value' property.  An example of
     * an array for a simple login form might be:
     *
     * [ { name: 'username', value: 'jresig' }, { name: 'password', value: 'secret' } ]
     *
     * It is this array that is passed to pre-submit callback functions provided to the
     * ajaxSubmit() and ajaxForm() methods.
     */
    $.fn.formToArray = function (semantic, elements) {
        var a = [];
        if (this.length === 0) {
            return a;
        }

        var form = this[0];
        var els = semantic ? form.getElementsByTagName('*') : form.elements;
        if (!els) {
            return a;
        }

        var i, j, n, v, el, max, jmax;
        for (i = 0, max = els.length; i < max; i++) {
            el = els[i];
            n = el.name;
            if (!n) {
                continue;
            }

            if (semantic && form.clk && el.type == "image") {
                // handle image inputs on the fly when semantic == true
                if (!el.disabled && form.clk == el) {
                    a.push({ name: n, value: $(el).val(), type: el.type });
                    a.push({ name: n + '.x', value: form.clk_x }, { name: n + '.y', value: form.clk_y });
                }
                continue;
            }

            v = $.fieldValue(el, true);
            if (v && v.constructor == Array) {
                if (elements) elements.push(el);
                for (j = 0, jmax = v.length; j < jmax; j++) {
                    a.push({ name: n, value: v[j] });
                }
            } else if (feature.fileapi && el.type == 'file' && !el.disabled) {
                if (elements) elements.push(el);
                var files = el.files;
                if (files.length) {
                    for (j = 0; j < files.length; j++) {
                        a.push({ name: n, value: files[j], type: el.type });
                    }
                } else {
                    // #180
                    a.push({ name: n, value: '', type: el.type });
                }
            } else if (v !== null && typeof v != 'undefined') {
                if (elements) elements.push(el);
                a.push({ name: n, value: v, type: el.type, required: el.required });
            }
        }

        if (!semantic && form.clk) {
            // input type=='image' are not found in elements array! handle it here
            var $input = $(form.clk),
                input = $input[0];
            n = input.name;
            if (n && !input.disabled && input.type == 'image') {
                a.push({ name: n, value: $input.val() });
                a.push({ name: n + '.x', value: form.clk_x }, { name: n + '.y', value: form.clk_y });
            }
        }
        return a;
    };

    /**
     * Serializes form data into a 'submittable' string. This method will return a string
     * in the format: name1=value1&amp;name2=value2
     */
    $.fn.formSerialize = function (semantic) {
        //hand off to jQuery.param for proper encoding
        return $.param(this.formToArray(semantic));
    };

    /**
     * Serializes all field elements in the jQuery object into a query string.
     * This method will return a string in the format: name1=value1&amp;name2=value2
     */
    $.fn.fieldSerialize = function (successful) {
        var a = [];
        this.each(function () {
            var n = this.name;
            if (!n) {
                return;
            }
            var v = $.fieldValue(this, successful);
            if (v && v.constructor == Array) {
                for (var i = 0, max = v.length; i < max; i++) {
                    a.push({ name: n, value: v[i] });
                }
            } else if (v !== null && typeof v != 'undefined') {
                a.push({ name: this.name, value: v });
            }
        });
        //hand off to jQuery.param for proper encoding
        return $.param(a);
    };

    /**
     * Returns the value(s) of the element in the matched set.  For example, consider the following form:
     *
     *  <form><fieldset>
     *      <input name="A" type="text" />
     *      <input name="A" type="text" />
     *      <input name="B" type="checkbox" value="B1" />
     *      <input name="B" type="checkbox" value="B2"/>
     *      <input name="C" type="radio" value="C1" />
     *      <input name="C" type="radio" value="C2" />
     *  </fieldset></form>
     *
     *  var v = $(':text').fieldValue();
     *  // if no values are entered into the text inputs
     *  v == ['','']
     *  // if values entered into the text inputs are 'foo' and 'bar'
     *  v == ['foo','bar']
     *
     *  var v = $(':checkbox').fieldValue();
     *  // if neither checkbox is checked
     *  v === undefined
     *  // if both checkboxes are checked
     *  v == ['B1', 'B2']
     *
     *  var v = $(':radio').fieldValue();
     *  // if neither radio is checked
     *  v === undefined
     *  // if first radio is checked
     *  v == ['C1']
     *
     * The successful argument controls whether or not the field element must be 'successful'
     * (per http://www.w3.org/TR/html4/interact/forms.html#successful-controls).
     * The default value of the successful argument is true.  If this value is false the value(s)
     * for each element is returned.
     *
     * Note: This method *always* returns an array.  If no valid value can be determined the
     *    array will be empty, otherwise it will contain one or more values.
     */
    $.fn.fieldValue = function (successful) {
        for (var val = [], i = 0, max = this.length; i < max; i++) {
            var el = this[i];
            var v = $.fieldValue(el, successful);
            if (v === null || typeof v == 'undefined' || v.constructor == Array && !v.length) {
                continue;
            }
            if (v.constructor == Array) $.merge(val, v);else val.push(v);
        }
        return val;
    };

    /**
     * Returns the value of the field element.
     */
    $.fieldValue = function (el, successful) {
        var n = el.name,
            t = el.type,
            tag = el.tagName.toLowerCase();
        if (successful === undefined) {
            successful = true;
        }

        if (successful && (!n || el.disabled || t == 'reset' || t == 'button' || (t == 'checkbox' || t == 'radio') && !el.checked || (t == 'submit' || t == 'image') && el.form && el.form.clk != el || tag == 'select' && el.selectedIndex == -1)) {
            return null;
        }

        if (tag == 'select') {
            var index = el.selectedIndex;
            if (index < 0) {
                return null;
            }
            var a = [],
                ops = el.options;
            var one = t == 'select-one';
            var max = one ? index + 1 : ops.length;
            for (var i = one ? index : 0; i < max; i++) {
                var op = ops[i];
                if (op.selected) {
                    var v = op.value;
                    if (!v) {
                        // extra pain for IE...
                        v = op.attributes && op.attributes['value'] && !op.attributes['value'].specified ? op.text : op.value;
                    }
                    if (one) {
                        return v;
                    }
                    a.push(v);
                }
            }
            return a;
        }
        return $(el).val();
    };

    /**
     * Clears the form data.  Takes the following actions on the form's input fields:
     *  - input text fields will have their 'value' property set to the empty string
     *  - select elements will have their 'selectedIndex' property set to -1
     *  - checkbox and radio inputs will have their 'checked' property set to false
     *  - inputs of type submit, button, reset, and hidden will *not* be effected
     *  - button elements will *not* be effected
     */
    $.fn.clearForm = function (includeHidden) {
        return this.each(function () {
            $('input,select,textarea', this).clearFields(includeHidden);
        });
    };

    /**
     * Clears the selected form elements.
     */
    $.fn.clearFields = $.fn.clearInputs = function (includeHidden) {
        var re = /^(?:color|date|datetime|email|month|number|password|range|search|tel|text|time|url|week)$/i; // 'hidden' is not in this list
        return this.each(function () {
            var t = this.type,
                tag = this.tagName.toLowerCase();
            if (re.test(t) || tag == 'textarea') {
                this.value = '';
            } else if (t == 'checkbox' || t == 'radio') {
                this.checked = false;
            } else if (tag == 'select') {
                this.selectedIndex = -1;
            } else if (includeHidden) {
                // includeHidden can be the value true, or it can be a selector string
                // indicating a special test; for example:
                //  $('#myForm').clearForm('.special:hidden')
                // the above would clean hidden inputs that have the class of 'special'
                if (includeHidden === true && /hidden/.test(t) || typeof includeHidden == 'string' && $(this).is(includeHidden)) this.value = '';
            }
        });
    };

    /**
     * Resets the form data.  Causes all form elements to be reset to their original value.
     */
    $.fn.resetForm = function () {
        return this.each(function () {
            // guard against an input with the name of 'reset'
            // note that IE reports the reset function as an 'object'
            if (typeof this.reset == 'function' || _typeof(this.reset) == 'object' && !this.reset.nodeType) {
                this.reset();
            }
        });
    };

    /**
     * Enables or disables any matching elements.
     */
    $.fn.enable = function (b) {
        if (b === undefined) {
            b = true;
        }
        return this.each(function () {
            this.disabled = !b;
        });
    };

    /**
     * Checks/unchecks any matching checkboxes or radio buttons and
     * selects/deselects and matching option elements.
     */
    $.fn.selected = function (select) {
        if (select === undefined) {
            select = true;
        }
        return this.each(function () {
            var t = this.type;
            if (t == 'checkbox' || t == 'radio') {
                this.checked = select;
            } else if (this.tagName.toLowerCase() == 'option') {
                var $sel = $(this).parent('select');
                if (select && $sel[0] && $sel[0].type == 'select-one') {
                    // deselect all other options
                    $sel.find('option').selected(false);
                }
                this.selected = select;
            }
        });
    };

    // expose debug var
    $.fn.ajaxSubmit.debug = false;

    // helper fn for console logging
    function log() {
        if (!$.fn.ajaxSubmit.debug) return;
        var msg = '[jquery.form] ' + Array.prototype.join.call(arguments, '');
        if (window.console && window.console.log) {
            window.console.log(msg);
        } else if (window.opera && window.opera.postError) {
            window.opera.postError(msg);
        }
    }
})(jQuery);
/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(0)))

/***/ }),

/***/ "./common/static/js/vendor/jquery.leanModal.js":
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(jQuery) {// leanModal v1.1 by Ray Stone - http://finelysliced.com.au
// Dual licensed under the MIT and GPL

// Updated to prevent divs with duplicate IDs from being rendered.

(function ($) {
    $.fn.extend({
        leanModal: function leanModal(options) {
            var defaults = {
                top: 100,
                overlay: 0.5,
                closeButton: null
            };

            // Only append the overlay element if it isn't already present.
            if ($("#lean_overlay").length == 0) {
                var overlay = $("<div id='lean_overlay'></div>");
                $("body").append(overlay);
            }

            options = $.extend(defaults, options);
            return this.each(function () {
                var o = options;
                $(this).click(function (e) {
                    var modal_id = $(this).attr("href");
                    $("#lean_overlay").click(function () {
                        close_modal(modal_id);
                    });
                    $(o.closeButton).click(function () {
                        close_modal(modal_id);
                    });
                    var modal_height = $(modal_id).outerHeight();
                    var modal_width = $(modal_id).outerWidth();
                    $("#lean_overlay").css({
                        "display": "block",
                        opacity: 0
                    });
                    $("#lean_overlay").fadeTo(200, o.overlay);
                    $(modal_id).css({
                        "display": "block",
                        "position": "fixed",
                        "opacity": 0,
                        "z-index": 11000,
                        "left": 50 + "%",
                        "margin-left": -(modal_width / 2) + "px",
                        "top": o.top + "px"
                    });
                    $(modal_id).fadeTo(200, 1);
                    e.preventDefault();
                });
            });

            function close_modal(modal_id) {
                $("#lean_overlay").fadeOut(200);
                $(modal_id).css({
                    "display": "none"
                });
            }
        }
    });
})(jQuery);
/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(0)))

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

/***/ }),

/***/ "./common/static/js/vendor/timepicker/datepair.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;/************************
datepair.js

This is a component of the jquery-timepicker plugin

http://jonthornton.github.com/jquery-timepicker/

requires jQuery 1.6+

version: 1.2.2
************************/

!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(0), __webpack_require__("./common/static/js/vendor/jquery-ui.min.js"), __webpack_require__("./common/static/js/vendor/timepicker/jquery.timepicker.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function ($) {

	$(function () {

		$('.datepair input.date').each(function () {
			var $this = $(this);
			$this.datepicker({ 'dateFormat': 'm/d/yy' });

			if ($this.hasClass('start') || $this.hasClass('end')) {
				$this.on('changeDate change', doDatepair);
			}
		});

		$('.datepair input.time').each(function () {
			var $this = $(this);
			var opts = { 'showDuration': true, 'timeFormat': 'H:i', 'scrollDefaultNow': true };

			if ($this.hasClass('start') || $this.hasClass('end')) {
				opts.onSelect = doDatepair;
			}

			$this.timepicker(opts);
		});

		$('.datepair').each(initDatepair);

		function initDatepair() {
			var container = $(this);

			var startDateInput = container.find('input.start.date');
			var endDateInput = container.find('input.end.date');
			var dateDelta = 0;

			if (startDateInput.length && endDateInput.length) {
				var startDate = new Date(startDateInput.val());
				var endDate = new Date(endDateInput.val());

				dateDelta = endDate.getTime() - startDate.getTime();

				container.data('dateDelta', dateDelta);
			}

			var startTimeInput = container.find('input.start.time');
			var endTimeInput = container.find('input.end.time');

			if (startTimeInput.length && endTimeInput.length) {
				var startInt = startTimeInput.timepicker('getSecondsFromMidnight');
				var endInt = endTimeInput.timepicker('getSecondsFromMidnight');

				container.data('timeDelta', endInt - startInt);

				if (dateDelta < 86400000) {
					endTimeInput.timepicker('option', 'minTime', startInt);
				}
			}
		}

		function doDatepair() {
			var target = $(this);
			if (target.val() == '') {
				return;
			}

			var container = target.closest('.datepair');

			if (target.hasClass('date')) {
				updateDatePair(target, container);
			} else if (target.hasClass('time')) {
				updateTimePair(target, container);
			}
		}

		function updateDatePair(target, container) {
			var start = container.find('input.start.date');
			var end = container.find('input.end.date');

			if (!start.length || !end.length) {
				return;
			}

			var startDate = new Date(start.val());
			var endDate = new Date(end.val());

			var oldDelta = container.data('dateDelta');

			if (oldDelta && target.hasClass('start')) {
				var newEnd = new Date(startDate.getTime() + oldDelta);
				end.val(newEnd.format('m/d/Y'));
				end.datepicker('update');
				return;
			} else {
				var newDelta = endDate.getTime() - startDate.getTime();

				if (newDelta < 0) {
					newDelta = 0;

					if (target.hasClass('start')) {
						end.val(startDate.format('m/d/Y'));
						end.datepicker('update');
					} else if (target.hasClass('end')) {
						start.val(endDate.format('m/d/Y'));
						start.datepicker('update');
					}
				}

				if (newDelta < 86400000) {
					var startTimeVal = container.find('input.start.time').val();

					if (startTimeVal) {
						container.find('input.end.time').timepicker('option', { 'minTime': startTimeVal });
					}
				} else {
					container.find('input.end.time').timepicker('option', { 'minTime': null });
				}

				container.data('dateDelta', newDelta);
			}
		}

		function updateTimePair(target, container) {
			var start = container.find('input.start.time');
			var end = container.find('input.end.time');

			if (!start.length || !end.length) {
				return;
			}

			var startInt = start.timepicker('getSecondsFromMidnight');
			var endInt = end.timepicker('getSecondsFromMidnight');

			var oldDelta = container.data('timeDelta');
			var dateDelta = container.data('dateDelta');

			if (target.hasClass('start') && (!dateDelta || dateDelta < 86400000)) {
				end.timepicker('option', 'minTime', startInt);
			}

			var endDateAdvance = 0;
			var newDelta;

			if (oldDelta && target.hasClass('start')) {
				// lock the duration and advance the end time

				var newEnd = (startInt + oldDelta) % 86400;

				if (newEnd < 0) {
					newEnd += 86400;
				}

				end.timepicker('setTime', newEnd);
				newDelta = newEnd - startInt;
			} else if (startInt !== null && endInt !== null) {
				newDelta = endInt - startInt;
			} else {
				return;
			}

			container.data('timeDelta', newDelta);

			if (newDelta < 0 && (!oldDelta || oldDelta > 0)) {
				// overnight time span. advance the end date 1 day
				var endDateAdvance = 86400000;
			} else if (newDelta > 0 && oldDelta < 0) {
				// switching from overnight to same-day time span. decrease the end date 1 day
				var endDateAdvance = -86400000;
			}

			var startInput = container.find('.start.date');
			var endInput = container.find('.end.date');

			if (startInput.val() && !endInput.val()) {
				endInput.val(startInput.val());
				endInput.datepicker('update');
				dateDelta = 0;
				container.data('dateDelta', 0);
			}

			if (endDateAdvance != 0) {
				if (dateDelta || dateDelta === 0) {
					var endDate = new Date(endInput.val());
					var newEnd = new Date(endDate.getTime() + endDateAdvance);
					endInput.val(newEnd.format('m/d/Y'));
					endInput.datepicker('update');
					container.data('dateDelta', dateDelta + endDateAdvance);
				}
			}
		}
	});

	// Simulates PHP's date function
	Date.prototype.format = function (format) {
		var returnStr = '';var replace = Date.replaceChars;for (var i = 0; i < format.length; i++) {
			var curChar = format.charAt(i);if (replace[curChar]) {
				returnStr += replace[curChar].call(this);
			} else {
				returnStr += curChar;
			}
		}return returnStr;
	};Date.replaceChars = { shortMonths: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], longMonths: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'], shortDays: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'], longDays: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'], d: function d() {
			return (this.getDate() < 10 ? '0' : '') + this.getDate();
		}, D: function D() {
			return Date.replaceChars.shortDays[this.getDay()];
		}, j: function j() {
			return this.getDate();
		}, l: function l() {
			return Date.replaceChars.longDays[this.getDay()];
		}, N: function N() {
			return this.getDay() + 1;
		}, S: function S() {
			return this.getDate() % 10 == 1 && this.getDate() != 11 ? 'st' : this.getDate() % 10 == 2 && this.getDate() != 12 ? 'nd' : this.getDate() % 10 == 3 && this.getDate() != 13 ? 'rd' : 'th';
		}, w: function w() {
			return this.getDay();
		}, z: function z() {
			return "Not Yet Supported";
		}, W: function W() {
			return "Not Yet Supported";
		}, F: function F() {
			return Date.replaceChars.longMonths[this.getMonth()];
		}, m: function m() {
			return (this.getMonth() < 9 ? '0' : '') + (this.getMonth() + 1);
		}, M: function M() {
			return Date.replaceChars.shortMonths[this.getMonth()];
		}, n: function n() {
			return this.getMonth() + 1;
		}, t: function t() {
			return "Not Yet Supported";
		}, L: function L() {
			return this.getFullYear() % 4 == 0 && this.getFullYear() % 100 != 0 || this.getFullYear() % 400 == 0 ? '1' : '0';
		}, o: function o() {
			return "Not Supported";
		}, Y: function Y() {
			return this.getFullYear();
		}, y: function y() {
			return ('' + this.getFullYear()).substr(2);
		}, a: function a() {
			return this.getHours() < 12 ? 'am' : 'pm';
		}, A: function A() {
			return this.getHours() < 12 ? 'AM' : 'PM';
		}, B: function B() {
			return "Not Yet Supported";
		}, g: function g() {
			return this.getHours() % 12 || 12;
		}, G: function G() {
			return this.getHours();
		}, h: function h() {
			return ((this.getHours() % 12 || 12) < 10 ? '0' : '') + (this.getHours() % 12 || 12);
		}, H: function H() {
			return (this.getHours() < 10 ? '0' : '') + this.getHours();
		}, i: function i() {
			return (this.getMinutes() < 10 ? '0' : '') + this.getMinutes();
		}, s: function s() {
			return (this.getSeconds() < 10 ? '0' : '') + this.getSeconds();
		}, e: function e() {
			return "Not Yet Supported";
		}, I: function I() {
			return "Not Supported";
		}, O: function O() {
			return (-this.getTimezoneOffset() < 0 ? '-' : '+') + (Math.abs(this.getTimezoneOffset() / 60) < 10 ? '0' : '') + Math.abs(this.getTimezoneOffset() / 60) + '00';
		}, P: function P() {
			return (-this.getTimezoneOffset() < 0 ? '-' : '+') + (Math.abs(this.getTimezoneOffset() / 60) < 10 ? '0' : '') + Math.abs(this.getTimezoneOffset() / 60) + ':' + (Math.abs(this.getTimezoneOffset() % 60) < 10 ? '0' : '') + Math.abs(this.getTimezoneOffset() % 60);
		}, T: function T() {
			var m = this.getMonth();this.setMonth(0);var result = this.toTimeString().replace(/^.+ \(?([^\)]+)\)?$/, '$1');this.setMonth(m);return result;
		}, Z: function Z() {
			return -this.getTimezoneOffset() * 60;
		}, c: function c() {
			return this.format("Y-m-d") + "T" + this.format("H:i:sP");
		}, r: function r() {
			return this.toString();
		}, U: function U() {
			return this.getTime() / 1000;
		} };
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__)); // end define()

/***/ }),

/***/ "./common/static/js/vendor/timepicker/jquery.timepicker.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_FACTORY__, __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; };

/************************
jquery-timepicker
http://jonthornton.github.com/jquery-timepicker/

requires jQuery 1.7+
************************/

(function (factory) {
	if (true) {
		// AMD. Register as an anonymous module.
		!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(0)], __WEBPACK_AMD_DEFINE_FACTORY__ = (factory),
				__WEBPACK_AMD_DEFINE_RESULT__ = (typeof __WEBPACK_AMD_DEFINE_FACTORY__ === 'function' ?
				(__WEBPACK_AMD_DEFINE_FACTORY__.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__)) : __WEBPACK_AMD_DEFINE_FACTORY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));
	} else {
		// Browser globals
		factory(jQuery);
	}
})(function ($) {
	var _baseDate = _generateBaseDate();
	var _ONE_DAY = 86400;
	var _closeEvent = 'ontouchstart' in document ? 'touchstart' : 'mousedown';
	var _defaults = {
		className: null,
		minTime: null,
		maxTime: null,
		durationTime: null,
		step: 30,
		showDuration: false,
		timeFormat: 'g:ia',
		scrollDefaultNow: false,
		scrollDefaultTime: false,
		selectOnBlur: false,
		forceRoundTime: false,
		appendTo: 'body'
	};
	var _lang = {
		decimal: '.',
		mins: 'mins',
		hr: 'hr',
		hrs: 'hrs'
	};
	var globalInit = false;

	var methods = {
		init: function init(options) {
			return this.each(function () {
				var self = $(this);

				// convert dropdowns to text input
				if (self[0].tagName == 'SELECT') {
					var input = $('<input />');
					var attrs = { 'type': 'text', 'value': self.val() };
					var raw_attrs = self[0].attributes;

					for (var i = 0; i < raw_attrs.length; i++) {
						attrs[raw_attrs[i].nodeName] = raw_attrs[i].nodeValue;
					}

					input.attr(attrs);
					self.replaceWith(input);
					self = input;
				}

				var settings = $.extend({}, _defaults);

				if (options) {
					settings = $.extend(settings, options);
				}

				if (settings.minTime) {
					settings.minTime = _time2int(settings.minTime);
				}

				if (settings.maxTime) {
					settings.maxTime = _time2int(settings.maxTime);
				}

				if (settings.durationTime) {
					settings.durationTime = _time2int(settings.durationTime);
				}

				if (settings.lang) {
					_lang = $.extend(_lang, settings.lang);
				}

				self.data('timepicker-settings', settings);
				self.attr('autocomplete', 'off');
				self.on('click.timepicker focus.timepicker', methods.show);
				self.on('blur.timepicker', _formatValue);
				self.on('keydown.timepicker', _keyhandler);
				self.addClass('ui-timepicker-input');

				_formatValue.call(self.get(0));

				if (!globalInit) {
					// close the dropdown when container loses focus
					$('body').on(_closeEvent, function (e) {
						var target = $(e.target);
						var input = target.closest('.ui-timepicker-input');
						if (input.length === 0 && target.closest('.ui-timepicker-list').length === 0) {
							methods.hide();
						}
					});
					globalInit = true;
				}
			});
		},

		show: function show(e) {
			var self = $(this);

			if ('ontouchstart' in document) {
				// block the keyboard on mobile devices
				self.blur();
			}

			var list = self.data('timepicker-list');

			// check if input is readonly
			if (self.attr('readonly')) {
				return;
			}

			// check if list needs to be rendered
			if (!list || list.length === 0) {
				_render(self);
				list = self.data('timepicker-list');
			}

			// check if a flag was set to close this picker
			if (self.hasClass('ui-timepicker-hideme')) {
				self.removeClass('ui-timepicker-hideme');
				list.hide();
				return;
			}

			if (list.is(':visible')) {
				return;
			}

			// make sure other pickers are hidden
			methods.hide();

			if (self.offset().top + self.outerHeight(true) + list.outerHeight() > $(window).height() + $(window).scrollTop()) {
				// position the dropdown on top
				list.css({ 'left': self.offset().left, 'top': self.offset().top - list.outerHeight() });
			} else {
				// put it under the input
				list.css({ 'left': self.offset().left, 'top': self.offset().top + self.outerHeight() });
			}

			list.show();

			var settings = self.data('timepicker-settings');
			// position scrolling
			var selected = list.find('.ui-timepicker-selected');

			if (!selected.length) {
				if (self.val()) {
					selected = _findRow(self, list, _time2int(self.val()));
				} else if (settings.scrollDefaultNow) {
					selected = _findRow(self, list, _time2int(new Date()));
				} else if (settings.scrollDefaultTime !== false) {
					selected = _findRow(self, list, _time2int(settings.scrollDefaultTime));
				}
			}

			if (selected && selected.length) {
				var topOffset = list.scrollTop() + selected.position().top - selected.outerHeight();
				list.scrollTop(topOffset);
			} else {
				list.scrollTop(0);
			}

			self.trigger('showTimepicker');
		},

		hide: function hide(e) {
			$('.ui-timepicker-list:visible').each(function () {
				var list = $(this);
				var self = list.data('timepicker-input');
				var settings = self.data('timepicker-settings');

				if (settings && settings.selectOnBlur) {
					_selectValue(self);
				}

				list.hide();
				self.trigger('hideTimepicker');
			});
		},

		option: function option(key, value) {
			var self = $(this);
			var settings = self.data('timepicker-settings');
			var list = self.data('timepicker-list');

			if ((typeof key === 'undefined' ? 'undefined' : _typeof(key)) == 'object') {
				settings = $.extend(settings, key);
			} else if (typeof key == 'string' && typeof value != 'undefined') {
				settings[key] = value;
			} else if (typeof key == 'string') {
				return settings[key];
			}

			if (settings.minTime) {
				settings.minTime = _time2int(settings.minTime);
			}

			if (settings.maxTime) {
				settings.maxTime = _time2int(settings.maxTime);
			}

			if (settings.durationTime) {
				settings.durationTime = _time2int(settings.durationTime);
			}

			self.data('timepicker-settings', settings);

			if (list) {
				list.remove();
				self.data('timepicker-list', false);
			}
		},

		getSecondsFromMidnight: function getSecondsFromMidnight() {
			return _time2int($(this).val());
		},

		getTime: function getTime() {
			return new Date(_baseDate.valueOf() + _time2int($(this).val()) * 1000);
		},

		setTime: function setTime(value) {
			var self = $(this);
			var prettyTime = _int2time(_time2int(value), self.data('timepicker-settings').timeFormat);
			self.val(prettyTime);
		},

		remove: function remove() {
			var self = $(this);

			// check if this element is a timepicker
			if (!self.hasClass('ui-timepicker-input')) {
				return;
			}

			self.removeAttr('autocomplete', 'off');
			self.removeClass('ui-timepicker-input');
			self.removeData('timepicker-settings');
			self.off('.timepicker');

			// timepicker-list won't be present unless the user has interacted with this timepicker
			if (self.data('timepicker-list')) {
				self.data('timepicker-list').remove();
			}

			self.removeData('timepicker-list');
		}
	};

	// private methods

	function _render(self) {
		var settings = self.data('timepicker-settings');
		var list = self.data('timepicker-list');

		if (list && list.length) {
			list.remove();
			self.data('timepicker-list', false);
		}

		list = $('<ul />');
		list.attr('tabindex', -1);
		list.addClass('ui-timepicker-list');
		if (settings.className) {
			list.addClass(settings.className);
		}

		list.css({ 'display': 'none', 'position': 'absolute' });

		if ((settings.minTime !== null || settings.durationTime !== null) && settings.showDuration) {
			list.addClass('ui-timepicker-with-duration');
		}

		var durStart = settings.durationTime !== null ? settings.durationTime : settings.minTime;
		var start = settings.minTime !== null ? settings.minTime : 0;
		var end = settings.maxTime !== null ? settings.maxTime : start + _ONE_DAY - 1;

		if (end <= start) {
			// make sure the end time is greater than start time, otherwise there will be no list to show
			end += _ONE_DAY;
		}
		for (var i = start; i <= end; i += settings.step * 60) {
			var timeInt = i;
			var row = $('<li />');
			row.data('time', timeInt);
			row.text(_int2time(timeInt, settings.timeFormat));

			if ((settings.minTime !== null || settings.durationTime !== null) && settings.showDuration) {
				var duration = $('<span />');
				duration.addClass('ui-timepicker-duration');
				duration.text(' (' + _int2duration(i - durStart) + ')');
				row.append(duration);
			}

			list.append(row);
		}

		list.data('timepicker-input', self);
		self.data('timepicker-list', list);

		var appendTo = settings.appendTo;
		if (typeof appendTo === 'string') {
			appendTo = $(appendTo);
		} else if (typeof appendTo === 'function') {
			appendTo = appendTo(self);
		}
		appendTo.append(list);
		_setSelected(self, list);

		list.on('click', 'li', function (e) {
			self.addClass('ui-timepicker-hideme');
			self[0].focus();

			// make sure only the clicked row is selected
			list.find('li').removeClass('ui-timepicker-selected');
			$(this).addClass('ui-timepicker-selected');

			_selectValue(self);
			list.hide();
		});
	}

	function _generateBaseDate() {
		var _baseDate = new Date();
		var _currentTimezoneOffset = _baseDate.getTimezoneOffset() * 60000;
		_baseDate.setHours(0);_baseDate.setMinutes(0);_baseDate.setSeconds(0);
		var _baseDateTimezoneOffset = _baseDate.getTimezoneOffset() * 60000;

		return new Date(_baseDate.valueOf() - _baseDateTimezoneOffset + _currentTimezoneOffset);
	}

	function _findRow(self, list, value) {
		if (!value && value !== 0) {
			return false;
		}

		var settings = self.data('timepicker-settings');
		var out = false;
		var halfStep = settings.step * 30;

		// loop through the menu items
		list.find('li').each(function (i, obj) {
			var jObj = $(obj);

			var offset = jObj.data('time') - value;

			// check if the value is less than half a step from each row
			if (Math.abs(offset) < halfStep || offset == halfStep) {
				out = jObj;
				return false;
			}
		});

		return out;
	}

	function _setSelected(self, list) {
		var timeValue = _time2int(self.val());

		var selected = _findRow(self, list, timeValue);
		if (selected) selected.addClass('ui-timepicker-selected');
	}

	function _formatValue() {
		if (this.value === '') {
			return;
		}

		var self = $(this);
		var seconds = _time2int(this.value);

		if (seconds === null) {
			self.trigger('timeFormatError');
			return;
		}

		var settings = self.data('timepicker-settings');

		if (settings.forceRoundTime) {
			var offset = seconds % (settings.step * 60); // step is in minutes

			if (offset >= settings.step * 30) {
				// if offset is larger than a half step, round up
				seconds += settings.step * 60 - offset;
			} else {
				// round down
				seconds -= offset;
			}
		}

		var prettyTime = _int2time(seconds, settings.timeFormat);
		self.val(prettyTime);
	}

	function _keyhandler(e) {
		var self = $(this);
		var list = self.data('timepicker-list');

		if (!list.is(':visible')) {
			if (e.keyCode == 40) {
				self.focus();
			} else {
				return true;
			}
		}

		switch (e.keyCode) {

			case 13:
				// return
				_selectValue(self);
				methods.hide.apply(this);
				e.preventDefault();
				return false;

			case 38:
				// up
				var selected = list.find('.ui-timepicker-selected');

				if (!selected.length) {
					list.children().each(function (i, obj) {
						if ($(obj).position().top > 0) {
							selected = $(obj);
							return false;
						}
					});
					selected.addClass('ui-timepicker-selected');
				} else if (!selected.is(':first-child')) {
					selected.removeClass('ui-timepicker-selected');
					selected.prev().addClass('ui-timepicker-selected');

					if (selected.prev().position().top < selected.outerHeight()) {
						list.scrollTop(list.scrollTop() - selected.outerHeight());
					}
				}

				break;

			case 40:
				// down
				selected = list.find('.ui-timepicker-selected');

				if (selected.length === 0) {
					list.children().each(function (i, obj) {
						if ($(obj).position().top > 0) {
							selected = $(obj);
							return false;
						}
					});

					selected.addClass('ui-timepicker-selected');
				} else if (!selected.is(':last-child')) {
					selected.removeClass('ui-timepicker-selected');
					selected.next().addClass('ui-timepicker-selected');

					if (selected.next().position().top + 2 * selected.outerHeight() > list.outerHeight()) {
						list.scrollTop(list.scrollTop() + selected.outerHeight());
					}
				}

				break;

			case 27:
				// escape
				list.find('li').removeClass('ui-timepicker-selected');
				list.hide();
				break;

			case 9:
				//tab
				methods.hide();
				break;

			case 16:
			case 17:
			case 18:
			case 19:
			case 20:
			case 33:
			case 34:
			case 35:
			case 36:
			case 37:
			case 39:
			case 45:
				return;

			default:
				list.find('li').removeClass('ui-timepicker-selected');
				return;
		}
	}

	function _selectValue(self) {
		var settings = self.data('timepicker-settings');
		var list = self.data('timepicker-list');
		var timeValue = null;

		var cursor = list.find('.ui-timepicker-selected');

		if (cursor.length) {
			// selected value found
			timeValue = cursor.data('time');
		} else if (self.val()) {

			// no selected value; fall back on input value
			timeValue = _time2int(self.val());

			_setSelected(self, list);
		}

		if (timeValue !== null) {
			var timeString = _int2time(timeValue, settings.timeFormat);
			self.attr('value', timeString);
		}

		self.trigger('change').trigger('changeTime');
	}

	function _int2duration(seconds) {
		var minutes = Math.round(seconds / 60);
		var duration;

		if (Math.abs(minutes) < 60) {
			duration = [minutes, _lang.mins];
		} else if (minutes == 60) {
			duration = ['1', _lang.hr];
		} else {
			var hours = (minutes / 60).toFixed(1);
			if (_lang.decimal != '.') hours = hours.replace('.', _lang.decimal);
			duration = [hours, _lang.hrs];
		}

		return duration.join(' ');
	}

	function _int2time(seconds, format) {
		if (seconds === null) {
			return;
		}

		var time = new Date(_baseDate.valueOf() + seconds * 1000);
		var output = '';
		var hour, code;

		for (var i = 0; i < format.length; i++) {

			code = format.charAt(i);
			switch (code) {

				case 'a':
					output += time.getHours() > 11 ? 'pm' : 'am';
					break;

				case 'A':
					output += time.getHours() > 11 ? 'PM' : 'AM';
					break;

				case 'g':
					hour = time.getHours() % 12;
					output += hour === 0 ? '12' : hour;
					break;

				case 'G':
					output += time.getHours();
					break;

				case 'h':
					hour = time.getHours() % 12;

					if (hour !== 0 && hour < 10) {
						hour = '0' + hour;
					}

					output += hour === 0 ? '12' : hour;
					break;

				case 'H':
					hour = time.getHours();
					if (seconds >= _ONE_DAY) hour = Math.floor(seconds / (60 * 60));
					output += hour > 9 ? hour : '0' + hour;
					break;

				case 'i':
					var minutes = time.getMinutes();
					output += minutes > 9 ? minutes : '0' + minutes;
					break;

				case 's':
					seconds = time.getSeconds();
					output += seconds > 9 ? seconds : '0' + seconds;
					break;

				default:
					output += code;
			}
		}

		return output;
	}

	function _time2int(timeString) {
		if (timeString === '') return null;
		if (timeString + 0 == timeString) return timeString;

		if ((typeof timeString === 'undefined' ? 'undefined' : _typeof(timeString)) == 'object') {
			timeString = timeString.getHours() + ':' + timeString.getMinutes() + ':' + timeString.getSeconds();
		}

		var d = new Date(0);
		var time = timeString.toLowerCase().match(/(\d{1,2})(?::(\d{1,2}))?(?::(\d{2}))?\s*([pa]?)/);

		if (!time) {
			return null;
		}

		var hour = parseInt(time[1] * 1, 10);
		var hours;

		if (time[4]) {
			if (hour == 12) {
				hours = time[4] == 'p' ? 12 : 0;
			} else {
				hours = hour + (time[4] == 'p' ? 12 : 0);
			}
		} else {
			hours = hour;
		}

		var minutes = time[2] * 1 || 0;
		var seconds = time[3] * 1 || 0;
		return hours * 3600 + minutes * 60 + seconds;
	}

	// Plugin entry
	$.fn.timepicker = function (method) {
		if (methods[method]) {
			return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
		} else if ((typeof method === 'undefined' ? 'undefined' : _typeof(method)) === "object" || !method) {
			return methods.init.apply(this, arguments);
		} else {
			$.error("Method " + method + " does not exist on jQuery.timepicker");
		}
	};
});

/***/ }),

/***/ "./node_modules/backbone-associations/backbone-associations-min.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;(function(q,f){if(true)!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(1),__webpack_require__(2)], __WEBPACK_AMD_DEFINE_RESULT__ = function(g,i){return f(q,i,g)}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));else if("undefined"!==typeof exports){var g=require("underscore"),i=require("backbone");f(q,i,g);"undefined"!==typeof module&&module.exports&&(module.exports=i);exports=i}else f(q,q.Backbone,q._)})(this,function(q,f,g){var i,p,t,w,n,v,D,E,k,z,F,s={};i=f.Model;p=f.Collection;t=i.prototype;n=p.prototype;w=f.Events;f.Associations={VERSION:"0.6.2"};f.Associations.scopes=[];var G=function(){return k},
A=function(a){if(!g.isString(a)||1>g.size(a))a=".";k=a;D=RegExp("[\\"+k+"\\[\\]]+","g");E=RegExp("[^\\"+k+"\\[\\]]+","g")};try{Object.defineProperty(f.Associations,"SEPARATOR",{enumerable:!0,get:G,set:A})}catch(J){}f.Associations.Many=f.Many="Many";f.Associations.One=f.One="One";f.Associations.Self=f.Self="Self";f.Associations.SEPARATOR=".";f.Associations.getSeparator=G;f.Associations.setSeparator=A;f.Associations.EVENTS_BUBBLE=!0;f.Associations.EVENTS_WILDCARD=!0;f.Associations.EVENTS_NC=!1;A();
v=f.AssociatedModel=f.Associations.AssociatedModel=i.extend({relations:void 0,_proxyCalls:void 0,constructor:function(a,c){c&&c.__parents__&&(this.parents=[c.__parents__]);i.apply(this,arguments)},on:function(a,c,d){var b=w.on.apply(this,arguments);if(f.Associations.EVENTS_NC)return b;var l=/\s+/;g.isString(a)&&a&&!l.test(a)&&c&&(l=B(a))&&(s[l]="undefined"===typeof s[l]?1:s[l]+1);return b},off:function(a,c,d){if(f.Associations.EVENTS_NC)return w.off.apply(this,arguments);var b=/\s+/,l=this._events,
e={},h=l?g.keys(l):[],m=!a&&!c&&!d,i=g.isString(a)&&!b.test(a);if(m||i)for(var b=0,j=h.length;b<j;b++)e[h[b]]=l[h[b]]?l[h[b]].length:0;var p=w.off.apply(this,arguments);if(m||i){b=0;for(j=h.length;b<j;b++)(m=B(h[b]))&&(s[m]=l[h[b]]?s[m]-(e[h[b]]-l[h[b]].length):s[m]-e[h[b]])}return p},get:function(a){var c=this.__attributes__,d=t.get.call(this,a),c=c?x(d)?d:c[a]:d;return x(c)?c:this._getAttr.apply(this,arguments)},set:function(a,c,d){var b;g.isObject(a)||null==a?(b=a,d=c):(b={},b[a]=c);a=this._set(b,
d);this._processPendingEvents();return a},_set:function(a,c){var d,b,l,e,h=this;if(!a)return this;this.__attributes__=a;for(d in a)if(b||(b={}),d.match(D)){var f=H(d);e=g.initial(f);f=f[f.length-1];e=this.get(e);e instanceof i&&(e=b[e.cid]||(b[e.cid]={model:e,data:{}}),e.data[f]=a[d])}else e=b[this.cid]||(b[this.cid]={model:this,data:{}}),e.data[d]=a[d];if(b)for(l in b)e=b[l],this._setAttr.call(e.model,e.data,c)||(h=!1);else h=this._setAttr.call(this,a,c);delete this.__attributes__;return h},_setAttr:function(a,
c){var d;c||(c={});if(c.unset)for(d in a)a[d]=void 0;this.parents=this.parents||[];this.relations&&g.each(this.relations,function(b){var d=b.key,e=b.scope||q,h=this._transformRelatedModel(b,a),m=this._transformCollectionType(b,h,a),u=g.isString(b.map)?C(b.map,e):b.map,j=this.attributes[d],k=j&&j.idAttribute,o,r,n=!1;o=b.options?g.extend({},b.options,c):c;if(a[d]){e=g.result(a,d);e=u?u.call(this,e,m?m:h):e;if(x(e))if(b.type===f.Many)j?(j._deferEvents=!0,j[o.reset?"reset":"set"](e instanceof p?e.models:
e,o),h=j):(n=!0,e instanceof p?h=e:(h=this._createCollection(m||p,b.collectionOptions||(h?{model:h}:{})),h[o.reset?"reset":"set"](e,o)));else if(b.type===f.One)b=e instanceof i?e.attributes.hasOwnProperty(k):e.hasOwnProperty(k),m=e instanceof i?e.attributes[k]:e[k],j&&b&&j.attributes[k]===m?(j._deferEvents=!0,j._set(e instanceof i?e.attributes:e,o),h=j):(n=!0,e instanceof i?h=e:(o.__parents__=this,h=new h(e,o),delete o.__parents__));else throw Error("type attribute must be specified and have the values Backbone.One or Backbone.Many");
else h=e;r=a[d]=h;if(n||r&&!r._proxyCallback)r._proxyCallback||(r._proxyCallback=function(){return f.Associations.EVENTS_BUBBLE&&this._bubbleEvent.call(this,d,r,arguments)}),r.on("all",r._proxyCallback,this)}a.hasOwnProperty(d)&&this._setupParents(a[d],this.attributes[d])},this);return t.set.call(this,a,c)},_bubbleEvent:function(a,c,d){var b=d[0].split(":"),g=b[0],e="nested-change"==d[0],h="change"===g,m=d[1],u=-1,j=c._proxyCalls,b=b[1],n=!b||-1==b.indexOf(k),o;if(!e&&(n&&(F=B(d[0])||a),f.Associations.EVENTS_NC||
s[F])){if(f.Associations.EVENTS_WILDCARD&&/\[\*\]/g.test(b))return this;if(c instanceof p&&(h||b))u=c.indexOf(z||m);this instanceof i&&(z=this);b=a+(-1!==u&&(h||b)?"["+u+"]":"")+(b?k+b:"");f.Associations.EVENTS_WILDCARD&&(o=b.replace(/\[\d+\]/g,"[*]"));e=[];e.push.apply(e,d);e[0]=g+":"+b;f.Associations.EVENTS_WILDCARD&&b!==o&&(e[0]=e[0]+" "+g+":"+o);j=c._proxyCalls=j||{};if(this._isEventAvailable.call(this,j,b))return this;j[b]=!0;h&&(this._previousAttributes[a]=c._previousAttributes,this.changed[a]=
c);this.trigger.apply(this,e);f.Associations.EVENTS_NC&&(h&&this.get(b)!=d[2])&&(a=["nested-change",b,d[1]],d[2]&&a.push(d[2]),this.trigger.apply(this,a));j&&b&&delete j[b];z=void 0;return this}},_isEventAvailable:function(a,c){return g.find(a,function(a,b){return-1!==c.indexOf(b,c.length-b.length)})},_setupParents:function(a,c){a&&(a.parents=a.parents||[],-1==g.indexOf(a.parents,this)&&a.parents.push(this));c&&(0<c.parents.length&&c!=a)&&(c.parents=g.difference(c.parents,[this]),c._proxyCallback&&
c.off("all",c._proxyCallback,this))},_createCollection:function(a,c){var c=g.defaults(c,{model:a.model}),d=new a([],g.isFunction(c)?c.call(this):c);d.parents=[this];return d},_processPendingEvents:function(){this._processedEvents||(this._processedEvents=!0,this._deferEvents=!1,g.each(this._pendingEvents,function(a){a.c.trigger.apply(a.c,a.a)}),this._pendingEvents=[],g.each(this.relations,function(a){(a=this.attributes[a.key])&&a._processPendingEvents&&a._processPendingEvents()},this),delete this._processedEvents)},
_transformRelatedModel:function(a,c){var d=a.relatedModel,b=a.scope||q;d&&!(d.prototype instanceof i)&&(d=g.isFunction(d)?d.call(this,a,c):d);d&&g.isString(d)&&(d=d===f.Self?this.constructor:C(d,b));if(a.type===f.One){if(!d)throw Error("specify a relatedModel for Backbone.One type");if(!(d.prototype instanceof f.Model))throw Error("specify an AssociatedModel or Backbone.Model for Backbone.One type");}return d},_transformCollectionType:function(a,c,d){var b=a.collectionType,l=a.scope||q;if(b&&g.isFunction(b)&&
b.prototype instanceof i)throw Error("type is of Backbone.Model. Specify derivatives of Backbone.Collection");b&&!(b.prototype instanceof p)&&(b=g.isFunction(b)?b.call(this,a,d):b);b&&g.isString(b)&&(b=C(b,l));if(b&&!b.prototype instanceof p)throw Error("collectionType must inherit from Backbone.Collection");if(a.type===f.Many&&!c&&!b)throw Error("specify either a relatedModel or collectionType");return b},trigger:function(a){this._deferEvents?(this._pendingEvents=this._pendingEvents||[],this._pendingEvents.push({c:this,
a:arguments})):t.trigger.apply(this,arguments)},toJSON:function(a){var c={},d;c[this.idAttribute]=this.id;this.visited||(this.visited=!0,c=t.toJSON.apply(this,arguments),a&&a.serialize_keys&&(c=g.pick(c,a.serialize_keys)),this.relations&&g.each(this.relations,function(b){var f=b.key,e=b.remoteKey,h=this.attributes[f],i=!b.isTransient,b=b.serialize||[],k=g.clone(a);delete c[f];i&&(b.length&&(k?k.serialize_keys=b:k={serialize_keys:b}),d=h&&h.toJSON?h.toJSON(k):h,c[e||f]=g.isArray(d)?g.compact(d):d)},
this),delete this.visited);return c},clone:function(a){return new this.constructor(this.toJSON(a))},cleanup:function(a){a=a||{};g.each(this.relations,function(a){if(a=this.attributes[a.key])a._proxyCallback&&a.off("all",a._proxyCallback,this),a.parents=g.difference(a.parents,[this])},this);!a.listen&&this.off()},destroy:function(a){var a=a?g.clone(a):{},a=g.defaults(a,{remove_references:!0,listen:!0}),c=this;if(a.remove_references&&a.wait){var d=a.success;a.success=function(b){d&&d(c,b,a);c.cleanup(a)}}var b=
t.destroy.apply(this,[a]);a.remove_references&&!a.wait&&c.cleanup(a);return b},_getAttr:function(a){var c=this,d=this.__attributes__,a=H(a),b,f;if(!(1>g.size(a))){for(f=0;f<a.length;f++){b=a[f];if(!c)break;c=c instanceof p?isNaN(b)?void 0:c.at(b):d?x(c.attributes[b])?c.attributes[b]:d[b]:c.attributes[b]}return c}}});var H=function(a){return""===a?[""]:g.isString(a)?a.match(E):a||[]},B=function(a){if(!a)return a;a=a.split(":");return 1<a.length?(a=a[a.length-1],a=a.split(k),1<a.length?a[a.length-1].split("[")[0]:
a[0].split("[")[0]):""},C=function(a,c){var d,b=[c];b.push.apply(b,f.Associations.scopes);for(var i,e=0,h=b.length;e<h;++e)if(i=b[e])if(d=g.reduce(a.split(k),function(a,b){return a[b]},i))break;return d},I=function(a,c,d){var b,f;g.find(a,function(a){if(b=g.find(a.relations,function(b){return a.get(b.key)===c},this))return f=a,!0},this);return b&&b.map?b.map.call(f,d,c):d},x=function(a){return!g.isUndefined(a)&&!g.isNull(a)},y={};g.each(["set","remove","reset"],function(a){y[a]=p.prototype[a];n[a]=
function(c,d){this.model.prototype instanceof v&&this.parents&&(arguments[0]=I(this.parents,this,c));return y[a].apply(this,arguments)}});y.trigger=n.trigger;n.trigger=function(a){this._deferEvents?(this._pendingEvents=this._pendingEvents||[],this._pendingEvents.push({c:this,a:arguments})):y.trigger.apply(this,arguments)};n._processPendingEvents=v.prototype._processPendingEvents;n.on=v.prototype.on;n.off=v.prototype.off;return f});


/***/ }),

/***/ "./node_modules/edx-ui-toolkit/src/js/dropdown-menu/dropdown-menu-view.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";
var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;/**
 * A Backbone view that renders a fully accessible dropdown menu.
 *
 * Initialize the view by passing in the following attributes:
 *
 *~~~ javascript
 * view = new DropdownMenuView({
 *     className: 'space separated string of classes for element',
 *     model: new Backbone.Model({
 *         main: {
 *             image: 'http://placehold.it/40x40',
 *             screenreader_label: 'Dashboard for: ',
 *             text: 'username',
 *             url: 'dashboard'
 *         },
 *         button: {
 *             icon: 'icon-angle-down',
 *             label: 'User options dropdown'
 *         },
 *         items: [
 *             {
 *                 text: 'Account',
 *                 url: 'account_settings'
 *             }, {
 *                 text: 'Sign Out',
 *                 url: 'logout'
 *             }
 *         ]
 *     }),
 *     parent: 'selector for parent element that will be replaced with dropdown menu',
 *     ...
 * });
 *~~~
 * @module DropdownMenuView
 */



!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(2), __webpack_require__(0), __webpack_require__(1), __webpack_require__("./node_modules/edx-ui-toolkit/src/js/utils/constants.js"), __webpack_require__("./node_modules/edx-ui-toolkit/src/js/dropdown-menu/dropdown.underscore")], __WEBPACK_AMD_DEFINE_RESULT__ = function (Backbone, $, _, constants, DropdownTpl) {
    var DropdownMenuView = Backbone.View.extend({
        tpl: _.template(DropdownTpl),

        events: {
            'click .js-dropdown-button': 'clickOpenDropdown',
            'click a': 'analyticsLinkClick',
            keydown: 'viewKeypress'
        },

        dropdownButton: '.js-dropdown-button',

        menu: '.dropdown-menu',

        initialize: function initialize(options) {
            if (options.parent) {
                this.$parent = $(options.parent);
            }

            this.menuId = options.menuId || 'dropdown-menu-' + this.cid;
            this.keyBack = [constants.keyCodes.up, constants.keyCodes.left];
            this.keyForward = [constants.keyCodes.down, constants.keyCodes.right];
            this.keyClose = [constants.keyCodes.esc, constants.keyCodes.space];
        },

        className: function className() {
            return this.options.className;
        },

        render: function render() {
            /**
             * Set in the render function to prevent error when
             * view is used with a pre-rendered DOM
             */
            this.model.set({ menuId: this.menuId });

            this.$el.html(this.tpl(this.model.toJSON()));
            this.$parent.replaceWith(this.$el);
            this.postRender();

            return this;
        },

        postRender: function postRender() {
            this.$menu = this.$('.dropdown-menu');
            this.$page = $(document);
            this.$dropdownButton = this.$(this.dropdownButton);
            this.$lastItem = this.$menu.find('li:last-child a');
        },

        /**
         * Function to track analytics.
         *
         * By default it doesn't do anything, to utilize please
         * extend the View and implement a method such as the
         * following:
         *
         *~~~ javascript
         * var $link = $(event.target),
         *     label = $link.hasClass('menu-title') ? 'Dashboard' : $link.html().trim();
         *
         * window.analytics.track('user_dropdown.clicked', {
         *     category: 'navigation',
         *     label: label,
         *     link: $link.attr('href')
         * });
         *~~~
         *
         * @param {object} event The event to be tracked.
         * @returns {*} The event.
         */
        analyticsLinkClick: function analyticsLinkClick(event) {
            return event;
        },

        clickCloseDropdown: function clickCloseDropdown(event, context) {
            var $el = $(event.target) || $(document),
                $btn;

            // When using edX Pattern Library icons the target
            // is sometimes not the button.
            if (!$el.hasClass(this.dropdownButton)) {
                // If there is a parent dropdown button that is the element to test
                $btn = $el.closest(this.dropdownButton);
                if ($btn.length > 0) {
                    $el = $btn;
                }
            }

            if (!$el.hasClass('button-more') && !$el.hasClass('has-dropdown')) {
                context.closeDropdownMenu();
            }
        },

        clickOpenDropdown: function clickOpenDropdown(event) {
            event.preventDefault();
            this.openMenu(this.$dropdownButton);
        },

        closeDropdownMenu: function closeDropdownMenu() {
            var $open = this.$(this.menu);

            $open.removeClass('is-visible').addClass('is-hidden');

            this.$dropdownButton.removeClass('is-active').attr('aria-expanded', 'false');
        },

        focusFirstItem: function focusFirstItem() {
            this.$menu.find('.dropdown-item:first-child .action').focus();
        },

        focusLastItem: function focusLastItem() {
            this.$lastItem.focus();
        },

        handlerIsAction: function handlerIsAction(key, $el) {
            if (_.contains(this.keyForward, key)) {
                this.nextMenuItemLink($el);
            } else if (_.contains(this.keyBack, key)) {
                this.previousMenuItemLink($el);
            }
        },

        handlerIsButton: function handlerIsButton(key, event) {
            if (_.contains(this.keyForward, key)) {
                this.focusFirstItem();
                // if up arrow or left arrow key pressed or shift+tab
            } else if (_.contains(this.keyBack, key) || key === constants.keyCodes.tab && event.shiftKey) {
                event.preventDefault();
                this.focusLastItem();
            }
        },

        handlerIsMenu: function handlerIsMenu(key) {
            if (_.contains(this.keyForward, key)) {
                this.focusFirstItem();
            } else if (_.contains(this.keyBack, key)) {
                this.$dropdownButton.focus();
            }
        },

        handlerPageClicks: function handlerPageClicks(context) {
            // Only want 1 event listener for click.dropdown
            // on the page so unbind for instantiating
            this.$page.off('click.dropdown');
            this.$page.on('click.dropdown', function (event) {
                context.clickCloseDropdown(event, context);
            });
        },

        nextMenuItemLink: function nextMenuItemLink($el) {
            var items = this.$('.dropdown-menu').children('.dropdown-item').find('.action'),
                itemsCount = items.length - 1,
                index = items.index($el),
                next = index + 1;

            if (index === itemsCount) {
                this.$dropdownButton.focus();
            } else {
                items.eq(next).focus();
            }
        },

        openMenu: function openMenu($btn) {
            var $menu = this.$menu;
            if ($menu.hasClass('is-visible')) {
                this.closeDropdownMenu();
            } else {
                $btn.addClass('is-active').attr('aria-expanded', 'true');

                $menu.removeClass('is-hidden').addClass('is-visible');

                $menu.focus();
                this.setOrientation();
                this.handlerPageClicks(this);
            }
        },

        previousMenuItemLink: function previousMenuItemLink($el) {
            var items = this.$('.dropdown-menu').children('.dropdown-item').find('.action'),
                index = items.index($el),
                prev = index - 1;

            if (index === 0) {
                this.$dropdownButton.focus();
            } else {
                items.eq(prev).focus();
            }
        },

        setOrientation: function setOrientation() {
            var midpoint = $(window).width() / 2,
                alignClass = this.$dropdownButton.offset().left > midpoint ? 'align-right' : 'align-left';

            this.$menu.removeClass('align-left align-right').addClass(alignClass);
        },

        viewKeypress: function viewKeypress(event) {
            var key = event.keyCode,
                $el = $(event.target);

            if (_.contains(this.keyForward, key) || _.contains(this.keyBack, key)) {
                // Prevent default behavior if one of our trigger keys
                event.preventDefault();
            }

            if (key === constants.keyCodes.tab && !event.shiftKey && _.first($el) === _.first(this.$lastItem)) {
                event.preventDefault();
                this.$dropdownButton.focus();
            } else if (_.contains(this.keyClose, key)) {
                this.closeDropdownMenu();
                this.$dropdownButton.focus();
            } else if ($el.hasClass('action')) {
                // Key handlers for when a menu item has focus
                this.handlerIsAction(key, $el);
            } else if ($el.hasClass('dropdown-menu')) {
                // Key handlers for when the menu itself has focus, before an item within it receives focus
                this.handlerIsMenu(key);
            } else if ($el.hasClass('has-dropdown')) {
                // Key handlers for when the button that opens the menu has focus
                this.handlerIsButton(key, event);
            }
        }
    });

    return DropdownMenuView;
}.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));

/***/ }),

/***/ "./node_modules/edx-ui-toolkit/src/js/dropdown-menu/dropdown.underscore":
/***/ (function(module, exports) {

module.exports = "<a href=\"<%- main.url %>\" class=\"menu-title\">\n    <% if (main.screenreader_label) { %>\n        <span class=\"sr-only\"><%- main.screenreader_label %> </span>\n    <% } %>\n    <% if (main.image) { %>\n        <img class=\"menu-image\" src=\"<%- main.image %>\" alt=\"\">\n    <% } %>\n    <%- main.text %>\n</a>\n<button type=\"button\" class=\"menu-button button-more has-dropdown js-dropdown-button <% if (!button.icon) { %>default-icon<% } %>\" aria-haspopup=\"true\" aria-expanded=\"false\" aria-controls=\"<%- menuId %>\">\n    <% if (button.icon) { %>\n        <span class=\"icon <%- button.icon %>\" aria-hidden=\"true\"></span>\n    <% } %>\n    <span class=\"sr-only\"><%- button.label %></span>\n</button>\n<ul class=\"dropdown-menu list-divided is-hidden\" id=\"<%- menuId %>\" tabindex=\"-1\">\n    <% _.each(items, function(item, index) { %>\n        <li class=\"dropdown-item item has-block-link\">\n            <a href=\"<%- item.url %>\" class=\"action\"><%- item.text %></a>\n        </li>\n    <% }); %>\n</ul>\n"

/***/ }),

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

},["./cms/static/js/factories/textbooks.js"])));
//# sourceMappingURL=textbooks.js.map
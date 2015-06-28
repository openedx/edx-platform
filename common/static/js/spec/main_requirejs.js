(function(requirejs, define) {
    requirejs.config({
        paths: {
            'gettext': 'js/test/i18n',
            'jquery': 'js/vendor/jquery.min',
            'jquery.ui': 'js/vendor/jquery-ui.min',
            'jquery.flot': 'js/vendor/flot/jquery.flot.min',
            'jquery.form': 'js/vendor/jquery.form',
            'jquery.markitup': 'js/vendor/markitup/jquery.markitup',
            'jquery.leanModal': 'js/vendor/jquery.leanModal.min',
            'jquery.ajaxQueue': 'js/vendor/jquery.ajaxQueue',
            'jquery.smoothScroll': 'js/vendor/jquery.smooth-scroll.min',
            'jquery.scrollTo': 'js/vendor/jquery.scrollTo-1.4.2-min',
            'jquery.timepicker': 'js/vendor/timepicker/jquery.timepicker',
            'jquery.cookie': 'js/vendor/jquery.cookie',
            'jquery.qtip': 'js/vendor/jquery.qtip.min',
            'jquery.fileupload': 'js/vendor/jQuery-File-Upload/js/jquery.fileupload',
            'jquery.iframe-transport': 'js/vendor/jQuery-File-Upload/js/jquery.iframe-transport',
            'jquery.inputnumber': 'js/vendor/html5-input-polyfills/number-polyfill',
            'jquery.immediateDescendents': 'coffee/src/jquery.immediateDescendents',
            'jquery.simulate': 'js/vendor/jquery.simulate',
            'jquery.url': 'js/vendor/url.min',
            'sinon': 'js/vendor/sinon-1.7.1',
            'text': 'js/vendor/requirejs/text',
            'underscore': 'js/vendor/underscore-min',
            'underscore.string': 'js/vendor/underscore.string.min',
            'backbone': 'js/vendor/backbone-min',
            'backbone.associations': 'js/vendor/backbone-associations-min',
            'backbone.paginator': 'js/vendor/backbone.paginator.min',
            "backbone-super": "js/vendor/backbone-super",
            'jasmine-jquery': 'js/vendor/jasmine-jquery',
            'jasmine-imagediff': 'js/vendor/jasmine-imagediff',
            'jasmine-stealth': 'js/vendor/jasmine-stealth',
            'jasmine.async': 'js/vendor/jasmine.async',
            'URI': 'js/vendor/URI.min'
        },
        shim: {
            'gettext': {
                exports: 'gettext'
            },
            'jquery.ui': {
                deps: ['jquery'],
                exports: 'jQuery.ui'
            },
            'jquery.flot': {
                deps: ['jquery'],
                exports: 'jQuery.flot'
            },
            'jquery.form': {
                deps: ['jquery'],
                exports: 'jQuery.fn.ajaxForm'
            },
            'jquery.markitup': {
                deps: ['jquery'],
                exports: 'jQuery.fn.markitup'
            },
            'jquery.leanModal': {
                deps: ['jquery'],
                exports: 'jQuery.fn.leanModal'
            },
            'jquery.smoothScroll': {
                deps: ['jquery'],
                exports: 'jQuery.fn.smoothScroll'
            },
            'jquery.ajaxQueue': {
                deps: ['jquery'],
                exports: 'jQuery.fn.ajaxQueue'
            },
            'jquery.scrollTo': {
                deps: ['jquery'],
                exports: 'jQuery.fn.scrollTo'
            },
            'jquery.cookie': {
                deps: ['jquery'],
                exports: 'jQuery.fn.cookie'
            },
            'jquery.qtip': {
                deps: ['jquery'],
                exports: 'jQuery.fn.qtip'
            },
            'jquery.fileupload': {
                deps: ['jquery.iframe-transport'],
                exports: 'jQuery.fn.fileupload'
            },
            'jquery.inputnumber': {
                deps: ['jquery'],
                exports: 'jQuery.fn.inputNumber'
            },
            'jquery.simulate': {
                deps: ['jquery'],
                exports: 'jQuery.fn.simulate'
            },
            'jquery.url': {
                deps: ['jquery'],
                exports: 'jQuery.fn.url'
            },
            'datepair': {
                deps: ['jquery.ui', 'jquery.timepicker']
            },
            'underscore': {
                deps: ['underscore.string'],
                exports: '_',
                init: function(UnderscoreString) {
                    /* Mix non-conflicting functions from underscore.string
                     * (all but include, contains, and reverse) into the
                     * Underscore namespace. This allows the login, register,
                     * and password reset templates to render independent of the
                     * access view.
                     */
                    _.mixin(UnderscoreString.exports());

                    /* Since the access view is not using RequireJS, we also
                     * expose underscore.string at _.str, so that the access
                     * view can perform the mixin on its own.
                     */
                    _.str = UnderscoreString;
                }
            },
            'backbone': {
                deps: ['underscore', 'jquery'],
                exports: 'Backbone'
            },
            'backbone.associations': {
                deps: ['backbone'],
                exports: 'Backbone.Associations'
            },
            'backbone.paginator': {
                deps: ['backbone'],
                exports: 'Backbone.Paginator'
            },
            "backbone-super": {
                deps: ["backbone"]
            },
            'URI': {
                exports: 'URI'
            },
            'jasmine-jquery': {
                deps: ['jasmine']
            },
            'jasmine-imagediff': {
                deps: ['jasmine']
            },
            'jasmine-stealth': {
                deps: ['jasmine']
            },
            'jasmine.async': {
                deps: ['jasmine'],
                exports: 'AsyncSpec'
            },
            "sinon": {
                exports: "sinon"
            }
        }
    });

    define([
        // Run the common tests that use RequireJS.
        'common-requirejs/include/common/js/spec/components/list_spec.js',
        'common-requirejs/include/common/js/spec/components/paging_collection_spec.js',
        'common-requirejs/include/common/js/spec/components/paging_header_spec.js',
        'common-requirejs/include/common/js/spec/components/paging_footer_spec.js'
    ]);

}).call(this, requirejs, define);

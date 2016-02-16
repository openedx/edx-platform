(function(requirejs, define) {
    requirejs.config({
        baseUrl: '/base/',
        paths: {
            'gettext': 'js/test/i18n',
            'jquery': 'js/vendor/jquery.min',
            'jquery.ui': 'js/vendor/jquery-ui.min',
            'jquery.flot': 'js/vendor/flot/jquery.flot.min',
            'jquery.form': 'js/vendor/jquery.form',
            'jquery.markitup': 'js/vendor/markitup/jquery.markitup',
            'jquery.leanModal': 'js/vendor/jquery.leanModal',
            'jquery.ajaxQueue': 'js/vendor/jquery.ajaxQueue',
            'jquery.smoothScroll': 'js/vendor/jquery.smooth-scroll.min',
            'jquery.scrollTo': 'js/vendor/jquery.scrollTo.min',
            'jquery.timepicker': 'js/vendor/timepicker/jquery.timepicker',
            'jquery.cookie': 'js/vendor/jquery.cookie',
            'jquery.qtip': 'js/vendor/jquery.qtip.min',
            'jquery.fileupload': 'js/vendor/jQuery-File-Upload/js/jquery.fileupload',
            'jquery.iframe-transport': 'js/vendor/jQuery-File-Upload/js/jquery.iframe-transport',
            'jquery.inputnumber': 'js/vendor/html5-input-polyfills/number-polyfill',
            'jquery.immediateDescendents': 'coffee/src/jquery.immediateDescendents',
            'jquery.simulate': 'js/vendor/jquery.simulate',
            'jquery.url': 'js/vendor/url.min',
            'sinon': 'js/vendor/sinon-1.17.0',
            'text': 'js/vendor/requirejs/text',
            'underscore': 'common/js/vendor/underscore',
            'underscore.string': 'common/js/vendor/underscore.string',
            'backbone': 'common/js/vendor/backbone',
            'backbone.associations': 'js/vendor/backbone-associations-min',
            'backbone.paginator': 'js/vendor/backbone.paginator.min',
            'backbone-super': 'js/vendor/backbone-super',
            'jasmine-imagediff': 'js/vendor/jasmine-imagediff',
            'URI': 'js/vendor/URI.min',
            'modernizr': 'edx-pattern-library/js/modernizr-custom',
            'afontgarde': 'edx-pattern-library/js/afontgarde',
            'edxicons': 'edx-pattern-library/js/edx-icons',
            'draggabilly': 'js/vendor/draggabilly'
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
            'jasmine-imagediff': {},
            'common/js/spec_helpers/jasmine-extensions': {
                deps: ['jquery']
            },
            'common/js/spec_helpers/jasmine-stealth': {
                deps: ['underscore', 'underscore.string']
            },
            'common/js/spec_helpers/jasmine-waituntil': {
                deps: ['jquery']
            },
            "sinon": {
                exports: "sinon"
            },
            "modernizr": {
                exports: "Modernizr"
            },
            "afontgarde": {
                exports: "AFontGarde"
            }
        }
    });

    var testFiles = [
        'common/js/spec/components/tabbed_view_spec.js',
        'common/js/spec/components/feedback_spec.js',
        'common/js/spec/components/list_spec.js',
        'common/js/spec/components/paginated_view_spec.js',
        'common/js/spec/components/paging_collection_spec.js',
        'common/js/spec/components/paging_header_spec.js',
        'common/js/spec/components/paging_footer_spec.js',
        'common/js/spec/components/search_field_spec.js',
        'common/js/spec/components/view_utils_spec.js',
        'common/js/spec/utils/edx.utils.validate_spec.js'
    ];

    for (var i = 0; i < testFiles.length; i++) {
        testFiles[i] = '/base/' + testFiles[i];
    }

    var specHelpers = [
        'common/js/spec_helpers/jasmine-extensions',
        'common/js/spec_helpers/jasmine-stealth',
        'common/js/spec_helpers/jasmine-waituntil'
    ];

    // Jasmine has a global stack for creating a tree of specs. We need to load
    // spec files one by one, otherwise some end up getting nested under others.
    window.requireSerial(specHelpers.concat(testFiles), function () {
        // start test run, once Require.js is done
        window.__karma__.start();
    });

}).call(this, requirejs, define);

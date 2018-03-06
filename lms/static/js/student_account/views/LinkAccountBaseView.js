(function(define) {
    'use strict';
    define([
        'gettext',
        'jquery',
        'underscore',
        'backbone',
        'edx-ui-toolkit/js/utils/string-utils',
        'edx-ui-toolkit/js/utils/html-utils'
    ], function(gettext, $, _, Backbone, StringUtils, HtmlUtils) {
        return Backbone.View.extend({
            el: '',
            initialize: function(options) {
                this.options = _.extend({}, options);
                _.bindAll(this, 'redirect_to', 'showError');
            },
            redirect_to: function(url) {
                window.location.href = url;
            },
            showError: function(message) {
                var error = message;
                var errorMsg;
                if (!error.endsWith('.')) {
                    error += '.';
                }
                errorMsg = HtmlUtils.joinHtml(
                    gettext(message),
                    gettext(' Please contact '),
                    HtmlUtils.HTML('<a href="/faq" target="_blank">'),
                    gettext('support'),
                    HtmlUtils.HTML('</a>'),
                    gettext('.')
                );
                HtmlUtils.setHtml(this.$('.error-message'), errorMsg);
                this.$('.link-account-error-container')
                    .removeClass('is-hidden')
                    .focus();
            }
        });
    });
}).call(this, define || RequireJS.define);

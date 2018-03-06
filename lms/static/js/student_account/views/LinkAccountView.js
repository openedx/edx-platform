(function(define) {
    'use strict';
    define([
        'gettext',
        'jquery',
        'underscore',
        'backbone',
        'js/student_account/views/LinkAccountBaseView',
        'text!templates/fields/field_social_link_account.underscore',
        'text!templates/student_account/link_account.underscore',
        'edx-ui-toolkit/js/utils/string-utils',
        'edx-ui-toolkit/js/utils/html-utils'
    ], function(
        gettext, $, _, Backbone,
        LinkAccountBaseView,
        fieldSocialLinkTemplate,
        linkAccountTpl,
        StringUtils,
        HtmlUtils
    ) {
        return LinkAccountBaseView.extend({
            el: '#link-account-main',
            events: {
                'click .link-account-button': 'linkClicked'
            },
            initialize: function(options) {
                this.options = _.extend({}, options);
            },
            render: function() {
                var title = StringUtils.interpolate(
                    gettext('Sign in with {providerName}.'),
                    {providerName: this.options.providerName}
                );
                HtmlUtils.setHtml(this.$el, HtmlUtils.template(linkAccountTpl)({
                    userName: this.options.userName,
                    title: title,
                    message: ''
                }));
                if (this.options.duplicateProvider) {
                    this.showError(this.options.duplicateProvider);
                }
                return this;
            },
            linkClicked: function() {
                this.redirect_to(this.options.connectUrl);
            }
        });
    });
}).call(this, define || RequireJS.define);

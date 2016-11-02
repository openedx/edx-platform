/**
 * This Backbone view mimics the appearance of breadcrumbs, but does not provide true breadcrumb navigation.
 * This implementation is a stopgap developed due to limitations in the Discussions UI.
 * Don't use this breadcrumbs implementation as a model or reference.
 * Instead, check out the UXPL's breadcrumbs, which have been vetted for UX and A11Y.
 * http://ux.edx.org/components/breadcrumbs/
 */

(function(define) {
    'use strict';

    define([
        'backbone',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils',
        'text!discussion/templates/fake-breadcrumbs.underscore'
    ],
    function(Backbone, gettext, HtmlUtils, breadcrumbsTemplate) {
        var DiscussionFakeBreadcrumbs = Backbone.View.extend({
            initialize: function() {
                this.template = HtmlUtils.template(breadcrumbsTemplate);
                this.listenTo(this.model, 'change', this.render);
                this.render();
            },
            render: function() {
                var json = this.model.attributes;
                HtmlUtils.setHtml(this.$el, this.template(json));
                return this;
            }
        });

        return DiscussionFakeBreadcrumbs;
    });
}).call(this, define || RequireJS.define);

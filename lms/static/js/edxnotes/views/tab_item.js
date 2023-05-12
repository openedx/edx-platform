/* eslint-disable-next-line no-shadow-restricted-names, no-unused-vars */
(function(define, undefined) {
    'use strict';

    define(['gettext', 'underscore',
        'jquery', 'backbone', 'js/edxnotes/utils/template', 'edx-ui-toolkit/js/utils/html-utils'],
    function(gettext, _, $, Backbone, templateUtils, HtmlUtils) {
        // eslint-disable-next-line no-var
        var TabItemView = Backbone.View.extend({
            tagName: 'li',
            className: 'tab',
            activeClassName: 'is-active',

            events: {
                click: 'selectHandler',
                'click a': function(event) { event.preventDefault(); },
                'click .action-close': 'closeHandler'
            },

            // eslint-disable-next-line no-unused-vars
            initialize: function(options) {
                this.template = templateUtils.loadTemplate('tab-item');
                this.$el.attr('id', this.model.get('identifier'));
                this.listenTo(this.model, {
                    'change:is_active': function(model, value) {
                        this.$el.toggleClass(this.activeClassName, value);
                        if (value) {
                            this.$('.tab-label').prepend($('<span />', {
                                class: 'tab-aria-label sr',
                                text: gettext('Current tab')
                            }));
                        } else {
                            this.$('.tab-aria-label').remove();
                        }
                    },
                    destroy: this.remove
                });
            },

            render: function() {
                // eslint-disable-next-line no-var
                var html = this.template(this.model.toJSON());
                this.$el.html(HtmlUtils.HTML(html).toString());
                return this;
            },

            selectHandler: function(event) {
                event.preventDefault();
                if (!this.model.isActive()) {
                    this.model.activate();
                }
            },

            closeHandler: function(event) {
                event.preventDefault();
                event.stopPropagation();
                this.model.destroy();
            }
        });

        return TabItemView;
    });
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);

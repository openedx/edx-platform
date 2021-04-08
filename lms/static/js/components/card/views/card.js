/**
 * A generic card view class.
 *
 * Subclasses can override any of the following:
 * - configuration (string or function): Sets the display style of the card as square or list. Can take values of
 *      "square_card" or "list_card". Defaults to "square_card".
 * - action (function): Action to take when the action button is clicked. Defaults to a no-op.
 * - cardClass (string or function): Class name for this card's DOM element. Defaults to the empty string.
 * - pennant (string or function): Text of the card's pennant. No pennant is displayed if this value is falsy.
 * - title (string or function): Title of the card. Defaults to the empty string.
 * - description (string or function): Description of the card. Defaults to the empty string.
 * - details (array or function): Array of child views to be rendered as details of this card. The class "meta-detail"
 *      is automatically added to each rendered child view to ensure appropriate styling. Defaults to an empty list.
 * - actionClass (string or function): Class name for the action DOM element. Defaults to the empty string.
 * - actionUrl (string or function): URL to navigate to when the action button is clicked. Defaults to the empty string.
 * - actionContent: Content of the action button. This may include HTML. Default to the empty string.
 */
(function(define) {
    'use strict';
    define(['jquery',
        'underscore',
        'backbone',
        'text!templates/components/card/card.underscore',
        'edx-ui-toolkit/js/utils/html-utils'
    ],
        function($, _, Backbone, cardTemplate, HtmlUtils) {
            var CardView = Backbone.View.extend({
                tagName: 'li',

                events: {
                    'click .action': 'action'
                },

                /**
                 * constructor is needed in addition to initialize because of Backbone's initialization order.
                 * initialize seems to run last in the initialization process, after className. However, className
                 * depends on this.configuration being set to pick the appropriate class. Therefore, configuration
                 * is set in the constructor, but the rest of the initialization happens in initialize.
                 */
                constructor: function(options) {
                    if (!this.configuration) {
                        this.configuration = (options && options.configuration) ? options.configuration : 'square_card';
                    }
                    Backbone.View.prototype.constructor.apply(this, arguments);
                },

                initialize: function() {
                    this.render();
                },

                template: HtmlUtils.template(cardTemplate),

                switchOnConfiguration: function(square_result, list_result) {
                    return this.callIfFunction(this.configuration) === 'square_card' ?
                        square_result : list_result;
                },

                callIfFunction: function(value) {
                    if ($.isFunction(value)) {
                        return value.call(this);
                    } else {
                        return value;
                    }
                },

                className: function() {
                    var result = 'card ' +
                                 this.switchOnConfiguration('square-card', 'list-card') + ' ' +
                                 this.callIfFunction(this.cardClass);
                    if (this.callIfFunction(this.pennant)) {
                        result += ' has-pennant';
                    }
                    return result;
                },

                render: function() {
                    var maxLength = 72,
                        description = this.callIfFunction(this.description);
                    if (description.length > maxLength) {
                        description = description.substring(0, maxLength).trim() + '...';
                    }
                    HtmlUtils.setHtml(
                        this.$el,
                        this.template({
                            pennant: this.callIfFunction(this.pennant),
                            title: this.callIfFunction(this.title),
                            description: description,
                            action_class: this.callIfFunction(this.actionClass),
                            action_url: this.callIfFunction(this.actionUrl),
                            action_content: this.callIfFunction(this.actionContent),
                            configuration: this.callIfFunction(this.configuration),
                            srInfo: this.srInfo
                        })
                    );
                    var detailsEl = this.$el.find('.card-meta');
                    _.each(this.callIfFunction(this.details), function(detail) {
                        // Call setElement to rebind event handlers
                        detail.setElement(detail.el).render();
                        detail.$el.addClass('meta-detail');
                        detailsEl.append(detail.el);
                    });
                    return this;
                },

                action: function() { },
                cardClass: '',
                pennant: '',
                title: '',
                description: '',
                details: [],
                actionClass: '',
                actionUrl: '',
                actionContent: ''
            });

            return CardView;
        });
}).call(this, define || RequireJS.define);

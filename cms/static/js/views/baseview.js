define(["jquery", "underscore", "backbone", "gettext", "js/utils/handle_iframe_binding", "js/utils/templates",
    "js/views/feedback_notification", "js/views/feedback_prompt"],
    function ($, _, Backbone, gettext, IframeUtils, TemplateUtils, NotificationView, PromptView) {
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
                "click .ui-toggle-expansion": "toggleExpandCollapse"
            },

            //override the constructor function
            constructor: function(options) {
                _.bindAll(this, 'beforeRender', 'render', 'afterRender');
                var _this = this;
                this.render = _.wrap(this.render, function (render, options) {
                    _this.beforeRender();
                    render(options);
                    _this.afterRender();
                    return _this;
                });

                //call Backbone's own constructor
                Backbone.View.prototype.constructor.apply(this, arguments);
            },

            beforeRender: function() {
            },

            render: function() {
                return this;
            },

            afterRender: function() {
                IframeUtils.iframeBinding(this);
            },

            toggleExpandCollapse: function(event) {
                var target = $(event.target);
                // Don't propagate the event as it is possible that two views will both contain
                // this element, e.g. clicking on the element of a child view container in a parent.
                event.stopPropagation();
                event.preventDefault();
                target.closest('.expand-collapse').toggleClass('expand').toggleClass('collapse');
                target.closest('.is-collapsible, .window').toggleClass('collapsed');
                target.closest('.is-collapsible').children('article').slideToggle();
            },

            showLoadingIndicator: function() {
                $('.ui-loading').show();
            },

            hideLoadingIndicator: function() {
                $('.ui-loading').hide();
            },

            /**
             * Confirms with the user whether to run an operation or not, and then runs it if desired.
             */
            confirmThenRunOperation: function(title, message, actionLabel, operation) {
                var self = this;
                return new PromptView.Warning({
                    title: title,
                    message: message,
                    actions: {
                        primary: {
                            text: actionLabel,
                            click: function(prompt) {
                                prompt.hide();
                                operation();
                            }
                        },
                        secondary: {
                            text: gettext('Cancel'),
                            click: function(prompt) {
                                return prompt.hide();
                            }
                        }
                    }
                }).show();
            },

            /**
             * Shows a progress message for the duration of an asynchronous operation.
             * Note: this does not remove the notification upon failure because an error
             * will be shown that shouldn't be removed.
             * @param message The message to show.
             * @param operation A function that returns a promise representing the operation.
             */
            runOperationShowingMessage: function(message, operation) {
                var notificationView;
                notificationView = new NotificationView.Mini({
                    title: gettext(message)
                });
                notificationView.show();
                return operation().done(function() {
                    notificationView.hide();
                });
            },

            /**
             * Disables a given element when a given operation is running.
             * @param {jQuery} element: the element to be disabled.
             * @param operation: the operation during whose duration the
             * element should be disabled. The operation should return
             * a JQuery promise.
             */
            disableElementWhileRunning: function(element, operation) {
                element.addClass("is-disabled");
                return operation().always(function() {
                    element.removeClass("is-disabled");
                });
            },

            /**
             * Loads the named template from the page, or logs an error if it fails.
             * @param name The name of the template.
             * @returns The loaded template.
             */
            loadTemplate: function(name) {
                return TemplateUtils.loadTemplate(name);
            },

            /**
             * Returns the amount that the element is scrolled from the top of the view port.
             * @param element The element in question.
             */
            getScrollOffset: function(element) {
                var elementTop = element.offset().top;
                return elementTop - $(window).scrollTop();
            },

            /**
             * Scrolls the window so that the element is scrolled down to the specified
             * offset from the top of the view port.
             * @param element The element in question.
             * @param offset The amount by which the element should be scrolled from the top of the view port.
             */
            setScrollOffset: function(element, offset) {
                var elementTop = element.offset().top,
                    newScrollTop = elementTop - offset;
                this.setScrollTop(newScrollTop);
            },

            /**
             * Performs an animated scroll so that the window has the specified scroll top.
             * @param scrollTop The desired scroll top for the window.
             */
            setScrollTop: function(scrollTop) {
                $('html, body').animate({
                    scrollTop: scrollTop
                }, 500);
            }
        });

        return BaseView;
    });

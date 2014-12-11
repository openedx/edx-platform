/**
 * This is a base modal implementation that provides common utilities.
 *
 * A modal implementation should override the following methods:
 *
 *   getTitle():
 *     returns the title for the modal.
 *   getHTMLContent():
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
 *   addSaveButton: A boolean indicating whether to include a save
 *     button on the modal.
 */
define(["jquery", "underscore", "gettext", "js/views/baseview"],
    function($, _, gettext, BaseView) {
        var BaseModal = BaseView.extend({
            events : {
                'click .action-cancel': 'cancel'
            },

            options: $.extend({}, BaseView.prototype.options, {
                type: 'prompt',
                closeIcon: false,
                icon: false,
                modalName: 'basic',
                modalType: 'generic',
                modalSize: 'lg',
                title: '',
                // A list of class names, separated by space.
                viewSpecificClasses: ''
            }),

            initialize: function() {
                var parent = this.options.parent,
                    parentElement = this.options.parentElement;
                this.modalTemplate = this.loadTemplate('basic-modal');
                this.buttonTemplate = this.loadTemplate('modal-button');
                if (parent) {
                    parentElement = parent.$el;
                } else if (!parentElement) {
                    parentElement = this.$el.closest('.modal-window');
                    if (parentElement.length === 0) {
                        parentElement = $('body');
                    }
                }
                this.parentElement = parentElement;
            },

            render: function() {
                this.$el.html(this.modalTemplate({
                    name: this.options.modalName,
                    type: this.options.modalType,
                    size: this.options.modalSize,
                    title: this.getTitle(),
                    viewSpecificClasses: this.options.viewSpecificClasses
                }));
                this.addActionButtons();
                this.renderContents();
                this.parentElement.append(this.$el);
            },

            getTitle: function() {
                return this.options.title;
            },

            renderContents: function() {
                var contentHtml = this.getContentHtml();
                this.$('.modal-content').html(contentHtml);
            },

            /**
             * Returns the content to be shown in the modal.
             */
            getContentHtml: function() {
                return '';
            },

            show: function() {
                this.render();
                this.resize();
                $(window).resize(_.bind(this.resize, this));
            },

            hide: function() {
                // Completely remove the modal from the DOM
                this.undelegateEvents();
                this.$el.html('');
            },

            cancel: function(event) {
                if (event) {
                    event.preventDefault();
                    event.stopPropagation(); // Make sure parent modals don't see the click
                }
                this.hide();
            },

            /**
             * Adds the action buttons to the modal.
             */
            addActionButtons: function() {
                if (this.options.addSaveButton) {
                    this.addActionButton('save', gettext('Save'), true);
                }
                this.addActionButton('cancel', gettext('Cancel'));
            },

            /**
             * Adds a new action button to the modal.
             * @param type The type of the action.
             * @param name The action's name.
             * @param isPrimary True if this button is the primary one.
             */
            addActionButton: function(type, name, isPrimary) {
                var html = this.buttonTemplate({
                    type: type,
                    name: name,
                    isPrimary: isPrimary
                });
                this.getActionBar().find('ul').append(html);
            },

            /**
             * Returns the action bar that contains the modal's action buttons.
             */
            getActionBar: function() {
                return this.$('.modal-window > div > .modal-actions');
            },

            /**
             * Returns the action button of the specified type.
             */
            getActionButton: function(type) {
                return this.getActionBar().find('.action-' + type);
            },

            resize: function() {
                var top, left, modalWindow, modalWidth, modalHeight,
                    availableWidth, availableHeight, maxWidth, maxHeight;

                modalWindow = this.$('.modal-window');
                availableWidth = $(window).width();
                availableHeight = $(window).height();
                maxWidth = availableWidth * 0.80;
                maxHeight = availableHeight * 0.80;
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
    });

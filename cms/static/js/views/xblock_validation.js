define(['jquery', 'underscore', 'js/views/baseview', 'gettext'],
    function($, _, BaseView, gettext) {
        /**
         * View for xblock validation messages as displayed in Studio.
         */
        var XBlockValidationView = BaseView.extend({

            // Takes XBlockValidationModel as a model
            initialize: function(options) {
                BaseView.prototype.initialize.call(this);
                this.template = this.loadTemplate('xblock-validation-messages');
                this.root = options.root;
            },

            render: function() {
                this.$el.html(this.template({
                    validation: this.model,
                    additionalClasses: this.getAdditionalClasses(),
                    getIcon: this.getIcon.bind(this),
                    getDisplayName: this.getDisplayName.bind(this)
                }));
                return this;
            },

            /**
             * Returns the icon css class based on the message type.
             * @param messageType
             * @returns string representation of css class that will render the correct icon, or null if unknown type
             */
            getIcon: function(messageType) {
                if (messageType === this.model.ERROR) {
                    return 'fa-exclamation-circle';
                }
                else if (messageType === this.model.WARNING || messageType === this.model.NOT_CONFIGURED) {
                    return 'fa-exclamation-triangle';
                }
                return null;
            },

            /**
             * Returns a display name for a message (useful for screen readers), based on the message type.
             * @param messageType
             * @returns string display name (translated)
             */
            getDisplayName: function(messageType) {
                if (messageType === this.model.WARNING || messageType === this.model.NOT_CONFIGURED) {
                    // Translators: This message will be added to the front of messages of type warning,
                    // e.g. "Warning: this component has not been configured yet".
                    return gettext('Warning');
                }
                else if (messageType === this.model.ERROR) {
                    // Translators: This message will be added to the front of messages of type error,
                    // e.g. "Error: required field is missing".
                    return gettext('Error');
                }
                return null;
            },

            /**
             * Returns additional css classes that can be added to HTML containing the validation messages.
             * Useful for rendering NOT_CONFIGURED in a special way.
             *
             * @returns string of additional css classes (or empty string)
             */
            getAdditionalClasses: function() {
                if (this.root && this.model.get('summary').type === this.model.NOT_CONFIGURED &&
                    this.model.get('messages').length === 0) {
                    return 'no-container-content';
                }
                return '';
            }
        });

        return XBlockValidationView;
    });

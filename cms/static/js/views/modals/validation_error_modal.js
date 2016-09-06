define(['jquery', 'underscore', 'gettext', 'js/views/modals/base_modal'],
    function($, _, gettext, BaseModal) {
        var ValidationErrorModal = BaseModal.extend({
            events: {
                'click .action-cancel': 'cancel',
                'click .action-undo': 'resetAction'
            },

            initialize: function() {
                BaseModal.prototype.initialize.call(this);
                this.template = this.loadTemplate('validation-error-modal');
            },

            options: $.extend({}, BaseModal.prototype.options, {
                modalName: 'Validation Error Modal',
                title: gettext('Validation Error While Saving'),
                modalSize: 'md'
            }),

            addActionButtons: function() {
                this.addActionButton('undo', gettext('Undo Changes'), true);
                this.addActionButton('cancel', gettext('Change Manually'));
            },

            render: function() {
                BaseModal.prototype.render.call(this);
            },

            /* Set the JSON object of error_models that will be displayed
             * it must be an object, not json string. */
            setContent: function(json_object) {
                this.response = json_object;
            },

            /* Create the content HTML for this modal by passing necessary 
             * parameters to template (validation-error-modal) */
            getContentHtml: function() {

                return this.template({
                    response: this.response,
                    num_errors: this.response.length
                });
            },

            /* Receive calback function from the view, so that it can be 
             * invoked when the user clicks the reset button */
            setResetCallback: function(reset_callback) {
                this.reset_callback = reset_callback;
            },

            /* Upon receiving a user's clicking event on the reset button, 
             * resets all setting changes, and hide the modal */
            resetAction: function() {

                // reset page content
                this.reset_callback();

                // hide the modal
                BaseModal.prototype.hide.call(this); 
            }
        });

        return ValidationErrorModal;
    }
);

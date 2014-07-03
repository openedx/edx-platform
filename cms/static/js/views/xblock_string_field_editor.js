/**
 * XBlockStringFieldEditor is a view that allows the user to inline edit an XBlock string field.
 * Clicking on the field value will hide the text and replace it with an input to allow the user
 * to change the value. Once the user leaves the field, a request will be sent to update the
 * XBlock field's value if it has been changed. If the user presses Escape, then any changes will
 * be removed and the input hidden again.
 */
define(["jquery", "gettext", "js/views/baseview"],
    function ($, gettext, BaseView) {

        var XBlockStringFieldEditor = BaseView.extend({
            events: {
                'click .xblock-field-value': 'showInput',
                'change .xblock-field-input': 'updateField',
                'focusout .xblock-field-input': 'onInputFocusLost',
                'keyup .xblock-field-input': 'handleKeyUp'
            },

            // takes XBlockInfo as a model

            initialize: function() {
                BaseView.prototype.initialize.call(this);
                this.fieldName = this.$el.data('field');
                this.template = this.loadTemplate('xblock-string-field-editor');
                this.model.on('change:' + this.fieldName, this.onChangeField, this);
            },

            render: function() {
                this.$el.append(this.template({
                    value: this.model.get(this.fieldName),
                    fieldName: this.fieldName
                }));
                return this;
            },

            getLabel: function() {
                return this.$('.xblock-field-value');
            },

            getInput: function () {
                return this.$('.xblock-field-input');
            },

            onInputFocusLost: function() {
                var currentValue = this.model.get(this.fieldName);
                if (currentValue === this.getInput().val()) {
                    this.hideInput();
                }
            },

            onChangeField: function() {
                var value = this.model.get(this.fieldName);
                this.getLabel().text(value);
                this.getInput().val(value);
                this.hideInput();
            },

            showInput: function(event) {
                var input = this.getInput();
                event.preventDefault();
                this.getLabel().addClass('is-hidden');
                input.removeClass('is-hidden');
                input.focus();
            },

            hideInput: function() {
                this.getLabel().removeClass('is-hidden');
                this.getInput().addClass('is-hidden');
            },

            updateField: function() {
                var xblockInfo = this.model,
                    newValue = this.getInput().val(),
                    requestData = this.createUpdateRequestData(newValue),
                    fieldName = this.fieldName;
                this.runOperationShowingMessage(gettext('Saving&hellip;'),
                    function() {
                        return xblockInfo.save(requestData);
                    }).done(function() {
                        // Update publish and last modified information from the server.
                        xblockInfo.fetch();
                    });
            },

            createUpdateRequestData: function(newValue) {
                var metadata = {};
                metadata[this.fieldName] = newValue;
                return {
                    metadata: metadata
                };
            },

            handleKeyUp: function(event) {
                if (event.keyCode === 27) {   // Revert the changes if the user hits escape
                    this.getInput().val(this.model.get(this.fieldName));
                    this.hideInput();
                }
            }
        });

        return XBlockStringFieldEditor;
    }); // end define();

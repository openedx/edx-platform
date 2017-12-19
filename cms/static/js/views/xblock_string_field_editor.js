/**
 * XBlockStringFieldEditor is a view that allows the user to inline edit an XBlock string field.
 * Clicking on the field value will hide the text and replace it with an input to allow the user
 * to change the value. Once the user leaves the field, a request will be sent to update the
 * XBlock field's value if it has been changed. If the user presses Escape, then any changes will
 * be removed and the input hidden again.
 */
define(['js/views/baseview', 'js/views/utils/xblock_utils'],
    function(BaseView, XBlockViewUtils) {
        var XBlockStringFieldEditor = BaseView.extend({
            events: {
                'click .xblock-field-value-edit': 'showInput',
                'click button[name=submit]': 'onClickSubmit',
                'click button[name=cancel]': 'onClickCancel',
                'click .xblock-string-field-editor': 'onClickEditor',
                'change .xblock-field-input': 'updateField',
                'focusout .xblock-field-input': 'onInputFocusLost',
                'keyup .xblock-field-input': 'handleKeyUp'
            },

            // takes XBlockInfo as a model

            initialize: function() {
                BaseView.prototype.initialize.call(this);
                this.fieldName = this.$el.data('field');
                this.fieldDisplayName = this.$el.data('field-display-name');
                this.template = this.loadTemplate('xblock-string-field-editor');
                this.model.on('change:' + this.fieldName, this.onChangeField, this);
            },

            render: function() {
                this.$el.append(this.template({
                    value: this.model.escape(this.fieldName),
                    fieldName: this.fieldName,
                    fieldDisplayName: this.fieldDisplayName
                }));
                return this;
            },

            getLabel: function() {
                return this.$('.xblock-field-value');
            },

            getInput: function() {
                return this.$('.xblock-field-input');
            },

            onInputFocusLost: function() {
                var currentValue = this.model.get(this.fieldName);
                if (currentValue === this.getInput().val()) {
                    this.hideInput();
                }
            },

            onClickSubmit: function(event) {
                event.preventDefault();
                event.stopPropagation();
                this.updateField();
            },

            onClickCancel: function(event) {
                event.preventDefault();
                event.stopPropagation();
                this.cancelInput();
            },

            onClickEditor: function(event) {
                event.stopPropagation();
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
                event.stopPropagation();
                this.$el.addClass('is-editing');
                input.focus().select();
            },

            hideInput: function() {
                this.$el.removeClass('is-editing');
            },

            cancelInput: function() {
                this.getInput().val(this.model.get(this.fieldName));
                this.hideInput();
            },

            /**
             * Refresh the model from the server so that it gets the latest publish and last modified information.
             */
            refresh: function() {
                this.model.fetch();
            },

            updateField: function() {
                var self = this,
                    xblockInfo = this.model,
                    newValue = this.getInput().val().trim(),
                    oldValue = xblockInfo.get(this.fieldName);
                // TODO: generalize this as not all xblock fields want to disallow empty strings...
                if (newValue === '' || newValue === oldValue) {
                    this.cancelInput();
                    return;
                }
                return XBlockViewUtils.updateXBlockField(xblockInfo, this.fieldName, newValue).done(function() {
                    self.refresh();
                });
            },

            handleKeyUp: function(event) {
                if (event.keyCode === 27) {   // Revert the changes if the user hits escape
                    this.cancelInput();
                }
            }
        });

        return XBlockStringFieldEditor;
    }); // end define();

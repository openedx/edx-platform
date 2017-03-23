/**
 * XBlockStringFieldDescriptionEditor is a view which extends XBlockStringFieldEditor.
 */
define(["js/views/utils/xblock_utils", "js/views/xblock_string_field_editor"],
    function (XBlockViewUtils, XBlockStringFieldEditor) {
        return XBlockStringFieldEditor.extend({
            additionalEvents: {
                'click .xblock-field-description-value-edit': 'showInput',
                'click .xblock-description-field-editor': 'onClickEditor'
            },

            initialize: function() {
                XBlockStringFieldEditor.prototype.initialize.call(this);
                this.fieldName = this.$el.data('field-description');
                this.fieldDisplayName = this.$el.data('field-display-description');
                this.template = this.loadTemplate('xblock-description-field-editor');
            },

            onInputFocusLost: function() {
                var currentValue = this.model.get(this.fieldName);
                if (currentValue === this.getInput().val() || !(this.getInput().val())) {
                    this.hideInput();
                }
            },

            updateField: function() {
                var self = this,
                    xblockInfo = this.model,
                    newValue = this.getInput().val().trim(),
                    oldValue = xblockInfo.get(this.fieldName);
                if (newValue === oldValue) {
                    this.cancelInput();
                    return;
                }
                /**
                 *  We want to allow user to "delete" description.
                 */
                if (newValue === '') {
                    newValue = null;
                }
                return XBlockViewUtils.updateXBlockField(xblockInfo, this.fieldName, newValue).done(function() {
                    self.refresh();
                });
            }
        });
    }); // end define();

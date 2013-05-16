/**
 * Model used for metadata setting editors. This model does not do its own saving,
 * as that is done by module_edit.coffee.
 */
CMS.Models.Metadata = Backbone.Model.extend({

    defaults: {
        "field_name": null,
        "display_name": null,
        "value" : null,
        "explicitly_set": null,
        "default_value" : null,
        "options" : null,
        "type" : null
    },

    initialize: function() {
        this.original_value = this.get('value');
        this.original_explicitly_set = this.get('explicitly_set');
    },

    getOriginalValue: function() {
        return this.originalValue;
    },

    isModified : function() {
        if (!this.get('explicitly_set') && !this.original_explicitly_set) {
            return false;
        }
        if (this.get('explicitly_set') && this.original_explicitly_set) {
            return this.get('value') !== this.original_value;
        }
        return true;
    },

    isExplicitlySet: function() {
        return this.get('explicitly_set');
    },

    getDisplayValue : function () {
        return this.get('value');
    },

    getValue: function() {
        return this.get('explicitly_set') ? this.get('value') : null;
    },

    setValue: function (value) {
        this.set('explicitly_set', true);
        this.set('value', value);
    },

    getFieldName: function () {
        return this.get('field_name');
    },

    getOptions: function () {
        return this.get('options');
    },

    getType: function() {
        return this.get('type');
    },

    clear: function() {
        this.set('explicitly_set', false);
        this.set('value', this.get('default_value'));
    }
});

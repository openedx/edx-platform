CMS.Models.Metadata = Backbone.Model.extend({
    // This model class is not suited for restful operations and is considered just a server side initialized container
    url: '',

    defaults: {
        "display_name": null,
        "value" : null,
        "explicitly_set": null,
        "default_value" : null
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

    clear: function() {
        this.set('explicitly_set', false);
        this.set('value', this.get('default_value'));
    }
});

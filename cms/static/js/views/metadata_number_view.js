if (!CMS.Views['Metadata']) CMS.Views.Metadata = {};

CMS.Views.Metadata.Number = CMS.Views.Metadata.String.extend({

    getValue: function() {
        var stringVal = this.$el.find('#' + this.uniqueId).val();
        if (this.isInteger) {
            return parseInt(stringVal)
        }
        else {
            return parseFloat(stringVal)
        }
    }
});
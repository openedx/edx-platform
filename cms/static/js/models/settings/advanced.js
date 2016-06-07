define(["backbone"], function(Backbone) {

var Advanced = Backbone.Model.extend({

    defaults: {
        // There will be one property per course setting. Each property's value is an object with keys
        // 'display_name', 'help', 'value', and 'deprecated. The property keys are the setting names.
        // For instance: advanced_modules: {display_name: "Advanced Modules, help:"Beta modules...",
        //                                  value: ["word_cloud", "split_module"], deprecated: False}
        // Only 'value' is editable.
    },

    validate: function (attrs) {
        // Keys can no longer be edited. We are currently not validating values.
    }
});

return Advanced;
}); // end define()

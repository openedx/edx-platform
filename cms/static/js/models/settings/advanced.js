define(["backbone"], function(Backbone) {

var Advanced = Backbone.Model.extend({

    defaults: {
        // the properties are whatever the user types in (in addition to whatever comes originally from the server)
    },

    validate: function (attrs) {
        // Keys can no longer be edited. We are currently not validating values.
    },

    save : function (attrs, options) {
        // wraps the save call w/ the deletion of the removed keys after we know the saved ones worked
        options = options ? _.clone(options) : {};
        // add saveSuccess to the success
        var success = options.success;
        options.success = function(model, resp, options) {
          if (success) success(model, resp, options);
        };
        Backbone.Model.prototype.save.call(this, attrs, options);
    }
});

return Advanced;
}); // end define()

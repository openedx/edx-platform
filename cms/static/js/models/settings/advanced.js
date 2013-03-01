if (!CMS.Models['Settings']) CMS.Models.Settings = {};

CMS.Models.Settings.Advanced = Backbone.Model.extend({
    // the key for a newly added policy-- before the user has entered a key value
    new_key : "__new_advanced_key__",

    defaults: {
        // the properties are whatever the user types in (in addition to whatever comes originally from the server)
    },
    // which keys to send as the deleted keys on next save
    deleteKeys : [],
    blacklistKeys : [], // an array which the controller should populate directly for now [static not instance based]

    validate: function (attrs) {
        var errors = {};
        for (var key in attrs) {
            if (key === this.new_key || _.isEmpty(key)) {
                errors[key] = "A key must be entered.";
            }
            else if (_.contains(this.blacklistKeys, key)) {
                errors[key] = key + " is a reserved keyword or can be edited on another screen";
            }
        }
        if (!_.isEmpty(errors)) return errors;
    },
    
    save : function (attrs, options) {
        // wraps the save call w/ the deletion of the removed keys after we know the saved ones worked
        options = options ? _.clone(options) : {};
        // add saveSuccess to the success
        var success = options.success;
        options.success = function(model, resp, options) {
          model.afterSave(model);
          if (success) success(model, resp, options);
        };
        Backbone.Model.prototype.save.call(this, attrs, options);
    },
    
    afterSave : function(self) {
        // remove deleted attrs
        if (!_.isEmpty(self.deleteKeys)) {
            // remove the to be deleted keys from the returned model
            _.each(self.deleteKeys, function(key) { self.unset(key); });
            // not able to do via backbone since we're not destroying the model
            $.ajax({
                url : self.url,
                // json to and fro
                contentType : "application/json",
                dataType : "json",
                // delete
                type : 'DELETE',
                // data
                data : JSON.stringify({ deleteKeys : self.deleteKeys})
            })
            .fail(function(hdr, status, error) { CMS.ServerError(self, "Deleting keys:" + status); })
            .done(function(data, status, error) {
                // clear deleteKeys on success
                self.deleteKeys = [];
            });
        }
    }
});
